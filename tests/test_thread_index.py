import unittest

from src.thread_index import (
    apply_index_action,
    build_thread_list_from_payload,
    next_thread_id_from_payload,
)


class ThreadIndexTests(unittest.TestCase):
    def test_build_thread_list_filters_deleted_entries(self):
        payload = {
            "1": {"id": 1, "name": "One", "action": "create", "created_at": "c1", "timestamp": "t1"},
            "2": {"id": 2, "name": "Two", "action": "delete", "created_at": "c2", "timestamp": "t2"},
        }
        threads = build_thread_list_from_payload(payload)
        self.assertIn(1, threads)
        self.assertNotIn(2, threads)

    def test_apply_index_action_and_next_id(self):
        payload = {}
        payload = apply_index_action(payload, 1, "create", "First")
        payload = apply_index_action(payload, 1, "rename", "Renamed")
        payload = apply_index_action(payload, 2, "create", "Second")

        self.assertEqual(payload["1"]["name"], "Renamed")
        self.assertEqual(next_thread_id_from_payload(payload), 3)


if __name__ == "__main__":
    unittest.main()
