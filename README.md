# Sentinel

**Human-led. AI-assisted. Operator controlled.**

Sentinel is an experimental local cybersecurity workflow and knowledge assistant designed to support penetration testing, security research and learning while keeping the human operator in control.

It is the software implementation developed as part of **Project Sentinel**.

Rather than treating an AI model as the application, Sentinel treats reasoning as one bounded capability within a wider system responsible for session state, knowledge retrieval, context management, policy, execution and operator control.

The long-term goal is not to build an autonomous penetration-testing agent.

The goal is to build a system that understands the operator's current engagement, retrieves useful knowledge at the right time, preserves reasoning and evidence, assists with repeatable workflows and reduces the cognitive overhead surrounding technical work.

> **A recommendation is not authority to execute.**

---

## Current Status

Sentinel has reached its first **usable local CLI milestone**.

The current implementation provides an end-to-end path from operator interaction through session state and vault retrieval to a real locally hosted language model.

The current automated regression baseline is:

```text
107 tests
107 passed
```

The first successful live end-to-end session has also been completed using a locally hosted **Qwen3 1.7B** model through `llama.cpp`.

The system remains an early prototype.

The emphasis at this stage is architectural correctness, explicit boundaries and useful workflow behaviour rather than UI polish, autonomous tooling or model sophistication.

---

## What Works Today

The current Sentinel implementation includes:

- structured engagement state;
- explicit session target, objective and phase;
- operator observations;
- deterministic planning;
- policy evaluation;
- explicit operator approval;
- capability registration and bounded execution;
- provider-independent model access;
- read-only Obsidian vault access;
- bounded vault retrieval;
- context construction and budgeting;
- session-aware reasoning;
- a local `llama.cpp` reasoning provider;
- an interactive command-line interface;
- automated regression tests.

This creates the first complete local workflow:

```text
Operator
   |
   v
Sentinel CLI
   |
   +----> Session State
   |
   +----> Vault Retrieval
   |          |
   |          v
   |     Context Manager
   |          |
   +----------+
   |
   v
Reasoning Service
   |
   v
Model Gateway
   |
   v
Local Model Provider
   |
   v
llama.cpp
   |
   v
Local Qwen3 Model
```

The language model is deliberately not the centre of this architecture.

Sentinel owns the workflow.

The model receives bounded context assembled by Sentinel and returns reasoning within the boundaries Sentinel provides.

---

# Architecture

Sentinel is being developed as a collection of explicit architectural boundaries rather than as a monolithic AI agent.

## Engagement State

Sentinel maintains structured state representing the current engagement.

Current session information includes:

- target;
- objective;
- phase;
- observations;
- findings;
- completed actions;
- evidence.

This state exists independently of the language model.

The model does not own Sentinel's memory or engagement state.

---

## Session Layer

`session.py` provides the operator-facing session abstraction.

The session layer gives the CLI and reasoning pipeline a coherent representation of the current working engagement.

At the current stage, session state exists for the lifetime of the running Sentinel process.

Persistent engagement storage and session resumption are future capabilities.

---

## Obsidian Vault Adapter

The vault adapter provides a controlled, read-only boundary between Sentinel and an Obsidian knowledge base.

Sentinel can:

- discover Markdown notes;
- search vault content;
- retrieve individual notes;
- resolve relevant internal links;
- reject paths outside the configured vault.

The adapter is deliberately read-only.

The reasoning model does not receive unrestricted filesystem access.

---

## Context Manager

The context manager determines what retrieved information should actually be presented to the reasoning system.

It currently supports:

- retrieval from natural-language queries;
- multiple matching notes;
- directly linked note inclusion;
- duplicate prevention;
- unresolved-link tracking;
- bounded note counts;
- hard context-size budgeting.

The context manager exists because retrieving information and presenting information to a model are separate problems.

Sentinel should not simply dump the contents of the knowledge base into the model context window.

---

## Reasoning Service

The reasoning service coordinates:

```text
Operator question
Session state
Vault retrieval
Context construction
Model reasoning
```

It builds the bounded reasoning request supplied to the Model Gateway.

Current engagement information such as the target, objective, phase and observations is included in the reasoning path so that responses can be grounded in both:

1. what Sentinel knows from the knowledge base; and
2. what the operator is currently doing.

---

## Model Gateway

The Model Gateway separates Sentinel from any specific language-model implementation.

Higher-level Sentinel components communicate with the gateway rather than directly with `llama.cpp`, Qwen or another provider.

This allows reasoning providers to change without requiring the rest of Sentinel to be redesigned.

The current real provider is:

```text
Sentinel
   |
Model Gateway
   |
llama.cpp Provider
   |
llama-server
   |
Qwen3 1.7B
```

Future local or external reasoning providers can sit behind the same architectural boundary.

---

## Local Reasoning Provider

`llama_cpp_provider.py` implements Sentinel's first real model provider.

It communicates with a locally running `llama-server` using its OpenAI-compatible HTTP interface.

The provider is intentionally isolated from higher-level workflow logic.

The current proving model is:

```text
ggml-org/Qwen3-1.7B-GGUF:Q4_K_M
```

Qwen3 1.7B is not intended to define Sentinel's long-term reasoning capability.

It currently exists to prove that the architecture can successfully connect:

```text
CLI
Session
Vault
Context Manager
Reasoning Service
Model Gateway
Local Provider
Real Local Model
```

without making the model itself responsible for the wider system.

---

# Command-Line Interface

Sentinel currently provides a lightweight interactive CLI.

Start Sentinel with:

```bash
python3 sentinel_cli.py
```

The interface provides explicit commands for state-changing operations while ordinary text can be used for reasoning questions.

This distinction is intentional.

Explicit commands modify Sentinel state.

Natural-language questions request reasoning.

---

## Current Commands

### Set target

```text
/target <target>
```

Example:

```text
/target 10.10.10.10
```

### Set objective

```text
/objective <objective>
```

Example:

```text
/objective web enumeration
```

### Set phase

```text
/phase <phase>
```

Example:

```text
/phase enumeration
```

### Record observation

```text
/observe <observation>
```

Example:

```text
/observe 80/tcp open http
```

### Display session state

```text
/status
```

### Search the configured vault

```text
/search <query>
```

### Open a vault note

```text
/open <relative path>
```

### Ask a reasoning question

```text
/ask <question>
```

Ordinary text is also interpreted as a reasoning question.

For example:

```text
Given my current session and the knowledge in my vault, what should I focus on next?
```

### Help

```text
/help
```

### Exit

```text
/quit
```

or:

```text
/exit
```

---

# Running the Local Model

Sentinel's current local reasoning provider expects a `llama-server` instance on localhost.

The current proving configuration is:

```bash
llama-server \
  -hf ggml-org/Qwen3-1.7B-GGUF:Q4_K_M \
  -c 8192 \
  --reasoning off \
  --host 127.0.0.1 \
  --port 8080
```

This starts the local model server at:

```text
127.0.0.1:8080
```

The server should remain running in its own terminal while Sentinel is used from another terminal.

For example:

```text
Terminal 1
llama-server

Terminal 2
Sentinel CLI

Terminal 3
Operator tools / lab work
```

The current configuration deliberately binds the model server to localhost rather than exposing it across the network.

---

# Configuring the Vault

Sentinel currently obtains its Obsidian vault location from the configured environment path used by the application.

The vault is treated as an external knowledge source rather than part of the Sentinel software repository.

This separation is intentional.

```text
Sentinel software repository
        |
        | read-only retrieval
        v
Obsidian knowledge vault
```

The current development environment uses the **Project Sentinel Vault** as the initial proving knowledge base.

Broader integration with the operator's wider Obsidian knowledge base is planned as the retrieval architecture develops.

---

# Example Session

A minimal current session looks like:

```text
$ python3 sentinel_cli.py

Project Sentinel
Local workflow and knowledge assistant
Type /help for commands.

Sentinel> /target 10.10.10.10
Target set: 10.10.10.10

Sentinel> /objective web enumeration
Objective set: web enumeration

Sentinel> /phase enumeration
Phase set: enumeration

Sentinel> /observe 80/tcp open http
Observation recorded: 80/tcp open http

Sentinel> /observe The login page appears to be custom-built
Observation recorded: The login page appears to be custom-built

Sentinel> /status

Current session
Target: 10.10.10.10
Objective: web enumeration
Phase: enumeration

Observations:
- 80/tcp open http
- The login page appears to be custom-built

Findings:
- None

Completed actions:
- None

Evidence:
- None
```

A natural-language question can then use both the active session and retrieved vault context:

```text
Sentinel> Given my current session and the knowledge in my vault, what should I focus on next?
```

Sentinel retrieves bounded relevant knowledge, combines it with the current session and sends the resulting context through the Model Gateway to the configured reasoning provider.

---

# Context Is Bounded

One of the first live integration tests exposed an important architectural requirement.

Initial end-to-end requests exceeded the model's available context window because retrieved vault notes could collectively produce requests larger than the configured model context.

The solution was not simply to increase the model context window.

Sentinel now enforces a context budget before information reaches the reasoning provider.

This establishes an important principle:

> **The Context Manager decides what the model needs to see.**

The model's context window is a limited computational resource, not a storage mechanism.

As Sentinel develops, context selection should become increasingly intelligent while remaining bounded and inspectable.

---

# Control Model

Sentinel separates reasoning from execution.

A reasoning system may recommend an action, but that recommendation does not itself authorize execution.

The intended control path is:

```text
Reasoning
   |
   v
Proposed Action
   |
   v
Policy Evaluation
   |
   v
Operator Approval
   |
   v
Capability Resolution
   |
   v
Execution
```

For an executable action to proceed, it must satisfy the relevant policy requirements, receive operator approval where required and resolve to an explicitly registered capability.

This principle predates the local LLM integration and remains authoritative as Sentinel's reasoning capability grows.

---

# Human-Led, AI-Assisted

Sentinel is not intended to replace the operator's understanding of penetration testing.

The system should instead help the operator maintain:

- situational awareness;
- engagement context;
- methodology;
- observations;
- evidence;
- hypotheses;
- reasoning;
- documentation;
- workflow continuity.

The operator should remain responsible for understanding the target, interpreting evidence and making decisions.

Sentinel exists to reduce the surrounding cognitive and organisational overhead.

---

# Current Limitations

The current implementation is intentionally limited.

Notable limitations include:

- session state is not yet persisted between CLI runs;
- the current local model is small and primarily proves the provider architecture;
- retrieval is still relatively simple;
- context relevance is not yet deeply ranked or weighted;
- the current proving vault is narrower than the intended long-term knowledge base;
- observations are manually entered;
- voice capture is not yet implemented;
- engagement write-up generation is not yet implemented;
- no graphical interface is required at this stage;
- autonomous penetration-testing behaviour is not a project objective.

These limitations are expected at the current stage.

The priority is to establish a useful and trustworthy foundation before adding higher-level capabilities.

---

# Near-Term Direction

The next stages of Sentinel development will build on the working CLI rather than replacing it.

Likely areas of development include:

- stronger retrieval relevance;
- richer engagement state;
- engagement persistence and resumption;
- methodology and SOP retrieval;
- findings and evidence workflows;
- write-up and reporting templates;
- improved context selection;
- broader Obsidian knowledge integration;
- capture of operator reasoning during an engagement;
- eventual voice input where it improves workflow.

Voice interaction is intended primarily as a capture mechanism rather than a cosmetic interface feature.

A future operator should be able to verbalise observations and reasoning during technical work so that Sentinel can preserve useful engagement context without requiring retrospective reconstruction.

---

# Testing

Run the complete test suite with:

```bash
python3 -m unittest discover -v
```

Current baseline:

```text
Ran 107 tests
OK
```

The regression suite covers the existing architectural boundaries including:

- engagement state;
- observation parsing;
- planning;
- policy;
- approval;
- capability execution;
- Model Gateway behaviour;
- vault access;
- context management;
- reasoning coordination;
- session behaviour;
- CLI behaviour;
- `llama.cpp` provider behaviour.

Maintaining a green regression baseline is a requirement as Sentinel develops.

---

# Development Philosophy

Sentinel is being built incrementally.

Each development step should:

1. introduce one understandable capability;
2. preserve existing architectural boundaries;
3. include automated tests;
4. be exercised manually where appropriate;
5. be documented alongside the implementation;
6. leave the repository in a coherent working state.

The project deliberately favours a small working system over a large speculative architecture.

Capabilities should be added because they improve the operator's real workflow, not simply because they are technically possible.

---

# Project Sentinel

This repository contains the **Sentinel application**.

The wider **Project Sentinel** documentation is maintained separately in an Obsidian vault and records:

- project vision;
- requirements;
- architecture;
- Architectural Decision Records;
- roadmap;
- development history;
- test records;
- hardware planning;
- security boundaries;
- Standard Operating Procedures;
- future capability design.

The software and documentation repositories remain separate intentionally.

The software repository records **what Sentinel does**.

The Project Sentinel Vault records **why Sentinel is being built that way**.

---

## Current Milestone

**Foundation 0.3 — First Usable Local Sentinel CLI**

Current verified path:

```text
Operator
   |
   v
CLI
   |
   +---- Session State
   |
   +---- Obsidian Retrieval
              |
              v
        Context Manager
              |
              v
       Reasoning Service
              |
              v
         Model Gateway
              |
              v
      llama.cpp Provider
              |
              v
       Local Qwen3 Model
```

**Regression baseline: 107 / 107 tests passing.**

The foundation is now capable of supporting a real operator session.

The next objective is to make that session progressively more useful.