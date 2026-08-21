import unittest
from unittest.mock import Mock, patch

from capability_registry import Capability, CapabilityRegistry
from runtime import SentinelRuntime
from state import EngagementState, Observation


class RuntimeTests(unittest.TestCase):
    @patch("builtins.input", return_value="y")
    def test_approved_action_is_recorded(self, mock_input):
        state = EngagementState(target="10.10.10.10")
        state.add_observation(
            Observation(
                description="80/tcp open http",
                service="http",
                port=80,
                protocol="tcp",
            )
        )

        runtime = SentinelRuntime()
        runtime.step(state)

        self.assertIn("enumerate_http", state.actions_completed)

    @patch("builtins.input", return_value="y")
    def test_approved_action_executes_registered_capability(self, mock_input):
        state = EngagementState(target="10.10.10.10")
        state.add_observation(
            Observation(
                description="80/tcp open http",
                service="http",
                port=80,
                protocol="tcp",
            )
        )
        handler = Mock()
        registry = CapabilityRegistry()
        registry.register(
            Capability(
                name="enumerate_http",
                description="Test HTTP enumeration capability.",
                handler=handler,
            )
        )

        runtime = SentinelRuntime(registry=registry)
        runtime.step(state)

        handler.assert_called_once_with(state)
        self.assertIn("enumerate_http", state.actions_completed)

    @patch("builtins.input", return_value="y")
    def test_unregistered_capability_is_not_executed_or_recorded(self, mock_input):
        state = EngagementState(target="10.10.10.10")
        state.add_observation(
            Observation(
                description="80/tcp open http",
                service="http",
                port=80,
                protocol="tcp",
            )
        )
        runtime = SentinelRuntime(registry=CapabilityRegistry())

        runtime.step(state)

        self.assertNotIn("enumerate_http", state.actions_completed)

    @patch("builtins.input", return_value="n")
    def test_declined_action_is_not_recorded(self, mock_input):
        state = EngagementState(target="10.10.10.10")
        state.add_observation(
            Observation(
                description="80/tcp open http",
                service="http",
                port=80,
                protocol="tcp",
            )
        )

        runtime = SentinelRuntime()
        runtime.step(state)

        self.assertNotIn("enumerate_http", state.actions_completed)

    @patch("builtins.input")
    def test_denied_action_does_not_prompt_or_record(self, mock_input):
        state = EngagementState(target="")
        state.add_observation(
            Observation(
                description="80/tcp open http",
                service="http",
                port=80,
                protocol="tcp",
            )
        )

        runtime = SentinelRuntime()
        runtime.step(state)

        mock_input.assert_not_called()
        self.assertNotIn("enumerate_http", state.actions_completed)


if __name__ == "__main__":
    unittest.main()