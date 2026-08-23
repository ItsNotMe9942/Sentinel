from dataclasses import dataclass

from vault_adapter import VaultAdapter, VaultNote


@dataclass(frozen=True)
class WorkingContext:
    query: str
    notes: tuple[VaultNote, ...]
    unresolved_links: tuple[str, ...]


class ContextManager:
    STOP_WORDS = {
        "a",
        "about",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "can",
        "could",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "me",
        "my",
        "of",
        "on",
        "say",
        "tell",
        "that",
        "the",
        "this",
        "to",
        "vault",
        "what",
        "where",
        "which",
        "with",
    }

    def __init__(
        self,
        vault_adapter: VaultAdapter,
        max_notes: int = 5,
        max_context_chars: int = 12000,
    ):
        if max_notes < 1:
            raise ValueError("max_notes must be at least 1.")

        if max_context_chars < 1:
            raise ValueError(
                "max_context_chars must be at least 1."
            )

        self.vault_adapter = vault_adapter
        self.max_notes = max_notes
        self.max_context_chars = max_context_chars

    def build_context(self, query: str) -> WorkingContext:
        normalised_query = query.strip()

        if not normalised_query:
            raise ValueError("Context query must not be empty.")

        direct_results = self._retrieve_notes(
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

        bounded_notes = self._apply_context_budget(
            selected_notes
        )

        return WorkingContext(
            query=normalised_query,
            notes=tuple(bounded_notes),
            unresolved_links=tuple(unresolved_links),
        )

    def _retrieve_notes(
        self,
        query: str,
    ) -> list[VaultNote]:
        direct_results = self.vault_adapter.search_notes(
            query
        )

        if direct_results:
            return direct_results

        search_terms = self._extract_search_terms(query)

        results: list[VaultNote] = []
        seen_paths: set[str] = set()

        for term in search_terms:
            matches = self.vault_adapter.search_notes(term)

            for note in matches:
                if note.path in seen_paths:
                    continue

                results.append(note)
                seen_paths.add(note.path)

        return results

    def _extract_search_terms(
        self,
        query: str,
    ) -> list[str]:
        words = [
            word.strip(".,?!:;()[]{}\"'")
            for word in query.split()
        ]

        terms = []

        for word in words:
            if not word:
                continue

            if word.casefold() in self.STOP_WORDS:
                continue

            if len(word) < 3:
                continue

            terms.append(word)

        return terms

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

    def _apply_context_budget(
        self,
        notes: list[VaultNote],
    ) -> list[VaultNote]:
        bounded_notes: list[VaultNote] = []
        remaining_chars = self.max_context_chars

        for note in notes:
            if remaining_chars <= 0:
                break

            if len(note.content) <= remaining_chars:
                bounded_notes.append(note)
                remaining_chars -= len(note.content)
                continue

            bounded_notes.append(
                VaultNote(
                    path=note.path,
                    content=note.content[:remaining_chars],
                )
            )

            remaining_chars = 0

        return bounded_notes