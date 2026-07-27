import unittest
from unittest.mock import patch

from src import thread_index_store


class _FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value


class ThreadIndexStoreTests(unittest.TestCase):
    def setUp(self):
        self.fake = _FakeRedis()
        patcher = patch.object(thread_index_store, "_get_client", return_value=self.fake)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_missing_returns_empty_dict(self):
        self.assertEqual(thread_index_store.get_index_payload("user-1"), {})

    def test_set_then_get_roundtrips(self):
        payload = {"1": {"id": 1, "name": "First"}}
        thread_index_store.set_index_payload("user-1", payload)
        self.assertEqual(thread_index_store.get_index_payload("user-1"), payload)

    def test_keys_are_scoped_per_user(self):
        thread_index_store.set_index_payload("user-1", {"1": {"id": 1}})
        thread_index_store.set_index_payload("user-2", {"2": {"id": 2}})
        self.assertEqual(thread_index_store.get_index_payload("user-1"), {"1": {"id": 1}})
        self.assertEqual(thread_index_store.get_index_payload("user-2"), {"2": {"id": 2}})

    def test_corrupted_json_returns_empty_dict(self):
        self.fake.set(thread_index_store._key_for("user-1"), "not json")
        self.assertEqual(thread_index_store.get_index_payload("user-1"), {})

    def test_non_dict_json_returns_empty_dict(self):
        self.fake.set(thread_index_store._key_for("user-1"), "[1, 2, 3]")
        self.assertEqual(thread_index_store.get_index_payload("user-1"), {})


if __name__ == "__main__":
    unittest.main()
