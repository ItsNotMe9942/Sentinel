import unittest
from actions import ProposedAction
from policy import PolicyDecision, PolicyEngine
from state import EngagementState


class PolicyTests(unittest.TestCase):
    def test_action_requires_target(self):
        state = EngagementState(target="")
        action = ProposedAction(
            name="enumerate_http",
            reason="Test",
            requires_scope=True,
        )

        result = PolicyEngine().evaluate(action, state)

        self.assertEqual(result.decision, PolicyDecision.DENY)

    def test_offensive_action_requires_approval(self):
        state = EngagementState(target="10.10.10.10")
        action = ProposedAction(
            name="verify_finding",
            reason="Test",
            offensive=True,
        )

        result = PolicyEngine().evaluate(action, state)

        self.assertEqual(
            result.decision,
            PolicyDecision.REQUIRE_APPROVAL,
        )


if __name__ == "__main__":
    unittest.main()
