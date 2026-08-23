from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VaultNote:
    path: str
    content: str


class VaultAdapter:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path.resolve()

    def read_note(self, relative_path: str) -> VaultNote:
        note_path = (self.vault_path / relative_path).resolve()

        if not note_path.is_relative_to(self.vault_path):
            raise ValueError("Requested note is outside the configured vault.")

        content = note_path.read_text(encoding="utf-8")

        return VaultNote(
            path=relative_path,
            content=content,
        )

    def search_notes(self, query: str) -> list[VaultNote]:
        if not query.strip():
            raise ValueError("Search query must not be empty.")

        results = []
        normalised_query = query.casefold()

        for note_path in self.vault_path.rglob("*.md"):
            content = note_path.read_text(encoding="utf-8")

            if normalised_query in content.casefold():
                relative_path = note_path.relative_to(self.vault_path)

                results.append(
                    VaultNote(
                        path=str(relative_path),
                        content=content,
                    )
                )

        return results