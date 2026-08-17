# Sentinel

Project Sentinel application source code.

Current milestone: **Phase 0.1 — Minimal Control Loop**

## Run

```bash
python3 main.py
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

Phase 0.1 was verified at prototype level on 2026-08-17. The current planner, policy, runtime and state test suites pass **10/10 tests**.

Automated coverage currently verifies:

- HTTP observations produce an `enumerate_http` recommendation;
- completed HTTP enumeration is not recommended repeatedly;
- non-HTTP observations fall back to `review_observations`;
- actions requiring scope are denied when no target is defined;
- offensive actions require operator approval;
- approved actions are recorded in engagement state;
- declined actions are not recorded;
- policy-denied actions do not prompt for approval or mutate completed actions;
- observations are recorded in engagement state;
- completed actions are recorded in engagement state.

The approval, decline and no-target denial paths have also been exercised manually.

## Current Prototype Limitations

`RuleBasedPlanner` remains intentionally simple and rule-based. It currently recognises HTTP observations and can avoid repeating `enumerate_http` once that action has been recorded as completed.

The planner does not yet model richer relationships between observations, findings, evidence and completed actions. Expanding structured state and introducing explicitly registered bounded capabilities remain part of the Phase 0.2 work.

Execution remains simulated in Phase 0.1.


## Architectural Direction Beyond Phase 0

Phase 0 deliberately keeps model routing, long-term memory and Frontier integration outside the prototype control loop. The accepted Project Sentinel architecture now defines three logical reasoning tiers: **Local Fast**, **Local Reasoning** and optional **Frontier**.

These will be introduced behind stable interfaces after the deterministic runtime, structured state and capability registry have been validated. Frontier use will be treated as controlled data egress and will not imply web, lab, tool or vault access. Model responses will be processed by Sentinel before any material is promoted into persistent memory or reusable knowledge.

This boundary preserves the purpose of Phase 0: prove that Sentinel controls state, policy and execution independently of whichever reasoning model is later attached.
