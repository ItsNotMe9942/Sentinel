import unittest

from capabilities import build_default_registry
from capability_registry import Capability, CapabilityRegistry
from state import EngagementState


class CapabilityRegistryTests(unittest.TestCase):
    def test_registered_capability_can_be_resolved(self):
        registry = build_default_registry()

        capability = registry.resolve("enumerate_http")

        self.assertEqual(capability.name, "enumerate_http")

    def test_unregistered_capability_cannot_be_resolved(self):
        registry = CapabilityRegistry()

        with self.assertRaises(KeyError):
            registry.resolve("not_registered")

    def test_duplicate_capability_name_is_rejected(self):
        registry = CapabilityRegistry()
        capability = Capability(
            name="review_observations",
            description="Test capability.",
            handler=lambda state: None,
        )
        registry.register(capability)

        with self.assertRaises(ValueError):
            registry.register(capability)

    def test_capability_executes_registered_handler(self):
        state = EngagementState(target="10.10.10.10")
        executed_targets: list[str] = []
        capability = Capability(
            name="record_target",
            description="Record the target used by the capability.",
            handler=lambda current_state: executed_targets.append(current_state.target),
        )

        capability.execute(state)

        self.assertEqual(executed_targets, ["10.10.10.10"])


if __name__ == "__main__":
    unittest.main()