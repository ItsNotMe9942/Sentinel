import os
from collections.abc import Callable
from pathlib import Path

from context_manager import ContextManager
from llama_cpp_provider import LlamaCppProvider
from model_gateway import ModelGateway, ModelProvider
from reasoning_service import ReasoningService
from session import SentinelSession
from vault_adapter import VaultAdapter


BANNER = r"""
                  /\         /\
             ____/  \_______/  \____
            /                       \
           |      ◉           ◉      |
            \          /\           /
             \________/  \_________/
                     \____/

                 S E N T I N E L


Project Sentinel
Local workflow and knowledge assistant

Type /help for commands.
""".strip("\n")


class SentinelCLI:
    def __init__(
        self,
        session: SentinelSession,
        vault_adapter: VaultAdapter,
        reasoning_service: ReasoningService | None = None,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self.session = session
        self.vault_adapter = vault_adapter
        self.reasoning_service = reasoning_service
        self.input_fn = input_fn
        self.output_fn = output_fn

    def run(self) -> None:
        self._write("\n\n\n" + BANNER)

        while True:
            try:
                operator_input = self.input_fn("\nSentinel> ")
            except (EOFError, KeyboardInterrupt):
                self._write("\nExiting Sentinel.")
                break

            if not self.handle_input(operator_input):
                break

    def handle_input(self, operator_input: str) -> bool:
        text = operator_input.strip()

        if not text:
            return True

        if not text.startswith("/"):
            self._ask(text)
            return True

        command, argument = self._split_command(text)

        if command in {"/quit", "/exit"}:
            self._write("Exiting Sentinel.")
            return False

        if command == "/help":
            self._show_help()
            return True

        if command == "/target":
            self._set_target(argument)
            return True

        if command == "/objective":
            self._set_objective(argument)
            return True

        if command == "/phase":
            self._set_phase(argument)
            return True

        if command == "/observe":
            self._record_observation(argument)
            return True

        if command == "/status":
            self._show_status()
            return True

        if command == "/search":
            self._search_vault(argument)
            return True

        if command == "/open":
            self._open_note(argument)
            return True

        if command == "/ask":
            self._ask(argument)
            return True

        self._write(
            f"Unknown command: {command}. "
            "Type /help for available commands."
        )

        return True

    def _split_command(self, text: str) -> tuple[str, str]:
        command, separator, argument = text.partition(" ")

        if not separator:
            return command.casefold(), ""

        return command.casefold(), argument.strip()

    def _set_target(self, target: str) -> None:
        try:
            self.session.set_target(target)
        except ValueError as exc:
            self._write(str(exc))
            return

        self._write(
            f"Target set: {self.session.status().target}"
        )

    def _set_objective(self, objective: str) -> None:
        try:
            self.session.set_objective(objective)
        except ValueError as exc:
            self._write(str(exc))
            return

        self._write(
            f"Objective set: {self.session.status().objective}"
        )

    def _set_phase(self, phase: str) -> None:
        try:
            self.session.set_phase(phase)
        except ValueError as exc:
            self._write(str(exc))
            return

        self._write(
            f"Phase set: {self.session.status().phase}"
        )

    def _record_observation(
        self,
        raw_observation: str,
    ) -> None:
        try:
            observation = self.session.record_observation(
                raw_observation
            )
        except ValueError as exc:
            self._write(str(exc))
            return

        self._write(
            f"Observation recorded: {observation.description}"
        )

    def _show_status(self) -> None:
        status = self.session.status()

        self._write("")
        self._write("Current session")
        self._write(
            f"Target: {status.target or '(not set)'}"
        )
        self._write(
            f"Objective: {status.objective or '(not set)'}"
        )
        self._write(f"Phase: {status.phase}")

        self._write("")
        self._write("Observations:")

        if status.observations:
            for observation in status.observations:
                self._write(
                    f"- {observation.description}"
                )
        else:
            self._write("- None")

        self._write("")
        self._write("Findings:")

        if status.findings:
            for finding in status.findings:
                self._write(f"- {finding}")
        else:
            self._write("- None")

        self._write("")
        self._write("Completed actions:")

        if status.actions_completed:
            for action in status.actions_completed:
                self._write(f"- {action}")
        else:
            self._write("- None")

        self._write("")
        self._write("Evidence:")

        if status.evidence:
            for item in status.evidence:
                self._write(f"- {item}")
        else:
            self._write("- None")

    def _search_vault(self, query: str) -> None:
        try:
            results = self.vault_adapter.search_notes(
                query
            )
        except ValueError as exc:
            self._write(str(exc))
            return

        if not results:
            self._write("No matching vault notes.")
            return

        self._write("")
        self._write("Matching vault notes:")

        for note in results:
            self._write(f"- {note.path}")

    def _open_note(self, relative_path: str) -> None:
        path = self._remove_wrapping_quotes(
            relative_path
        )

        if not path:
            self._write("Note path must not be empty.")
            return

        try:
            note = self.vault_adapter.read_note(path)
        except (FileNotFoundError, ValueError) as exc:
            self._write(
                f"Unable to open note: {exc}"
            )
            return

        self._write("")
        self._write(f"--- {note.path} ---")
        self._write(note.content)
        self._write("---")

    def _ask(self, query: str) -> None:
        question = query.strip()

        if not question:
            self._write("Question must not be empty.")
            return

        if self.reasoning_service is None:
            self._write(
                "Reasoning provider is not configured yet."
            )
            self._write(
                "Vault and session commands remain available."
            )
            return

        try:
            result = self.reasoning_service.ask(
                question
            )
        except (ConnectionError, ValueError) as exc:
            self._write(
                f"Reasoning unavailable: {exc}"
            )
            return

        self._write("")
        self._write("Sources:")

        if result.context.notes:
            for note in result.context.notes:
                self._write(f"- {note.path}")
        else:
            self._write("- No vault notes retrieved")

        if result.context.unresolved_links:
            self._write("")
            self._write("Unresolved vault links:")

            for link in result.context.unresolved_links:
                self._write(f"- {link}")

        self._write("")
        self._write("Sentinel:")
        self._write(result.response.content)

    def _show_help(self) -> None:
        self._write(
            """
Available commands:

  /target <target>
      Set the current engagement target.

  /objective <objective>
      Set the current operator objective.

  /phase <phase>
      Set the current workflow phase.

  /observe <observation>
      Record an explicit engagement observation.

  /status
      Show the current session state.

  /search <query>
      Search the configured Obsidian vault.

  /open <relative path>
      Display a note from the vault.

  /ask <question>
      Ask Sentinel using session and bounded vault context.

  /help
      Show this help.

  /quit
  /exit
      Exit Sentinel.

Ordinary text is treated as a reasoning question.
""".strip()
        )

    def _remove_wrapping_quotes(
        self,
        value: str,
    ) -> str:
        text = value.strip()

        if len(text) >= 2:
            if (
                text[0] == text[-1]
                and text[0] in {'"', "'"}
            ):
                return text[1:-1].strip()

        return text

    def _write(self, text: str) -> None:
        self.output_fn(text)


def build_cli(
    vault_path: Path,
    provider: ModelProvider | None = None,
) -> SentinelCLI:
    vault_adapter = VaultAdapter(vault_path)

    session = SentinelSession()

    context_manager = ContextManager(
        vault_adapter
    )

    if provider is None:
        provider = LlamaCppProvider()

    model_gateway = ModelGateway(
        provider
    )

    reasoning_service = ReasoningService(
        context_manager,
        model_gateway,
        session=session,
    )

    return SentinelCLI(
        session=session,
        vault_adapter=vault_adapter,
        reasoning_service=reasoning_service,
    )


def main() -> None:
    configured_path = os.environ.get(
        "SENTINEL_VAULT_PATH"
    )

    if not configured_path:
        print(
            "Sentinel startup failed: "
            "SENTINEL_VAULT_PATH is not configured."
        )
        return

    vault_path = Path(
        configured_path
    ).expanduser()

    if not vault_path.is_dir():
        print(
            "Sentinel startup failed: "
            f"vault does not exist: {vault_path}"
        )
        return

    cli = build_cli(vault_path)
    cli.run()


if __name__ == "__main__":
    main()