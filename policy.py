from dataclasses import dataclass
from enum import Enum

from actions import ProposedAction
from state import EngagementState


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


@dataclass(frozen=True)
class PolicyResult:
    decision: PolicyDecision
    reason: str


class PolicyEngine:
    def evaluate(self, action: ProposedAction, state: EngagementState) -> PolicyResult:
        if action.requires_scope and not state.target.strip():
            return PolicyResult(
                PolicyDecision.DENY,
                "Action requires an in-scope target.",
            )

        if action.offensive:
            return PolicyResult(
                PolicyDecision.REQUIRE_APPROVAL,
                "Offensive actions require explicit operator approval.",
            )

        return PolicyResult(
            PolicyDecision.REQUIRE_APPROVAL,
            "Phase 0.1 requires operator approval before simulated execution.",
        )
