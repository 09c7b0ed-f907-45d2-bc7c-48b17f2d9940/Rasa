import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


def load_run_rasa_module():
    rasa_module = types.ModuleType("rasa")
    rasa_module.__version__ = "test"

    rasa_main_module = types.ModuleType("rasa.__main__")
    rasa_main_module.main = lambda: None

    rasa_core_module = types.ModuleType("rasa.core")
    rasa_core_run_module = types.ModuleType("rasa.core.run")
    rasa_core_run_module.configure_app = lambda *args, **kwargs: None

    sanic_module = types.ModuleType("sanic")
    sanic_response_module = types.ModuleType("sanic.response")
    sanic_response_module.json = lambda payload, status=200: {"payload": payload, "status": status}
    sanic_module.response = sanic_response_module

    sanic_routing_module = types.ModuleType("sanic_routing")
    sanic_routing_exceptions_module = types.ModuleType("sanic_routing.exceptions")

    class RouteExists(Exception):
        pass

    sanic_routing_exceptions_module.RouteExists = RouteExists

    module_map = {
        "rasa": rasa_module,
        "rasa.__main__": rasa_main_module,
        "rasa.core": rasa_core_module,
        "rasa.core.run": rasa_core_run_module,
        "sanic": sanic_module,
        "sanic.response": sanic_response_module,
        "sanic_routing": sanic_routing_module,
        "sanic_routing.exceptions": sanic_routing_exceptions_module,
    }

    module_path = Path(__file__).resolve().parents[1] / "src/run_rasa.py"
    spec = importlib.util.spec_from_file_location("run_rasa_under_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load run_rasa from {module_path}")

    with mock.patch.dict(sys.modules, module_map, clear=False):
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

    return module


run_rasa = load_run_rasa_module()


class RunRasaTests(unittest.TestCase):
    def test_read_env_trims_values_and_normalizes_empty_strings(self) -> None:
        with mock.patch.dict(sys.modules["os"].environ, {"RASA_TEST": "  value  "}, clear=False):
            self.assertEqual(run_rasa._read_env("RASA_TEST"), "value")

        with mock.patch.dict(sys.modules["os"].environ, {"RASA_TEST": "   "}, clear=False):
            self.assertIsNone(run_rasa._read_env("RASA_TEST"))

    def test_env_flag_parses_truthy_and_falsy_values(self) -> None:
        with mock.patch.dict(sys.modules["os"].environ, {"RASA_FLAG": "yes"}, clear=False):
            self.assertTrue(run_rasa._env_flag("RASA_FLAG", default=False))

        with mock.patch.dict(sys.modules["os"].environ, {"RASA_FLAG": "no"}, clear=False):
            self.assertFalse(run_rasa._env_flag("RASA_FLAG", default=True))

    def test_resolve_endpoints_file_uses_explicit_file_or_backend_preset(self) -> None:
        with mock.patch.dict(sys.modules["os"].environ, {"RASA_ENDPOINTS_FILE": "custom.yml"}, clear=False):
            self.assertEqual(run_rasa._resolve_endpoints_file(), "custom.yml")

        with mock.patch.dict(sys.modules["os"].environ, {"RASA_ENDPOINTS_FILE": "", "RASA_TRACKER_STORE_BACKEND": "memory"}, clear=False):
            self.assertEqual(run_rasa._resolve_endpoints_file(), "src/core/endpoints.memory.yml")

    def test_resolve_auth_token_requires_token_when_enabled(self) -> None:
        with mock.patch.dict(
            sys.modules["os"].environ,
            {"RASA_REQUIRE_AUTH_TOKEN": "true", "RASA_AUTH_TOKEN": ""},
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                run_rasa._resolve_auth_token()

        with mock.patch.dict(
            sys.modules["os"].environ,
            {"RASA_REQUIRE_AUTH_TOKEN": "false", "RASA_AUTH_TOKEN": ""},
            clear=False,
        ):
            self.assertEqual(run_rasa._resolve_auth_token(), "")

    def test_resolve_cors_accepts_only_bare_http_or_https_origins(self) -> None:
        with mock.patch.dict(sys.modules["os"].environ, {"RASA_CORS": "https://example.com"}, clear=False):
            self.assertEqual(run_rasa._resolve_cors(), "https://example.com")

        with mock.patch.dict(sys.modules["os"].environ, {"RASA_CORS": "https://example.com/path"}, clear=False):
            with self.assertRaises(RuntimeError):
                run_rasa._resolve_cors()

        with mock.patch.dict(sys.modules["os"].environ, {"RASA_CORS": "*"}, clear=False):
            with self.assertRaises(RuntimeError):
                run_rasa._resolve_cors()


class FakeRedisClient:
    def __init__(self) -> None:
        self.deleted_keys: list[str] = []
        self.delete_return = 1

    def delete(self, key: str) -> int:
        self.deleted_keys.append(key)
        return self.delete_return


class FakeRealStore:
    """Stands in for a raw, unwrapped RedisTrackerStore: exposes .red and
    .key_prefix directly, matching the real class's actual attributes."""

    def __init__(self, redis_client: "FakeRedisClient", key_prefix: str = "tracker:") -> None:
        self.red = redis_client
        self.key_prefix = key_prefix


class FakeWrapperStore:
    """Stands in for AwaitableTrackerStore/FailSafeTrackerStore: both hold
    the real store under the same private `_tracker_store` attribute, with
    no passthrough of the real store's own attributes."""

    def __init__(self, inner: object) -> None:
        self._tracker_store = inner


class HardDeleteTrackerTests(unittest.IsolatedAsyncioTestCase):
    async def test_unwraps_nested_wrappers_to_reach_real_store(self) -> None:
        # Reproduces the actual bug: agent.tracker_store is double-wrapped
        # (AwaitableTrackerStore around FailSafeTrackerStore around the real
        # RedisTrackerStore). Before unwrapping, .red/.key_prefix lookups on
        # the outer wrapper always found nothing and deletion silently
        # reported failure on every call.
        redis_client = FakeRedisClient()
        real_store = FakeRealStore(redis_client)
        wrapped_twice = FakeWrapperStore(FakeWrapperStore(real_store))

        result = await run_rasa._hard_delete_tracker(wrapped_twice, "user1:thread:1")

        self.assertTrue(result)
        self.assertEqual(redis_client.deleted_keys, ["tracker:user1:thread:1"])

    async def test_prefers_a_generic_delete_method_over_redis_fallback(self) -> None:
        redis_client = FakeRedisClient()

        class StoreWithDelete(FakeRealStore):
            def __init__(self) -> None:
                super().__init__(redis_client)
                self.delete_calls: list[str] = []

            async def delete(self, sender_id: str) -> bool:
                self.delete_calls.append(sender_id)
                return True

        store = StoreWithDelete()
        result = await run_rasa._hard_delete_tracker(store, "user1:thread:1")

        self.assertTrue(result)
        self.assertEqual(store.delete_calls, ["user1:thread:1"])
        self.assertEqual(redis_client.deleted_keys, [])  # fallback never attempted

    async def test_falls_back_to_redis_when_delete_method_returns_falsy(self) -> None:
        redis_client = FakeRedisClient()

        class StoreWithNoopDelete(FakeRealStore):
            def __init__(self) -> None:
                super().__init__(redis_client)

            def delete(self, sender_id: str) -> bool:
                return False  # e.g. a custom store reporting "nothing to delete"

        result = await run_rasa._hard_delete_tracker(StoreWithNoopDelete(), "user1:thread:1")

        self.assertTrue(result)
        self.assertEqual(redis_client.deleted_keys, ["tracker:user1:thread:1"])

    async def test_falls_back_to_redis_when_delete_method_raises(self) -> None:
        redis_client = FakeRedisClient()

        class StoreWithBrokenDelete(FakeRealStore):
            def __init__(self) -> None:
                super().__init__(redis_client)

            def delete(self, sender_id: str) -> bool:
                raise RuntimeError("boom")

        result = await run_rasa._hard_delete_tracker(StoreWithBrokenDelete(), "user1:thread:1")

        self.assertTrue(result)
        self.assertEqual(redis_client.deleted_keys, ["tracker:user1:thread:1"])

    async def test_returns_false_when_neither_delete_nor_redis_client_available(self) -> None:
        class BareStore:
            pass

        result = await run_rasa._hard_delete_tracker(BareStore(), "user1:thread:1")

        self.assertFalse(result)

    async def test_returns_false_when_redis_delete_raises(self) -> None:
        class ExplodingRedisClient:
            def delete(self, key: str) -> int:
                raise RuntimeError("connection lost")

        store = FakeRealStore(ExplodingRedisClient())
        result = await run_rasa._hard_delete_tracker(store, "user1:thread:1")

        self.assertFalse(result)

    async def test_returns_false_when_redis_reports_nothing_deleted(self) -> None:
        redis_client = FakeRedisClient()
        redis_client.delete_return = 0  # key didn't exist
        store = FakeRealStore(redis_client)

        result = await run_rasa._hard_delete_tracker(store, "user1:thread:1")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()