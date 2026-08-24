import tempfile
import unittest
from pathlib import Path

from context_manager import ContextManager, WorkingContext
from session import SentinelSession
from vault_adapter import VaultAdapter, VaultNote


class ContextManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)
        self.adapter = VaultAdapter(self.vault_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_builds_context_from_matching_note(self):
        note_path = self.vault_path / "Enumeration.md"
        note_path.write_text(
            (
                "# Enumeration\n\n"
                "Start by identifying exposed services."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context("exposed services")

        self.assertEqual(
            context,
            WorkingContext(
                query="exposed services",
                notes=(
                    VaultNote(
                        path="Enumeration.md",
                        content=(
                            "# Enumeration\n\n"
                            "Start by identifying exposed services."
                        ),
                    ),
                ),
                unresolved_links=(),
            ),
        )

    def test_preserves_multiple_matching_notes(self):
        first_note = self.vault_path / "HTTP.md"
        first_note.write_text(
            "# HTTP\n\nEnumerate the HTTP service.",
            encoding="utf-8",
        )

        second_note = self.vault_path / "Web.md"
        second_note.write_text(
            "# Web\n\nHTTP applications require enumeration.",
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context("HTTP")

        self.assertEqual(
            {note.path for note in context.notes},
            {"HTTP.md", "Web.md"},
        )

    def test_includes_directly_linked_note(self):
        first_note = self.vault_path / "Enumeration.md"
        first_note.write_text(
            (
                "# Enumeration\n\n"
                "Review the HTTP service.\n\n"
                "See [[Web Methodology]]."
            ),
            encoding="utf-8",
        )

        linked_note = self.vault_path / "Web Methodology.md"
        linked_note.write_text(
            (
                "# Web Methodology\n\n"
                "Perform web enumeration."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context("HTTP service")

        self.assertEqual(
            [note.path for note in context.notes],
            [
                "Enumeration.md",
                "Web Methodology.md",
            ],
        )

    def test_does_not_duplicate_linked_note(self):
        first_note = self.vault_path / "Enumeration.md"
        first_note.write_text(
            (
                "# Enumeration\n\n"
                "HTTP enumeration.\n\n"
                "See [[Web]]."
            ),
            encoding="utf-8",
        )

        second_note = self.vault_path / "Web.md"
        second_note.write_text(
            (
                "# Web\n\n"
                "HTTP enumeration methodology."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context("HTTP")

        paths = [note.path for note in context.notes]

        self.assertEqual(
            paths.count("Web.md"),
            1,
        )

    def test_does_not_recursively_follow_linked_notes(self):
        first_note = self.vault_path / "Start.md"
        first_note.write_text(
            (
                "# Start\n\n"
                "Initial enumeration.\n\n"
                "See [[Second]]."
            ),
            encoding="utf-8",
        )

        second_note = self.vault_path / "Second.md"
        second_note.write_text(
            (
                "# Second\n\n"
                "Additional methodology.\n\n"
                "See [[Third]]."
            ),
            encoding="utf-8",
        )

        third_note = self.vault_path / "Third.md"
        third_note.write_text(
            (
                "# Third\n\n"
                "This should not be followed recursively."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            "Initial enumeration"
        )

        self.assertEqual(
            [note.path for note in context.notes],
            [
                "Start.md",
                "Second.md",
            ],
        )

    def test_records_missing_link_as_unresolved(self):
        note_path = self.vault_path / "Enumeration.md"
        note_path.write_text(
            (
                "# Enumeration\n\n"
                "HTTP enumeration.\n\n"
                "See [[Missing Note]]."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            "HTTP enumeration"
        )

        self.assertEqual(
            context.unresolved_links,
            ("Missing Note",),
        )

    def test_records_ambiguous_link_as_unresolved(self):
        first_directory = self.vault_path / "One"
        second_directory = self.vault_path / "Two"

        first_directory.mkdir()
        second_directory.mkdir()

        start_note = self.vault_path / "Start.md"
        start_note.write_text(
            (
                "# Start\n\n"
                "HTTP enumeration.\n\n"
                "See [[Architecture]]."
            ),
            encoding="utf-8",
        )

        (
            first_directory / "Architecture.md"
        ).write_text(
            "# Architecture\n\nFirst architecture note.",
            encoding="utf-8",
        )

        (
            second_directory / "Architecture.md"
        ).write_text(
            "# Architecture\n\nSecond architecture note.",
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            "HTTP enumeration"
        )

        self.assertEqual(
            context.unresolved_links,
            ("Architecture",),
        )

    def test_limits_number_of_context_notes(self):
        first_note = self.vault_path / "One.md"
        first_note.write_text(
            (
                "# One\n\n"
                "HTTP enumeration.\n\n"
                "See [[Two]]."
            ),
            encoding="utf-8",
        )

        second_note = self.vault_path / "Two.md"
        second_note.write_text(
            "# Two\n\nHTTP enumeration.",
            encoding="utf-8",
        )

        third_note = self.vault_path / "Three.md"
        third_note.write_text(
            "# Three\n\nHTTP enumeration.",
            encoding="utf-8",
        )

        manager = ContextManager(
            self.adapter,
            max_notes=2,
        )

        context = manager.build_context("HTTP")

        self.assertEqual(
            len(context.notes),
            2,
        )

    def test_rejects_empty_query(self):
        manager = ContextManager(self.adapter)

        with self.assertRaises(ValueError):
            manager.build_context("   ")

    def test_rejects_invalid_max_notes(self):
        with self.assertRaises(ValueError):
            ContextManager(
                self.adapter,
                max_notes=0,
            )

    def test_retrieves_from_natural_language_query(self):
        note_path = self.vault_path / "Lab.md"
        note_path.write_text(
            "# Lab\n\nThe OptiPlex runs Proxmox.",
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            "What does my vault say about Proxmox?"
        )

        self.assertEqual(
            [note.path for note in context.notes],
            ["Lab.md"],
        )

    def test_combines_term_matches_without_duplicates(self):
        note_path = (
            self.vault_path / "Privilege Escalation.md"
        )
        note_path.write_text(
            (
                "# Privilege Escalation\n\n"
                "Linux privilege escalation methodology."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context(
            (
                "What do my notes say about "
                "Linux privilege escalation?"
            )
        )

        self.assertEqual(
            [note.path for note in context.notes],
            ["Privilege Escalation.md"],
        )

    def test_truncates_oversized_note_to_context_budget(self):
        note_path = self.vault_path / "Large.md"

        content = "Proxmox " + ("A" * 500)

        note_path.write_text(
            content,
            encoding="utf-8",
        )

        manager = ContextManager(
            self.adapter,
            max_context_chars=100,
        )

        context = manager.build_context("Proxmox")

        self.assertEqual(
            len(context.notes),
            1,
        )

        self.assertEqual(
            len(context.notes[0].content),
            100,
        )

        self.assertEqual(
            context.notes[0].path,
            "Large.md",
        )

        self.assertTrue(
            content.startswith(
                context.notes[0].content
            )
        )

    def test_limits_combined_note_content_to_context_budget(self):
        first_note = self.vault_path / "One.md"
        first_note.write_text(
            "HTTP " + ("A" * 100),
            encoding="utf-8",
        )

        second_note = self.vault_path / "Two.md"
        second_note.write_text(
            "HTTP " + ("B" * 100),
            encoding="utf-8",
        )

        manager = ContextManager(
            self.adapter,
            max_context_chars=120,
        )

        context = manager.build_context("HTTP")

        total_context_chars = sum(
            len(note.content)
            for note in context.notes
        )

        self.assertLessEqual(
            total_context_chars,
            120,
        )

    def test_rejects_invalid_context_budget(self):
        with self.assertRaises(ValueError):
            ContextManager(
                self.adapter,
                max_context_chars=0,
            )

    def test_session_objective_contributes_to_retrieval(self):
        operational_path = (
            self.vault_path / "Knowledge"
        )
        operational_path.mkdir()

        (
            operational_path / "Web Enumeration.md"
        ).write_text(
            (
                "# Web Enumeration\n\n"
                "Inspect HTTP services, routes and login forms."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        session = SentinelSession()
        session.set_objective("web enumeration")

        context = manager.build_context(
            "What should I investigate next?",
            session_status=session.status(),
        )

        self.assertEqual(
            [note.path for note in context.notes],
            ["Knowledge/Web Enumeration.md"],
        )

    def test_session_observation_contributes_to_retrieval(self):
        knowledge_path = self.vault_path / "Knowledge"
        knowledge_path.mkdir()

        (
            knowledge_path / "HTTP.md"
        ).write_text(
            (
                "# HTTP\n\n"
                "HTTP enumeration should inspect headers, "
                "routes and application behaviour."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        session = SentinelSession()
        session.record_observation(
            "80/tcp open http"
        )

        context = manager.build_context(
            "What should I investigate next?",
            session_status=session.status(),
        )

        self.assertEqual(
            [note.path for note in context.notes],
            ["Knowledge/HTTP.md"],
        )

    def test_operational_note_outranks_generic_project_note(
        self,
    ):
        knowledge_path = self.vault_path / "Knowledge"
        project_path = (
            self.vault_path / "Project Sentinel"
        )

        knowledge_path.mkdir()
        project_path.mkdir()

        (
            knowledge_path / "Web Enumeration.md"
        ).write_text(
            (
                "# Web Enumeration\n\n"
                "HTTP login enumeration methodology."
            ),
            encoding="utf-8",
        )

        (
            project_path / "Foundation Release.md"
        ).write_text(
            (
                "# Foundation Release\n\n"
                "The current session supports web enumeration "
                "and HTTP observations."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(
            self.adapter,
            max_notes=2,
        )

        session = SentinelSession()
        session.set_objective(
            "web enumeration"
        )
        session.set_phase(
            "enumeration"
        )
        session.record_observation(
            "80/tcp open http"
        )
        session.record_observation(
            "The login page appears to be custom-built"
        )

        context = manager.build_context(
            "Given my current session, "
            "what should I investigate next?",
            session_status=session.status(),
        )

        self.assertEqual(
            context.notes[0].path,
            "Knowledge/Web Enumeration.md",
        )

    def test_path_match_outranks_content_only_match(self):
        knowledge_path = self.vault_path / "Knowledge"
        project_path = self.vault_path / "Project"

        knowledge_path.mkdir()
        project_path.mkdir()

        (
            knowledge_path / "Enumeration.md"
        ).write_text(
            "# Enumeration\n\nMethodology.",
            encoding="utf-8",
        )

        (
            project_path / "Roadmap.md"
        ).write_text(
            (
                "# Roadmap\n\n"
                "Enumeration is mentioned here."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(
            self.adapter,
            max_notes=2,
        )

        context = manager.build_context(
            "enumeration"
        )

        self.assertEqual(
            context.notes[0].path,
            "Knowledge/Enumeration.md",
        )


if __name__ == "__main__":
    unittest.main()