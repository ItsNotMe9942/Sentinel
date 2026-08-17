import unittest
from unittest.mock import patch

from runtime import SentinelRuntime
from state import EngagementState


class RuntimeTests(unittest.TestCase):
    @patch("builtins.input", return_value="y")
    def test_approved_action_is_recorded(self, mock_input):
        state = EngagementState(target="10.10.10.10")
        state.add_observation("80/tcp open http")

        runtime = SentinelRuntime()
        runtime.step(state)

        self.assertIn("enumerate_http", state.actions_completed)

    @patch("builtins.input", return_value="n")
    def test_declined_action_is_not_recorded(self, mock_input):
        state = EngagementState(target="10.10.10.10")
        state.add_observation("80/tcp open http")

        runtime = SentinelRuntime()
        runtime.step(state)

        self.assertNotIn("enumerate_http", state.actions_completed)

    @patch("builtins.input")
    def test_denied_action_does_not_prompt_or_record(self, mock_input):
        state = EngagementState(target="")
        state.add_observation("80/tcp open http")

        runtime = SentinelRuntime()
        runtime.step(state)

        mock_input.assert_not_called()
        self.assertNotIn("enumerate_http", state.actions_completed)


if __name__ == "__main__":
    unittest.main()
