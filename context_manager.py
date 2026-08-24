from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath

from session import SessionStatus
from vault_adapter import VaultAdapter, VaultNote


@dataclass(frozen=True)
class WorkingContext:
    query: str
    notes: tuple[VaultNote, ...]
    unresolved_links: tuple[str, ...]


class RetrievalIntent(Enum):
    ENGAGEMENT = "engagement"
    LAB = "lab"
    SENTINEL = "sentinel"
    GENERAL = "general"


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
        "built",
        "can",
        "could",
        "current",
        "do",
        "does",
        "for",
        "from",
        "given",
        "how",
        "i",
        "in",
        "investigate",
        "is",
        "it",
        "me",
        "my",
        "next",
        "of",
        "on",
        "open",
        "our",
        "page",
        "say",
        "session",
        "should",
        "steps",
        "tell",
        "that",
        "the",
        "think",
        "this",
        "to",
        "vault",
        "what",
        "where",
        "which",
        "with",
        "you",
    }

    SENTINEL_QUERY_MARKERS = {
        "sentinel",
        "project sentinel",
        "context manager",
        "vault adapter",
        "model gateway",
        "reasoning service",
        "agent runtime",
        "capability registry",
        "session model",
        "foundation release",
    }

    LAB_QUERY_MARKERS = {
        "my lab",
        "the lab",
        "lab architecture",
        "lab infrastructure",
        "proxmox",
        "optiplex",
        "kali vm",
        "hardware inventory",
        "virtualisation",
        "virtualization",
    }

    ENGAGEMENT_ROOTS = {
        "knowledge",
        "templates",
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

    def build_context(
        self,
        query: str,
        session_status: SessionStatus | None = None,
    ) -> WorkingContext:
        normalised_query = query.strip()

        if not normalised_query:
            raise ValueError("Context query must not be empty.")

        intent = self._determine_retrieval_intent(
            normalised_query,
            session_status,
        )

        target_machine_roots = (
            self._resolve_target_machine_roots(
                session_status
            )
        )

        ranked_results = self._retrieve_ranked_notes(
            normalised_query,
            session_status,
            intent,
            target_machine_roots,
        )

        selected_notes: list[VaultNote] = []
        selected_paths: set[str] = set()
        unresolved_links: list[str] = []

        for note in ranked_results:
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

                if not self._note_is_allowed_for_target(
                    linked_note,
                    session_status,
                    target_machine_roots,
                ):
                    continue

                if not self._note_matches_intent(
                    linked_note,
                    intent,
                    target_machine_roots,
                ):
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

    def _determine_retrieval_intent(
        self,
        query: str,
        session_status: SessionStatus | None,
    ) -> RetrievalIntent:
        normalised_query = query.casefold()

        if self._contains_marker(
            normalised_query,
            self.SENTINEL_QUERY_MARKERS,
        ):
            return RetrievalIntent.SENTINEL

        if self._contains_marker(
            normalised_query,
            self.LAB_QUERY_MARKERS,
        ):
            return RetrievalIntent.LAB

        if self._is_operational_session(
            session_status
        ):
            return RetrievalIntent.ENGAGEMENT

        return RetrievalIntent.GENERAL

    def _contains_marker(
        self,
        text: str,
        markers: set[str],
    ) -> bool:
        return any(
            marker in text
            for marker in markers
        )

    def _retrieve_ranked_notes(
        self,
        query: str,
        session_status: SessionStatus | None,
        intent: RetrievalIntent,
        target_machine_roots: set[str],
    ) -> list[VaultNote]:
        weighted_terms = self._build_weighted_terms(
            query,
            session_status,
            intent,
        )

        candidates: dict[str, VaultNote] = {}

        direct_results = self.vault_adapter.search_notes(
            query
        )

        for note in direct_results:
            self._add_candidate_if_allowed(
                candidates,
                note,
                session_status,
                intent,
                target_machine_roots,
            )

        for term in weighted_terms:
            matches = self.vault_adapter.search_notes(term)

            for note in matches:
                self._add_candidate_if_allowed(
                    candidates,
                    note,
                    session_status,
                    intent,
                    target_machine_roots,
                )

        return sorted(
            candidates.values(),
            key=lambda note: (
                -self._score_note(
                    note,
                    weighted_terms,
                    session_status,
                    intent,
                    target_machine_roots,
                ),
                note.path.casefold(),
            ),
        )

    def _add_candidate_if_allowed(
        self,
        candidates: dict[str, VaultNote],
        note: VaultNote,
        session_status: SessionStatus | None,
        intent: RetrievalIntent,
        target_machine_roots: set[str],
    ) -> None:
        if not self._note_is_allowed_for_target(
            note,
            session_status,
            target_machine_roots,
        ):
            return

        if not self._note_matches_intent(
            note,
            intent,
            target_machine_roots,
        ):
            return

        candidates[note.path] = note

    def _note_matches_intent(
        self,
        note: VaultNote,
        intent: RetrievalIntent,
        target_machine_roots: set[str],
    ) -> bool:
        root_directory = self._root_directory(
            note.path
        )

        if self._is_root_level_note(note.path):
            return True

        if intent is RetrievalIntent.GENERAL:
            return True

        if intent is RetrievalIntent.SENTINEL:
            return root_directory == "project sentinel"

        if intent is RetrievalIntent.LAB:
            return root_directory == "lab"

        if intent is RetrievalIntent.ENGAGEMENT:
            if root_directory in self.ENGAGEMENT_ROOTS:
                return True

            machine_root = self._machine_root(
                note.path
            )

            if machine_root is None:
                return False

            return machine_root in target_machine_roots

        return False

    def _resolve_target_machine_roots(
        self,
        session_status: SessionStatus | None,
    ) -> set[str]:
        if session_status is None:
            return set()

        if not session_status.target:
            return set()

        target = session_status.target.strip()

        if not target:
            return set()

        matching_notes = self.vault_adapter.search_notes(
            target
        )

        machine_roots: set[str] = set()

        for note in matching_notes:
            machine_root = self._machine_root(
                note.path
            )

            if machine_root is not None:
                machine_roots.add(machine_root)

        return machine_roots

    def _note_is_allowed_for_target(
        self,
        note: VaultNote,
        session_status: SessionStatus | None,
        target_machine_roots: set[str],
    ) -> bool:
        machine_root = self._machine_root(
            note.path
        )

        if machine_root is None:
            return True

        if session_status is None:
            return True

        if not session_status.target:
            return True

        return machine_root in target_machine_roots

    def _machine_root(
        self,
        note_path: str,
    ) -> str | None:
        parts = PurePosixPath(note_path).parts

        if len(parts) < 2:
            return None

        if parts[0].casefold() != "machines":
            return None

        return "/".join(parts[:2]).casefold()

    def _root_directory(
        self,
        note_path: str,
    ) -> str:
        parts = PurePosixPath(note_path).parts

        if not parts:
            return ""

        return parts[0].casefold()

    def _is_root_level_note(
        self,
        note_path: str,
    ) -> bool:
        return len(
            PurePosixPath(note_path).parts
        ) == 1

    def _build_weighted_terms(
        self,
        query: str,
        session_status: SessionStatus | None,
        intent: RetrievalIntent,
    ) -> dict[str, int]:
        weighted_terms: dict[str, int] = {}

        self._add_terms(
            weighted_terms,
            query,
            weight=1,
        )

        if intent is not RetrievalIntent.ENGAGEMENT:
            return weighted_terms

        if session_status is None:
            return weighted_terms

        if session_status.target:
            self._add_weighted_term(
                weighted_terms,
                session_status.target,
                weight=5,
            )

        if session_status.objective:
            self._add_weighted_term(
                weighted_terms,
                session_status.objective,
                weight=6,
            )

            self._add_terms(
                weighted_terms,
                session_status.objective,
                weight=4,
            )

        if session_status.phase:
            self._add_weighted_term(
                weighted_terms,
                session_status.phase,
                weight=3,
            )

            self._add_terms(
                weighted_terms,
                session_status.phase,
                weight=3,
            )

        for observation in session_status.observations:
            self._add_terms(
                weighted_terms,
                observation.description,
                weight=3,
            )

            if observation.service:
                self._add_weighted_term(
                    weighted_terms,
                    observation.service,
                    weight=5,
                )

            if observation.protocol:
                self._add_weighted_term(
                    weighted_terms,
                    observation.protocol,
                    weight=2,
                )

            if observation.port is not None:
                self._add_weighted_term(
                    weighted_terms,
                    str(observation.port),
                    weight=2,
                )

        for finding in session_status.findings:
            self._add_terms(
                weighted_terms,
                finding,
                weight=4,
            )

        return weighted_terms

    def _add_terms(
        self,
        weighted_terms: dict[str, int],
        text: str,
        weight: int,
    ) -> None:
        for term in self._extract_search_terms(text):
            self._add_weighted_term(
                weighted_terms,
                term,
                weight,
            )

    def _add_weighted_term(
        self,
        weighted_terms: dict[str, int],
        term: str,
        weight: int,
    ) -> None:
        normalised_term = term.strip().casefold()

        if not normalised_term:
            return

        existing_weight = weighted_terms.get(
            normalised_term,
            0,
        )

        weighted_terms[normalised_term] = max(
            existing_weight,
            weight,
        )

    def _score_note(
        self,
        note: VaultNote,
        weighted_terms: dict[str, int],
        session_status: SessionStatus | None,
        intent: RetrievalIntent,
        target_machine_roots: set[str],
    ) -> int:
        path = note.path.casefold()
        title = self._note_title(note)
        content = note.content.casefold()

        score = 0

        for term, weight in weighted_terms.items():
            if term in title:
                score += weight * 5
            elif term in path:
                score += weight * 3

            if term in content:
                score += weight

        if intent is RetrievalIntent.ENGAGEMENT:
            score += self._score_session_phrases(
                note,
                session_status,
            )

            score += self._score_target_machine(
                note,
                target_machine_roots,
            )

            root_directory = self._root_directory(
                note.path
            )

            if root_directory == "knowledge":
                score += 40

            if root_directory == "templates":
                score += 25

        elif intent is RetrievalIntent.LAB:
            if self._root_directory(note.path) == "lab":
                score += 40

        elif intent is RetrievalIntent.SENTINEL:
            if (
                self._root_directory(note.path)
                == "project sentinel"
            ):
                score += 40

        return score

    def _score_session_phrases(
        self,
        note: VaultNote,
        session_status: SessionStatus | None,
    ) -> int:
        if session_status is None:
            return 0

        title = self._note_title(note)
        content = note.content.casefold()

        score = 0

        if session_status.objective:
            objective = (
                session_status.objective
                .strip()
                .casefold()
            )

            if objective:
                if objective in title:
                    score += 30
                elif objective in content:
                    score += 8

        if session_status.phase:
            phase = (
                session_status.phase
                .strip()
                .casefold()
            )

            if phase:
                if phase in title:
                    score += 15
                elif phase in content:
                    score += 4

        for observation in session_status.observations:
            if observation.service:
                service = (
                    observation.service
                    .casefold()
                )

                if service in title:
                    score += 15

        return score

    def _score_target_machine(
        self,
        note: VaultNote,
        target_machine_roots: set[str],
    ) -> int:
        machine_root = self._machine_root(
            note.path
        )

        if machine_root is None:
            return 0

        if machine_root in target_machine_roots:
            return 60

        return 0

    def _is_operational_session(
        self,
        session_status: SessionStatus | None,
    ) -> bool:
        if session_status is None:
            return False

        return bool(
            session_status.target
            or session_status.objective
            or session_status.observations
            or session_status.findings
        )

    def _note_title(
        self,
        note: VaultNote,
    ) -> str:
        title = PurePosixPath(note.path).name.casefold()

        while title.endswith(".md"):
            title = title[:-3]

        return title

    def _extract_search_terms(
        self,
        text: str,
    ) -> list[str]:
        words = [
            word.strip(".,?!:;()[]{}\"'")
            for word in text.split()
        ]

        terms: list[str] = []

        for word in words:
            normalised_word = word.casefold()

            if not normalised_word:
                continue

            if normalised_word in self.STOP_WORDS:
                continue

            if len(normalised_word) < 3:
                continue

            if normalised_word not in terms:
                terms.append(normalised_word)

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