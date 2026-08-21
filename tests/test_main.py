import unittest
from unittest.mock import patch

import main
from state import Observation


class TestMain(unittest.TestCase):
    @patch("main.SentinelRuntime.step")
    @patch("builtins.input", side_effect=["10.10.10.10", "80/tcp open http"])
    def test_main_passes_structured_observation_to_runtime(
        self,
        mock_input,
        mock_step,
    ):
        main.main()

        state = mock_step.call_args.args[0]

        self.assertEqual(state.target, "10.10.10.10")
        self.assertEqual(len(state.observations), 1)
        self.assertIsInstance(state.observations[0], Observation)
        self.assertEqual(state.observations[0].service, "http")
        self.assertEqual(state.observations[0].port, 80)
        self.assertEqual(state.observations[0].protocol, "tcp")


if __name__ == "__main__":
    unittest.main()