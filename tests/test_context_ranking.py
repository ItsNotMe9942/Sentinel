import tempfile
import unittest
from pathlib import Path

from context_manager import (
    ContextManager,
    RetrievalIntent,
)
from session import SentinelSession
from vault_adapter import VaultAdapter


class ContextRankingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)

        self.knowledge_path = (
            self.vault_path / "Knowledge"
        )
        self.machines_path = (
            self.vault_path / "Machines"
        )
        self.project_path = (
            self.vault_path / "Project Sentinel"
        )
        self.lab_path = (
            self.vault_path / "Lab"
        )
        self.templates_path = (
            self.vault_path / "Templates"
        )

        self.knowledge_path.mkdir()
        self.machines_path.mkdir()
        self.project_path.mkdir()
        self.lab_path.mkdir()
        self.templates_path.mkdir()

        self.adapter = VaultAdapter(self.vault_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _web_session(
        self,
        target: str = "10.10.10.10",
    ) -> SentinelSession:
        session = SentinelSession()

        session.set_target(target)
        session.set_objective("web enumeration")
        session.set_phase("enumeration")

        session.record_observation(
            "80/tcp open http"
        )

        session.record_observation(
            "The login page appears custom-built"
        )

        return session

    def _create_jump_machine(
        self,
        target: str = "10.130.171.173",
    ) -> None:
        jump_path = self.machines_path / "Jump"
        notes_path = jump_path / "Notes"

        notes_path.mkdir(parents=True)

        (
            jump_path / "README.md.md"
        ).write_text(
            (
                "# Jump\n\n"
                f"Target: {target}\n\n"
                "Enumeration notes for Jump."
            ),
            encoding="utf-8",
        )

        (
            notes_path / "01 Enumeration.md.md"
        ).write_text(
            (
                "# Enumeration\n\n"
                "FTP incoming directory is writable.\n"
                "HTTP enumeration notes."
            ),
            encoding="utf-8",
        )

    def test_active_session_defaults_to_engagement_intent(
        self,
    ):
        manager = ContextManager(self.adapter)

        intent = manager._determine_retrieval_intent(
            "What should our next steps be?",
            self._web_session().status(),
        )

        self.assertEqual(
            intent,
            RetrievalIntent.ENGAGEMENT,
        )

    def test_explicit_lab_query_uses_lab_intent(
        self,
    ):
        manager = ContextManager(self.adapter)

        intent = manager._determine_retrieval_intent(
            "How is my Kali VM connected to Proxmox?",
            self._web_session().status(),
        )

        self.assertEqual(
            intent,
            RetrievalIntent.LAB,
        )

    def test_explicit_sentinel_query_uses_sentinel_intent(
        self,
    ):
        manager = ContextManager(self.adapter)

        intent = manager._determine_retrieval_intent(
            (
                "How does Sentinel's Context Manager "
                "work?"
            ),
            self._web_session().status(),
        )

        self.assertEqual(
            intent,
            RetrievalIntent.SENTINEL,
        )

    def test_query_without_session_uses_general_intent(
        self,
    ):
        manager = ContextManager(self.adapter)

        intent = manager._determine_retrieval_intent(
            "regular expressions",
            None,
        )

        self.assertEqual(
            intent,
            RetrievalIntent.GENERAL,
        )

    def test_engagement_intent_retrieves_knowledge(
        self,
    ):
        (
            self.knowledge_path / "Nmap.md.md"
        ).write_text(
            (
                "# Nmap\n\n"
                "Reusable HTTP and service "
                "enumeration methodology."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            "What should our next steps be?",
            session_status=self._web_session().status(),
        )

        self.assertIn(
            "Knowledge/Nmap.md.md",
            [
                note.path
                for note in context.notes
            ],
        )

    def test_engagement_intent_excludes_lab_context(
        self,
    ):
        (
            self.knowledge_path / "Nmap.md.md"
        ).write_text(
            (
                "# Nmap\n\n"
                "HTTP enumeration methodology."
            ),
            encoding="utf-8",
        )

        (
            self.lab_path / "Architecture.md"
        ).write_text(
            (
                "# Architecture\n\n"
                "HTTP services exist in the lab."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            "What should our next steps be?",
            session_status=self._web_session().status(),
        )

        paths = [
            note.path
            for note in context.notes
        ]

        self.assertIn(
            "Knowledge/Nmap.md.md",
            paths,
        )

        self.assertNotIn(
            "Lab/Architecture.md",
            paths,
        )

    def test_engagement_intent_excludes_project_docs(
        self,
    ):
        (
            self.knowledge_path / "Nmap.md.md"
        ).write_text(
            (
                "# Nmap\n\n"
                "HTTP enumeration methodology."
            ),
            encoding="utf-8",
        )

        (
            self.project_path / "Session Model.md"
        ).write_text(
            (
                "# Session Model\n\n"
                "HTTP enumeration session observations."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            "What should our next steps be?",
            session_status=self._web_session().status(),
        )

        paths = [
            note.path
            for note in context.notes
        ]

        self.assertNotIn(
            "Project Sentinel/Session Model.md",
            paths,
        )

    def test_engagement_intent_excludes_unrelated_machine(
        self,
    ):
        self._create_jump_machine(
            target="10.130.171.173"
        )

        (
            self.knowledge_path / "Nmap.md.md"
        ).write_text(
            (
                "# Nmap\n\n"
                "HTTP enumeration methodology."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            "What should our next steps be?",
            session_status=self._web_session(
                target="10.10.10.10"
            ).status(),
        )

        self.assertFalse(
            any(
                note.path.startswith("Machines/Jump/")
                for note in context.notes
            )
        )

    def test_engagement_intent_allows_matching_machine(
        self,
    ):
        self._create_jump_machine(
            target="10.130.171.173"
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            "What should our next steps be?",
            session_status=self._web_session(
                target="10.130.171.173"
            ).status(),
        )

        self.assertTrue(
            any(
                note.path.startswith("Machines/Jump/")
                for note in context.notes
            )
        )

    def test_engagement_intent_allows_templates(
        self,
    ):
        (
            self.templates_path / "Enumeration.md"
        ).write_text(
            (
                "# Enumeration\n\n"
                "Reusable enumeration checklist."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            "What should our next steps be?",
            session_status=self._web_session().status(),
        )

        self.assertIn(
            "Templates/Enumeration.md",
            [
                note.path
                for note in context.notes
            ],
        )

    def test_lab_intent_retrieves_lab_context_only(
        self,
    ):
        (
            self.lab_path / "Virtualisation and Kali.md"
        ).write_text(
            (
                "# Virtualisation and Kali\n\n"
                "The Kali VM runs on Proxmox."
            ),
            encoding="utf-8",
        )

        (
            self.knowledge_path / "Kali.md"
        ).write_text(
            (
                "# Kali\n\n"
                "General Kali methodology."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            "How is my Kali VM connected to Proxmox?",
            session_status=self._web_session().status(),
        )

        self.assertEqual(
            [
                note.path
                for note in context.notes
            ],
            [
                "Lab/Virtualisation and Kali.md",
            ],
        )

    def test_sentinel_intent_retrieves_project_docs_only(
        self,
    ):
        (
            self.project_path / "Context Manager.md"
        ).write_text(
            (
                "# Context Manager\n\n"
                "The Sentinel Context Manager "
                "selects retrieved knowledge."
            ),
            encoding="utf-8",
        )

        (
            self.knowledge_path / "Context.md"
        ).write_text(
            (
                "# Context\n\n"
                "General context-management notes."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            (
                "How does Sentinel's "
                "Context Manager work?"
            ),
            session_status=self._web_session().status(),
        )

        self.assertEqual(
            [
                note.path
                for note in context.notes
            ],
            [
                "Project Sentinel/Context Manager.md",
            ],
        )

    def test_general_intent_can_search_across_domains(
        self,
    ):
        (
            self.knowledge_path / "Regex.md"
        ).write_text(
            (
                "# Regex\n\n"
                "Regular expressions."
            ),
            encoding="utf-8",
        )

        (
            self.lab_path / "Regex Notes.md"
        ).write_text(
            (
                "# Regex Notes\n\n"
                "Regular expressions in lab notes."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(
            self.adapter,
            max_notes=5,
        )

        context = manager.build_context(
            "regular expressions"
        )

        paths = {
            note.path
            for note in context.notes
        }

        self.assertEqual(
            paths,
            {
                "Knowledge/Regex.md",
                "Lab/Regex Notes.md",
            },
        )

    def test_linked_note_cannot_escape_engagement_intent(
        self,
    ):
        (
            self.knowledge_path / "Web Enumeration.md"
        ).write_text(
            (
                "# Web Enumeration\n\n"
                "HTTP methodology.\n\n"
                "See [[Lab/Architecture]].\n"
                "See [[Project Sentinel/Session Model]]."
            ),
            encoding="utf-8",
        )

        (
            self.lab_path / "Architecture.md"
        ).write_text(
            "# Architecture\n\nLab architecture.",
            encoding="utf-8",
        )

        (
            self.project_path / "Session Model.md"
        ).write_text(
            "# Session Model\n\nSentinel architecture.",
            encoding="utf-8",
        )

        manager = ContextManager(
            self.adapter,
            max_notes=5,
        )

        context = manager.build_context(
            "web enumeration",
            session_status=self._web_session().status(),
        )

        paths = [
            note.path
            for note in context.notes
        ]

        self.assertEqual(
            paths,
            ["Knowledge/Web Enumeration.md"],
        )


if __name__ == "__main__":
    unittest.main()