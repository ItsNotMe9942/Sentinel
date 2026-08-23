import tempfile
import unittest
from pathlib import Path

from context_manager import ContextManager
from model_gateway import (
    ModelGateway,
    ModelRequest,
    ModelResponse,
)
from reasoning_service import (
    ReasoningResult,
    ReasoningService,
)
from session import SentinelSession
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


class ReasoningServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)

        self.adapter = VaultAdapter(self.vault_path)

        self.context_manager = ContextManager(
            self.adapter
        )

        self.provider = FakeProvider()
        self.gateway = ModelGateway(self.provider)

        self.session = SentinelSession()

        self.service = ReasoningService(
            self.context_manager,
            self.gateway,
            session=self.session,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_returns_model_response(self):
        self.provider.response_content = (
            "Review the Proxmox configuration."
        )

        result = self.service.ask("Proxmox")

        self.assertEqual(
            result.response,
            ModelResponse(
                content=(
                    "Review the Proxmox configuration."
                )
            ),
        )

    def test_returns_working_context_with_response(self):
        note_path = self.vault_path / "Lab.md"
        note_path.write_text(
            "# Lab\n\nThe OptiPlex runs Proxmox.",
            encoding="utf-8",
        )

        result = self.service.ask("Proxmox")

        self.assertIsInstance(
            result,
            ReasoningResult,
        )

        self.assertEqual(
            [note.path for note in result.context.notes],
            ["Lab.md"],
        )

    def test_returns_session_snapshot_with_response(self):
        self.session.set_target("10.10.10.10")
        self.session.set_objective(
            "Web enumeration"
        )

        result = self.service.ask("Proxmox")

        self.assertIsNotNone(result.session)

        self.assertEqual(
            result.session.target,
            "10.10.10.10",
        )

        self.assertEqual(
            result.session.objective,
            "Web enumeration",
        )

    def test_prompt_contains_operator_query(self):
        self.service.ask(
            "How is Proxmox configured?"
        )

        self.assertIsNotNone(
            self.provider.last_request
        )

        self.assertIn(
            "OPERATOR QUERY",
            self.provider.last_request.prompt,
        )

        self.assertIn(
            "How is Proxmox configured?",
            self.provider.last_request.prompt,
        )

    def test_prompt_contains_current_session_state(self):
        self.session.set_target(
            "10.10.10.10"
        )
        self.session.set_objective(
            "Web enumeration"
        )
        self.session.set_phase(
            "enumeration"
        )

        self.session.record_observation(
            "80/tcp open http"
        )

        self.session.record_observation(
            "The login page appears to be custom-built"
        )

        self.service.ask(
            "What should I focus on next?"
        )

        prompt = self.provider.last_request.prompt

        self.assertIn(
            "CURRENT SESSION",
            prompt,
        )

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

        self.assertIn(
            (
                "- The login page appears "
                "to be custom-built"
            ),
            prompt,
        )

    def test_prompt_contains_retrieved_note_and_source(self):
        lab_path = self.vault_path / "Lab"
        lab_path.mkdir()

        architecture_path = (
            lab_path / "Architecture.md"
        )
        architecture_path.write_text(
            (
                "# Architecture\n\n"
                "The OptiPlex runs Proxmox."
            ),
            encoding="utf-8",
        )

        self.service.ask("Proxmox")

        prompt = self.provider.last_request.prompt

        self.assertIn(
            "RETRIEVED KNOWLEDGE",
            prompt,
        )

        self.assertIn(
            "SOURCE: Lab/Architecture.md",
            prompt,
        )

        self.assertIn(
            "The OptiPlex runs Proxmox.",
            prompt,
        )

    def test_prompt_records_when_no_notes_are_found(self):
        self.service.ask(
            "knowledge-that-does-not-exist"
        )

        self.assertIn(
            "No relevant vault notes were retrieved.",
            self.provider.last_request.prompt,
        )

    def test_prompt_includes_directly_linked_knowledge(self):
        architecture_path = (
            self.vault_path / "Architecture.md"
        )
        architecture_path.write_text(
            (
                "# Architecture\n\n"
                "Proxmox hosts the lab.\n\n"
                "See [[Hardware]]."
            ),
            encoding="utf-8",
        )

        hardware_path = (
            self.vault_path / "Hardware.md"
        )
        hardware_path.write_text(
            "# Hardware\n\nThe host has 8 GB RAM.",
            encoding="utf-8",
        )

        self.service.ask("Proxmox")

        prompt = self.provider.last_request.prompt

        self.assertIn(
            "SOURCE: Architecture.md",
            prompt,
        )

        self.assertIn(
            "SOURCE: Hardware.md",
            prompt,
        )

    def test_prompt_exposes_unresolved_links(self):
        architecture_path = (
            self.vault_path / "Architecture.md"
        )
        architecture_path.write_text(
            (
                "# Architecture\n\n"
                "Proxmox hosts the lab.\n\n"
                "See [[Missing Note]]."
            ),
            encoding="utf-8",
        )

        self.service.ask("Proxmox")

        prompt = self.provider.last_request.prompt

        self.assertIn(
            "UNRESOLVED VAULT LINKS",
            prompt,
        )

        self.assertIn(
            "- Missing Note",
            prompt,
        )


if __name__ == "__main__":
    unittest.main()