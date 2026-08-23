import tempfile
import unittest
from pathlib import Path

from context_manager import ContextManager, WorkingContext
from vault_adapter import VaultAdapter, VaultNote


class ContextManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)

        self.adapter = VaultAdapter(self.vault_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_builds_context_from_matching_note(self):
        note_path = self.vault_path / "Lab.md"
        note_path.write_text(
            "# Lab\n\nThe OptiPlex runs Proxmox.",
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context("Proxmox")

        self.assertEqual(
            context,
            WorkingContext(
                query="Proxmox",
                notes=(
                    VaultNote(
                        path="Lab.md",
                        content=(
                            "# Lab\n\n"
                            "The OptiPlex runs Proxmox."
                        ),
                    ),
                ),
                unresolved_links=(),
            ),
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

    def test_preserves_multiple_matching_notes(self):
        first_path = self.vault_path / "Architecture.md"
        first_path.write_text(
            "# Architecture\n\nProxmox hosts the lab.",
            encoding="utf-8",
        )

        second_path = self.vault_path / "Virtualisation.md"
        second_path.write_text(
            "# Virtualisation\n\nProxmox hosts Kali.",
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context("Proxmox")

        self.assertEqual(
            [note.path for note in context.notes],
            [
                "Architecture.md",
                "Virtualisation.md",
            ],
        )

    def test_limits_number_of_context_notes(self):
        for index in range(3):
            note_path = (
                self.vault_path / f"Note {index}.md"
            )
            note_path.write_text(
                f"# Note {index}\n\nProxmox information.",
                encoding="utf-8",
            )

        manager = ContextManager(
            self.adapter,
            max_notes=2,
        )

        context = manager.build_context("Proxmox")

        self.assertEqual(len(context.notes), 2)

    def test_includes_directly_linked_note(self):
        lab_path = self.vault_path / "Lab"
        lab_path.mkdir()

        architecture_path = (
            lab_path / "Architecture.md"
        )
        architecture_path.write_text(
            (
                "# Architecture\n\n"
                "The OptiPlex runs Proxmox.\n\n"
                "See [[Hardware Inventory]]."
            ),
            encoding="utf-8",
        )

        hardware_path = (
            lab_path / "Hardware Inventory.md"
        )
        hardware_path.write_text(
            (
                "# Hardware Inventory\n\n"
                "The OptiPlex has 8 GB RAM."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context("Proxmox")

        self.assertEqual(
            [note.path for note in context.notes],
            [
                "Lab/Architecture.md",
                "Lab/Hardware Inventory.md",
            ],
        )

    def test_does_not_recursively_follow_linked_notes(self):
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

        hardware_path = self.vault_path / "Hardware.md"
        hardware_path.write_text(
            (
                "# Hardware\n\n"
                "The host has 8 GB RAM.\n\n"
                "See [[Networking]]."
            ),
            encoding="utf-8",
        )

        networking_path = (
            self.vault_path / "Networking.md"
        )
        networking_path.write_text(
            "# Networking\n\nNetwork details.",
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context("Proxmox")

        self.assertEqual(
            [note.path for note in context.notes],
            [
                "Architecture.md",
                "Hardware.md",
            ],
        )

    def test_does_not_duplicate_linked_note(self):
        architecture_path = (
            self.vault_path / "Architecture.md"
        )
        architecture_path.write_text(
            (
                "# Architecture\n\n"
                "Proxmox architecture.\n\n"
                "See [[Hardware]]."
            ),
            encoding="utf-8",
        )

        hardware_path = self.vault_path / "Hardware.md"
        hardware_path.write_text(
            (
                "# Hardware\n\n"
                "Proxmox hardware."
            ),
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context("Proxmox")

        self.assertEqual(
            [note.path for note in context.notes],
            [
                "Architecture.md",
                "Hardware.md",
            ],
        )

    def test_records_missing_link_as_unresolved(self):
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

        manager = ContextManager(self.adapter)

        context = manager.build_context("Proxmox")

        self.assertEqual(
            context.unresolved_links,
            ("Missing Note",),
        )

    def test_records_ambiguous_link_as_unresolved(self):
        architecture_path = (
            self.vault_path / "Overview.md"
        )
        architecture_path.write_text(
            (
                "# Overview\n\n"
                "Proxmox overview.\n\n"
                "See [[Architecture]]."
            ),
            encoding="utf-8",
        )

        lab_path = self.vault_path / "Lab"
        lab_path.mkdir()

        sentinel_path = (
            self.vault_path / "Project Sentinel"
        )
        sentinel_path.mkdir()

        (lab_path / "Architecture.md").write_text(
            "# Architecture\n\nLab architecture.",
            encoding="utf-8",
        )

        (
            sentinel_path / "Architecture.md"
        ).write_text(
            "# Architecture\n\nSentinel architecture.",
            encoding="utf-8",
        )

        manager = ContextManager(self.adapter)

        context = manager.build_context("Proxmox")

        self.assertEqual(
            context.unresolved_links,
            ("Architecture",),
        )


if __name__ == "__main__":
    unittest.main()