from dataclasses import dataclass
from pathlib import Path
import re


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

        normalised_query = query.casefold()
        results = []

        for note_path in self.vault_path.rglob("*.md"):
            relative_path = note_path.relative_to(self.vault_path)
            content = note_path.read_text(encoding="utf-8")

            searchable_text = (
                f"{relative_path}\n{content}"
            ).casefold()

            if normalised_query in searchable_text:
                results.append(
                    VaultNote(
                        path=str(relative_path),
                        content=content,
                    )
                )

        return sorted(
            results,
            key=lambda note: note.path.casefold(),
        )

    def resolve_wikilink(self, link_name: str) -> VaultNote:
        target = self._normalise_wikilink_target(link_name)

        if "/" in target:
            relative_path = f"{target}.md"
            return self.read_note(relative_path)

        expected_name = f"{target}.md".casefold()

        matches = [
            note_path
            for note_path in self.vault_path.rglob("*.md")
            if note_path.name.casefold() == expected_name
        ]

        if not matches:
            raise FileNotFoundError(
                f"No note found for wikilink: {target}"
            )

        if len(matches) > 1:
            raise ValueError(
                f"Wikilink is ambiguous: {target}"
            )

        note_path = matches[0]
        relative_path = note_path.relative_to(self.vault_path)

        return VaultNote(
            path=str(relative_path),
            content=note_path.read_text(encoding="utf-8"),
        )

    def extract_wikilinks(self, note: VaultNote) -> list[str]:
        raw_links = re.findall(
            r"!?\[\[([^\[\]]+)\]\]",
            note.content,
        )

        links = []

        for raw_link in raw_links:
            target = self._normalise_wikilink_target(raw_link)

            if target not in links:
                links.append(target)

        return links

    def _normalise_wikilink_target(self, link_name: str) -> str:
        target = link_name.strip()

        if target.startswith("[[") and target.endswith("]]"):
            target = target[2:-2].strip()

        if "|" in target:
            target = target.split("|", 1)[0].strip()

        if "#" in target:
            target = target.split("#", 1)[0].strip()

        if target.casefold().endswith(".md"):
            target = target[:-3]

        if not target:
            raise ValueError("Wikilink name must not be empty.")

        return target