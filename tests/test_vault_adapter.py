import tempfile
import unittest
from pathlib import Path

from vault_adapter import VaultAdapter, VaultNote


class VaultAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)

        self.note_path = self.vault_path / "Enumeration.md"
        self.note_path.write_text(
            "# Enumeration\n\nStart by identifying exposed services.",
            encoding="utf-8",
        )

        self.adapter = VaultAdapter(self.vault_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_reads_existing_markdown_note(self):
        note = self.adapter.read_note("Enumeration.md")

        self.assertEqual(
            note,
            VaultNote(
                path="Enumeration.md",
                content="# Enumeration\n\nStart by identifying exposed services.",
            ),
        )

    def test_missing_note_raises_file_not_found_error(self):
        with self.assertRaises(FileNotFoundError):
            self.adapter.read_note("Missing.md")

    def test_rejects_path_outside_vault(self):
        outside_path = self.vault_path.parent / "Outside.md"
        outside_path.write_text(
            "# Outside\n\nThis file is not part of the vault.",
            encoding="utf-8",
        )

        with self.assertRaises(ValueError):
            self.adapter.read_note("../Outside.md")

    def test_reads_nested_markdown_note(self):
        lab_path = self.vault_path / "Lab"
        lab_path.mkdir()

        architecture_path = lab_path / "Architecture.md"
        architecture_path.write_text(
            "# Architecture\n\nThe OptiPlex is the Proxmox host.",
            encoding="utf-8",
        )

        note = self.adapter.read_note("Lab/Architecture.md")

        self.assertEqual(
            note,
            VaultNote(
                path="Lab/Architecture.md",
                content="# Architecture\n\nThe OptiPlex is the Proxmox host.",
            ),
        )

    def test_search_finds_matching_note_in_nested_directory(self):
        lab_path = self.vault_path / "Lab"
        lab_path.mkdir()

        architecture_path = lab_path / "Architecture.md"
        architecture_path.write_text(
            "# Architecture\n\nThe OptiPlex runs Proxmox.",
            encoding="utf-8",
        )

        results = self.adapter.search_notes("Proxmox")

        self.assertEqual(
            results,
            [
                VaultNote(
                    path="Lab/Architecture.md",
                    content="# Architecture\n\nThe OptiPlex runs Proxmox.",
                )
            ],
        )

    def test_search_is_case_insensitive(self):
        results = self.adapter.search_notes("enumeration")

        self.assertEqual(
            results,
            [
                VaultNote(
                    path="Enumeration.md",
                    content="# Enumeration\n\nStart by identifying exposed services.",
                )
            ],
        )

    def test_search_returns_multiple_matching_notes(self):
        lab_path = self.vault_path / "Lab"
        lab_path.mkdir()

        architecture_path = lab_path / "Architecture.md"
        architecture_path.write_text(
            "# Architecture\n\nThe OptiPlex runs Proxmox.",
            encoding="utf-8",
        )

        virtualisation_path = lab_path / "Virtualisation.md"
        virtualisation_path.write_text(
            "# Virtualisation\n\nProxmox hosts the Kali VM.",
            encoding="utf-8",
        )

        results = self.adapter.search_notes("Proxmox")

        self.assertEqual(
            results,
            [
                VaultNote(
                    path="Lab/Architecture.md",
                    content="# Architecture\n\nThe OptiPlex runs Proxmox.",
                ),
                VaultNote(
                    path="Lab/Virtualisation.md",
                    content="# Virtualisation\n\nProxmox hosts the Kali VM.",
                ),
            ],
        )

    def test_search_rejects_empty_query(self):
        with self.assertRaises(ValueError):
            self.adapter.search_notes("   ")


if __name__ == "__main__":
    unittest.main()