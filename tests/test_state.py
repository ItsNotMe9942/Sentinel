import unittest

from state import EngagementState


class StateTests(unittest.TestCase):
    def test_add_observation_records_observation(self):
        state = EngagementState(target="10.10.10.10")

        state.add_observation("80/tcp open http")

        self.assertIn("80/tcp open http", state.observations)

    def test_record_action_records_completed_action(self):
        state = EngagementState(target="10.10.10.10")

        state.record_action("enumerate_http")

        self.assertIn("enumerate_http", state.actions_completed)


if __name__ == "__main__":
    unittest.main()
