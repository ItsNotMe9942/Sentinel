# Project Sentinel

**Human-led. AI-assisted. Operator controlled.**

Project Sentinel is an experimental cybersecurity assistant designed to support pentesting, security research and learning without removing the human operator from the decision-making process.

Rather than building an autonomous agent and then trying to constrain it afterwards, Sentinel starts from the opposite assumption:

**AI may reason, recommend and assist — but authority belongs to the operator.**

The project separates reasoning from execution through explicit policy, state and approval boundaries. Potentially consequential actions should be inspectable, explainable and subject to operator control before they reach the underlying system.

Sentinel is being built incrementally as both a practical security tool and an exploration of how AI can be integrated into cybersecurity workflows without turning the operator into a passenger.

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
