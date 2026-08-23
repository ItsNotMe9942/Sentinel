import tempfile
import unittest
from pathlib import Path

from context_manager import ContextManager
from model_gateway import (
    ModelGateway,
    ModelRequest,
    ModelResponse,
)
from reasoning_service import ReasoningService
from sentinel_cli import SentinelCLI, build_cli
from session import SentinelSession
from state import Observation
from vault_adapter import VaultAdapter


class FakeProvider:
    def __init__(
        self,
        response_content: str = "Test response",
    ) -> None:
        self.response_content = response_content
        self.last_request: ModelRequest | None = None

    def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        self.last_request = request

        return ModelResponse(
            content=self.response_content
        )


class SentinelCLITests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)

        lab_path = self.vault_path / "Lab"
        lab_path.mkdir()

        self.architecture_path = (
            lab_path / "Architecture.md"
        )
        self.architecture_path.write_text(
            (
                "# Architecture\n\n"
                "The OptiPlex runs Proxmox."
            ),
            encoding="utf-8",
        )

        self.adapter = VaultAdapter(
            self.vault_path
        )

        self.session = SentinelSession()

        self.provider = FakeProvider(
            response_content=(
                "The OptiPlex is documented "
                "as the Proxmox host."
            )
        )

        self.context_manager = ContextManager(
            self.adapter
        )

        self.reasoning_service = ReasoningService(
            self.context_manager,
            ModelGateway(self.provider),
            session=self.session,
        )

        self.output: list[str] = []

        self.cli = SentinelCLI(
            session=self.session,
            vault_adapter=self.adapter,
            reasoning_service=self.reasoning_service,
            output_fn=self.output.append,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_help_lists_available_commands(self):
        self.cli.handle_input("/help")

        output = "\n".join(self.output)

        self.assertIn("/target", output)
        self.assertIn("/objective", output)
        self.assertIn("/observe", output)
        self.assertIn("/search", output)
        self.assertIn("/ask", output)

    def test_target_command_updates_session(self):
        self.cli.handle_input(
            "/target 10.10.10.10"
        )

        self.assertEqual(
            self.session.status().target,
            "10.10.10.10",
        )

    def test_objective_command_updates_session(self):
        self.cli.handle_input(
            "/objective privilege escalation"
        )

        self.assertEqual(
            self.session.status().objective,
            "privilege escalation",
        )

    def test_phase_command_updates_session(self):
        self.cli.handle_input(
            "/phase privilege escalation"
        )

        self.assertEqual(
            self.session.status().phase,
            "privilege escalation",
        )

    def test_observe_command_records_structured_observation(
        self,
    ):
        self.cli.handle_input(
            "/observe 80/tcp open http"
        )

        self.assertEqual(
            self.session.status().observations,
            (
                Observation(
                    description="80/tcp open http",
                    service="http",
                    port=80,
                    protocol="tcp",
                ),
            ),
        )

    def test_status_displays_current_session(self):
        self.session.set_target(
            "10.10.10.10"
        )

        self.session.set_objective(
            "Web enumeration"
        )

        self.session.record_observation(
            "80/tcp open http"
        )

        self.cli.handle_input("/status")

        output = "\n".join(self.output)

        self.assertIn(
            "Target: 10.10.10.10",
            output,
        )

        self.assertIn(
            "Objective: Web enumeration",
            output,
        )

        self.assertIn(
            "80/tcp open http",
            output,
        )

    def test_search_command_lists_matching_note(self):
        self.cli.handle_input(
            "/search Proxmox"
        )

        self.assertIn(
            "- Lab/Architecture.md",
            self.output,
        )

    def test_search_reports_no_matches(self):
        self.cli.handle_input(
            "/search nonexistent-topic"
        )

        self.assertIn(
            "No matching vault notes.",
            self.output,
        )

    def test_open_command_displays_note(self):
        self.cli.handle_input(
            '/open "Lab/Architecture.md"'
        )

        output = "\n".join(self.output)

        self.assertIn(
            "--- Lab/Architecture.md ---",
            output,
        )

        self.assertIn(
            "The OptiPlex runs Proxmox.",
            output,
        )

    def test_open_command_rejects_path_outside_vault(
        self,
    ):
        self.cli.handle_input(
            "/open ../Outside.md"
        )

        output = "\n".join(self.output)

        self.assertIn(
            "Unable to open note:",
            output,
        )

    def test_ask_command_uses_reasoning_service(self):
        self.cli.handle_input(
            "/ask What does my vault say about Proxmox?"
        )

        output = "\n".join(self.output)

        self.assertIn(
            "Sources:",
            output,
        )

        self.assertIn(
            "- Lab/Architecture.md",
            output,
        )

        self.assertIn(
            "Sentinel:",
            output,
        )

        self.assertIn(
            (
                "The OptiPlex is documented "
                "as the Proxmox host."
            ),
            output,
        )

    def test_ordinary_text_is_treated_as_question(self):
        self.cli.handle_input(
            "Tell me about Proxmox."
        )

        self.assertIsNotNone(
            self.provider.last_request
        )

        self.assertIn(
            "Tell me about Proxmox.",
            self.provider.last_request.prompt,
        )

    def test_reasoning_receives_live_cli_session_state(self):
        self.cli.handle_input(
            "/target 10.10.10.10"
        )

        self.cli.handle_input(
            "/objective Web enumeration"
        )

        self.cli.handle_input(
            "/phase enumeration"
        )

        self.cli.handle_input(
            "/observe 80/tcp open http"
        )

        self.cli.handle_input(
            "What should I focus on next?"
        )

        prompt = self.provider.last_request.prompt

        self.assertIn(
            "Target: 10.10.10.10",
            prompt,
        )

        self.assertIn(
            "Objective: Web enumeration",
            prompt,
        )

        self.assertIn(
            "Phase: enumeration",
            prompt,
        )

        self.assertIn(
            "- 80/tcp open http",
            prompt,
        )

    def test_build_cli_shares_session_with_reasoning_service(
        self,
    ):
        provider = FakeProvider()

        cli = build_cli(
            self.vault_path,
            provider=provider,
        )

        cli.handle_input(
            "/target 10.10.10.10"
        )

        cli.handle_input(
            "/objective Web enumeration"
        )

        cli.handle_input(
            "/observe 80/tcp open http"
        )

        cli.handle_input(
            "What should I focus on next?"
        )

        prompt = provider.last_request.prompt

        self.assertIn(
            "Target: 10.10.10.10",
            prompt,
        )

        self.assertIn(
            "Objective: Web enumeration",
            prompt,
        )

        self.assertIn(
            "- 80/tcp open http",
            prompt,
        )

    def test_reasoning_can_be_unavailable_without_breaking_cli(
        self,
    ):
        cli = SentinelCLI(
            session=self.session,
            vault_adapter=self.adapter,
            reasoning_service=None,
            output_fn=self.output.append,
        )

        cli.handle_input(
            "Tell me about Proxmox."
        )

        output = "\n".join(self.output)

        self.assertIn(
            (
                "Reasoning provider is "
                "not configured yet."
            ),
            output,
        )

        self.assertIn(
            (
                "Vault and session commands "
                "remain available."
            ),
            output,
        )

    def test_empty_state_command_argument_is_rejected(
        self,
    ):
        self.cli.handle_input("/target")

        self.assertIn(
            "Target must not be empty.",
            self.output,
        )

    def test_unknown_command_is_reported(self):
        self.cli.handle_input(
            "/something"
        )

        output = "\n".join(self.output)

        self.assertIn(
            "Unknown command: /something",
            output,
        )

    def test_quit_command_stops_command_loop(self):
        should_continue = (
            self.cli.handle_input("/quit")
        )

        self.assertFalse(should_continue)

        self.assertIn(
            "Exiting Sentinel.",
            self.output,
        )

    def test_exit_command_stops_command_loop(self):
        should_continue = (
            self.cli.handle_input("/exit")
        )

        self.assertFalse(should_continue)

    def test_empty_input_is_ignored(self):
        should_continue = (
            self.cli.handle_input("   ")
        )

        self.assertTrue(should_continue)

        self.assertEqual(
            self.output,
            [],
        )


if __name__ == "__main__":
    unittest.main()