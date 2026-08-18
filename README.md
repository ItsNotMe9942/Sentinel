# Project Sentinel

**Human-led. AI-assisted. Operator controlled.**

Project Sentinel is an experimental cybersecurity assistant designed to support pentesting, security research and learning without removing the human operator from the decision-making process.

Rather than building an autonomous agent and then trying to constrain it afterwards, Sentinel starts from the opposite assumption:

**AI may reason, recommend and assist — but authority belongs to the operator.**

The project separates reasoning from execution through explicit policy, state and approval boundaries. Potentially consequential actions should be inspectable, explainable and subject to operator control before they reach the underlying system.

Sentinel is being built incrementally as both a practical security tool and an exploration of how AI can be integrated into cybersecurity workflows without turning the operator into a passenger.

Sentinel is also intended to reduce the cognitive overhead surrounding technical work. It should help maintain context, surface relevant knowledge and methodology, organise evidence, and support documentation as part of the workflow so that the operator can devote more attention to reasoning about the problem itself.

## Why Sentinel?

Modern AI systems can generate commands, analyse output and propose attack paths remarkably well. But capability alone isn't enough for a system operating around security tooling.

A useful pentesting assistant also needs to answer harder questions:

- What is it actually allowed to do?
- What information may leave the local environment?
- Which actions require explicit approval?
- What does the system know, and where did that knowledge come from?
- How should uncertainty be represented?
- How do we prevent persuasive model output from becoming authority?
- How do we preserve the operator's opportunity to think, learn and disagree?

Sentinel treats those questions as part of the architecture rather than as features to bolt on later.

## Current Status

Sentinel is currently in its **foundation / Phase 0 development stage**.

The present implementation focuses deliberately on the control plane rather than offensive capability: establishing the runtime, state model, policy boundaries, action lifecycle and testing strategy that later capabilities will depend upon.

Current milestone:

**Phase 0.1 — Minimal Control Loop**

Phase 0.1 was verified at prototype level on 2026-08-17. The current planner, policy, runtime and state test suites pass **10/10 tests**.

The aim at this stage isn't to make Sentinel powerful.

It's to make sure that when it becomes powerful, **we still know who's in control.**

## Running the Prototype

```bash
python3 main.py
```

## Running the Tests

```bash
python3 -m unittest discover -s tests -v
```

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

The planner does not yet model richer relationships between observations, findings, evidence and completed actions.

Expanding structured state and introducing explicitly registered bounded capabilities remain part of the Phase 0.2 work.

Execution remains simulated in Phase 0.1.

## Architectural Direction Beyond Phase 0

Phase 0 deliberately keeps model routing, long-term memory and Frontier integration outside the prototype control loop.

The accepted Project Sentinel architecture defines three logical reasoning tiers:

- **Local Fast**
- **Local Reasoning**
- **Frontier** — optional and explicitly controlled

These will be introduced behind stable interfaces after the deterministic runtime, structured state and capability registry have been validated.

Frontier use will be treated as **controlled data egress** and will not imply web, lab, tool or vault access. Model responses will be processed by Sentinel before any material is promoted into persistent memory or reusable knowledge.

This boundary preserves the purpose of Phase 0:

**prove that Sentinel controls state, policy and execution independently of whichever reasoning model is later attached.**

## Project Documentation

The Sentinel application repository contains the executable Python prototype and its tests.

The deeper project documentation — including the vision, requirements, architecture, Architectural Decision Records (ADRs), roadmap, development history and test records — is maintained separately in the **Project Sentinel Vault**:

[Project-Sentinel-Vault](https://github.com/ItsNotMe9942/Project-Sentinel-Vault)

This separation keeps the software repository focused on the implementation while preserving the reasoning and engineering decisions behind it.

---

Project Sentinel is under active development.

The current implementation is deliberately small. The architecture around it is being established first so that future capability is added within known boundaries rather than becoming the boundary itself.
