import unittest

from state import EngagementState, Observation


class StateTests(unittest.TestCase):
    def test_add_observation_records_observation(self):
        state = EngagementState(target="10.10.10.10")
        observation = Observation(
            description="HTTP service discovered",
            service="http",
            port=80,
            protocol="tcp",
        )

        state.add_observation(observation)

        self.assertIn(observation, state.observations)

    def test_observation_allows_description_without_service_metadata(self):
        observation = Observation(description="Login page discovered")

        self.assertEqual(observation.description, "Login page discovered")
        self.assertIsNone(observation.service)
        self.assertIsNone(observation.port)
        self.assertIsNone(observation.protocol)

    def test_record_action_records_completed_action(self):
        state = EngagementState(target="10.10.10.10")

        state.record_action("enumerate_http")

        self.assertIn("enumerate_http", state.actions_completed)


if __name__ == "__main__":
    unittest.main()