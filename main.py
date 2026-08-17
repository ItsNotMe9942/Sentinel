from runtime import SentinelRuntime
from state import EngagementState


def main() -> None:
    print("Project Sentinel — Phase 0.1: Minimal Control Loop")

    target = input("Target: ").strip()
    state = EngagementState(target=target)

    print("\nPaste one observation.")
    print("Example: 22/tcp open ssh, 80/tcp open http")
    observation = input("> ").strip()
    state.add_observation(observation)

    SentinelRuntime().step(state)

    print("\n--- Engagement State ---")
    print(f"Observations: {state.observations}")
    print(f"Actions completed: {state.actions_completed}")


if __name__ == "__main__":
    main()
