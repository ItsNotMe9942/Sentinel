from dataclasses import dataclass, field


@dataclass
class EngagementState:
    target: str
    phase: str = "enumeration"
    observations: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    actions_completed: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def add_observation(self, observation: str) -> None:
        self.observations.append(observation)

    def record_action(self, action_name: str) -> None:
        self.actions_completed.append(action_name)
