from actions import ProposedAction
from state import EngagementState


class RuleBasedPlanner:
    def next_action(self, state: EngagementState) -> ProposedAction:
        http_observed = any(
            observation.service is not None
            and observation.service.lower() in {"http", "https"}
            for observation in state.observations
        )

        if http_observed and "enumerate_http" not in state.actions_completed:
            return ProposedAction(
                name="enumerate_http",
                reason="An HTTP service has been observed and has not yet been enumerated.",
            )

        if "enumerate_http" in state.actions_completed:
            return ProposedAction(
                name="review_observations",
                reason="HTTP enumeration has already been recorded; review current observations for the next step.",
                requires_scope=False,
            )

        return ProposedAction(
            name="review_observations",
            reason="There is not enough information to recommend a more specific action.",
            requires_scope=False,
        )
