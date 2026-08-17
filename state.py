from dataclasses import dataclass, field
from typing import List


@dataclass
class EngagementState:
    target: str
    phase: str = "enumeration"
    observations: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    actions_completed: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    def add_observation(self, observation: str) -> None:
        self.observations.append(observation)

    def record_action(self, action_name: str) -> None:
        self.actions_completed.append(action_name)
