from dataclasses import dataclass

from observation_parser import parse_observation
from state import EngagementState, Observation


@dataclass(frozen=True)
class SessionStatus:
    target: str
    objective: str
    phase: str
    observations: tuple[Observation, ...]
    findings: tuple[str, ...]
    actions_completed: tuple[str, ...]
    evidence: tuple[str, ...]


class SentinelSession:
    def __init__(self) -> None:
        self.objective = ""
        self.engagement = EngagementState(target="")

    def set_target(self, target: str) -> None:
        normalised_target = target.strip()

        if not normalised_target:
            raise ValueError("Target must not be empty.")

        self.engagement.target = normalised_target

    def set_objective(self, objective: str) -> None:
        normalised_objective = objective.strip()

        if not normalised_objective:
            raise ValueError("Objective must not be empty.")

        self.objective = normalised_objective

    def set_phase(self, phase: str) -> None:
        normalised_phase = phase.strip()

        if not normalised_phase:
            raise ValueError("Phase must not be empty.")

        self.engagement.phase = normalised_phase

    def record_observation(self, raw_observation: str) -> Observation:
        observation = parse_observation(raw_observation)

        self.engagement.add_observation(observation)

        return observation

    def status(self) -> SessionStatus:
        return SessionStatus(
            target=self.engagement.target,
            objective=self.objective,
            phase=self.engagement.phase,
            observations=tuple(self.engagement.observations),
            findings=tuple(self.engagement.findings),
            actions_completed=tuple(
                self.engagement.actions_completed
            ),
            evidence=tuple(self.engagement.evidence),
        )