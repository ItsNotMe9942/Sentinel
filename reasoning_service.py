from dataclasses import dataclass

from context_manager import ContextManager, WorkingContext
from model_gateway import ModelGateway, ModelResponse


@dataclass(frozen=True)
class ReasoningResult:
    context: WorkingContext
    response: ModelResponse


class ReasoningService:
    def __init__(
        self,
        context_manager: ContextManager,
        model_gateway: ModelGateway,
    ) -> None:
        self.context_manager = context_manager
        self.model_gateway = model_gateway

    def ask(self, query: str) -> ReasoningResult:
        context = self.context_manager.build_context(query)
        prompt = self._build_prompt(context)

        response = self.model_gateway.request(prompt)

        return ReasoningResult(
            context=context,
            response=response,
        )

    def _build_prompt(self, context: WorkingContext) -> str:
        sections = [
            "OPERATOR QUERY",
            context.query,
            "",
            "RETRIEVED KNOWLEDGE",
        ]

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