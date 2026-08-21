from observation_parser import parse_observation
from runtime import SentinelRuntime
from state import EngagementState


def main() -> None:
    print("Project Sentinel — Phase 0.2: Structured State and Capability Registry")

    target = input("Target: ").strip()

    if not target:
        print("Target cannot be empty.")
        return

    state = EngagementState(target=target)

    print("\nPaste one observation.")
    print("Example: 80/tcp open http")

    raw_observation = input("> ")

    try:
        observation = parse_observation(raw_observation)
    except ValueError as error:
        print(f"Invalid observation: {error}")
        return

    state.add_observation(observation)

    SentinelRuntime().step(state)

    print("\n--- Engagement State ---")
    print(f"Observations: {state.observations}")
    print(f"Actions completed: {state.actions_completed}")


if __name__ == "__main__":
    main()