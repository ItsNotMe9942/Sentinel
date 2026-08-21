from capabilities import build_default_registry
from capability_registry import CapabilityRegistry
from planner import RuleBasedPlanner
from policy import PolicyDecision, PolicyEngine
from state import EngagementState


class SentinelRuntime:
    def __init__(self, registry: CapabilityRegistry | None = None) -> None:
        self.planner = RuleBasedPlanner()
        self.policy = PolicyEngine()
        self.registry = registry if registry is not None else build_default_registry()

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

        try:
            capability = self.registry.resolve(action.name)
        except KeyError:
            print(f"Capability unavailable: {action.name}")
            return

        capability.execute(state)
        state.record_action(action.name)
        print("Action recorded.")
