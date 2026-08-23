from dataclasses import dataclass

from vault_adapter import VaultAdapter, VaultNote


@dataclass(frozen=True)
class WorkingContext:
    query: str
    notes: tuple[VaultNote, ...]
    unresolved_links: tuple[str, ...]


class ContextManager:
    def __init__(
        self,
        vault_adapter: VaultAdapter,
        max_notes: int = 5,
    ):
        if max_notes < 1:
            raise ValueError("max_notes must be at least 1.")

        self.vault_adapter = vault_adapter
        self.max_notes = max_notes

    def build_context(self, query: str) -> WorkingContext:
        normalised_query = query.strip()

        if not normalised_query:
            raise ValueError("Context query must not be empty.")

        direct_results = self.vault_adapter.search_notes(
            normalised_query
        )

        selected_notes: list[VaultNote] = []
        selected_paths: set[str] = set()
        unresolved_links: list[str] = []

        for note in direct_results:
            self._add_note(
                note,
                selected_notes,
                selected_paths,
            )

            if len(selected_notes) >= self.max_notes:
                break

        direct_notes = tuple(selected_notes)

        for note in direct_notes:
            if len(selected_notes) >= self.max_notes:
                break

            links = self.vault_adapter.extract_wikilinks(note)

            for link in links:
                if len(selected_notes) >= self.max_notes:
                    break

                try:
                    linked_note = (
                        self.vault_adapter.resolve_wikilink(link)
                    )
                except (FileNotFoundError, ValueError):
                    if link not in unresolved_links:
                        unresolved_links.append(link)

                    continue

                self._add_note(
                    linked_note,
                    selected_notes,
                    selected_paths,
                )

        return WorkingContext(
            query=normalised_query,
            notes=tuple(selected_notes),
            unresolved_links=tuple(unresolved_links),
        )

    def _add_note(
        self,
        note: VaultNote,
        selected_notes: list[VaultNote],
        selected_paths: set[str],
    ) -> None:
        if note.path in selected_paths:
            return

        selected_notes.append(note)
        selected_paths.add(note.path)