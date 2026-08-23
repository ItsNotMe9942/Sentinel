from dataclasses import dataclass

from context_manager import ContextManager, WorkingContext
from model_gateway import ModelGateway, ModelResponse
from session import SentinelSession, SessionStatus


@dataclass(frozen=True)
class ReasoningResult:
    context: WorkingContext
    response: ModelResponse
    session: SessionStatus | None = None


class ReasoningService:
    def __init__(
        self,
        context_manager: ContextManager,
        model_gateway: ModelGateway,
        session: SentinelSession | None = None,
    ) -> None:
        self.context_manager = context_manager
        self.model_gateway = model_gateway
        self.session = session

    def ask(self, query: str) -> ReasoningResult:
        context = self.context_manager.build_context(query)

        session_status = (
            self.session.status()
            if self.session is not None
            else None
        )

        prompt = self._build_prompt(
            context,
            session_status,
        )

        response = self.model_gateway.request(prompt)

        return ReasoningResult(
            context=context,
            response=response,
            session=session_status,
        )

    def _build_prompt(
        self,
        context: WorkingContext,
        session_status: SessionStatus | None,
    ) -> str:
        sections = [
            "OPERATOR QUERY",
            context.query,
            "",
            "CURRENT SESSION",
        ]

        if session_status is None:
            sections.append(
                "No session context was supplied."
            )
        else:
            sections.extend(
                [
                    (
                        "Target: "
                        f"{session_status.target or '(not set)'}"
                    ),
                    (
                        "Objective: "
                        f"{session_status.objective or '(not set)'}"
                    ),
                    f"Phase: {session_status.phase}",
                    "",
                    "Observations:",
                ]
            )

            if session_status.observations:
                for observation in session_status.observations:
                    sections.append(
                        f"- {observation.description}"
                    )
            else:
                sections.append("- None")

            sections.extend(
                [
                    "",
                    "Findings:",
                ]
            )

            if session_status.findings:
                for finding in session_status.findings:
                    sections.append(
                        f"- {finding}"
                    )
            else:
                sections.append("- None")

            sections.extend(
                [
                    "",
                    "Completed actions:",
                ]
            )

            if session_status.actions_completed:
                for action in session_status.actions_completed:
                    sections.append(
                        f"- {action}"
                    )
            else:
                sections.append("- None")

            sections.extend(
                [
                    "",
                    "Evidence:",
                ]
            )

            if session_status.evidence:
                for evidence in session_status.evidence:
                    sections.append(
                        f"- {evidence}"
                    )
            else:
                sections.append("- None")

        sections.extend(
            [
                "",
                "RETRIEVED KNOWLEDGE",
            ]
        )

        if not context.notes:
            sections.extend(
                [
                    "",
                    "No relevant vault notes were retrieved.",
                ]
            )

        for note in context.notes:
            sections.extend(
                [
                    "",
                    f"SOURCE: {note.path}",
                    note.content,
                ]
            )

        if context.unresolved_links:
            sections.extend(
                [
                    "",
                    "UNRESOLVED VAULT LINKS",
                ]
            )

            for link in context.unresolved_links:
                sections.append(f"- {link}")

        return "\n".join(sections)