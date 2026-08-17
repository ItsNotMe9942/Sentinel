from dataclasses import dataclass


@dataclass(frozen=True)
class ProposedAction:
    name: str
    reason: str
    offensive: bool = False
    requires_scope: bool = True
