from planner import RuleBasedPlanner
from policy import PolicyDecision, PolicyEngine
from state import EngagementState


class SentinelRuntime:
    def __init__(self) -> None:
        self.planner = RuleBasedPlanner()
        self.policy = PolicyEngine()

    def step(self, state: EngagementState) -> None:
        action = self.planner.next_action(state)
        policy = self.policy.evaluate(action, state)

        print("\n--- Sentinel Decision ---")
        print(f"Target: {state.target}")
        print(f"Phase: {state.phase}")
        print(f"Action: {action.name}")
        print(f"Reason: {action.reason}")
        print(f"Policy: {policy.decision.value}")
        print(f"Policy reason: {policy.reason}")

        if policy.decision == PolicyDecision.DENY:
            print("Action blocked.")
            return

        approved = input("Approve this action? [y/N]: ").strip().lower() == "y"

        if not approved:
            print("Operator declined action.")
            return

        print(f"[SIMULATED] Executing: {action.name}")
        state.record_action(action.name)
        print("Action recorded.")
