import unittest

from planner import RuleBasedPlanner
from state import EngagementState


class PlannerTests(unittest.TestCase):
    def test_completed_http_enumeration_is_not_repeated(self):
        state = EngagementState(target="10.10.10.10")
        state.add_observation("80/tcp open http")
        state.record_action("enumerate_http")

        planner = RuleBasedPlanner()
        action = planner.next_action(state)

        self.assertNotEqual(action.name, "enumerate_http")

    def test_http_observation_proposes_enumeration(self):
        state = EngagementState(target="10.10.10.10")
        state.add_observation("80/tcp open http")

        planner = RuleBasedPlanner()
        action = planner.next_action(state)

        self.assertEqual(action.name, "enumerate_http")

    def test_non_http_observation_falls_back_to_review(self):
        state = EngagementState(target="10.10.10.10")
        state.add_observation("22/tcp open ssh")

        planner = RuleBasedPlanner()
        action = planner.next_action(state)

        self.assertEqual(action.name, "review_observations")


if __name__ == "__main__":
    unittest.main()
