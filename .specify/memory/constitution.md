# Family School Dashboard Constitution

## Core Principles

### I. Local Only

The app MUST bind to the local machine only. It MUST NOT send telemetry.
This project MUST NOT add a cloud deployment.

Rationale: The records are a family's school life. The machine that holds
them is the privacy boundary.

### II. Children's Data Stays Out of Git

School records, databases that contain real children, and any future access
tokens MUST NOT be committed. The database file and `.env` MUST be ignored.
Checked-in sample data MUST use fictional students.

### III. Two Child Profiles Are First-Class

The household has two children. Every list MUST filter to one child or to
both. An item that applies to both children is stored once and shown when
the parent chooses Both.

### IV. This Slice Does Not Call School Systems

This feature MUST NOT call Canvas, email, or TalkingPoints. Later connectors
are separate features and MUST be read-only toward those systems. Each record
carries a source label so a later connector can set it. Manual entry is the
default source.

### V. Smallest App That Meets the Spec

The implementation MUST be the smallest local app that satisfies the current
spec. Automated tests MUST cover child filtering and the upcoming-date window.
Specs describe behavior. Stack choices belong in the plan, not the spec.

## Privacy and Scope Boundaries

One parent uses the app on one computer. This feature has no login.
Accounts, notifications, AI summaries, and live connectors are out of scope
until a later spec.

## Development Workflow

Work follows Spec Kit one feature at a time: constitution, specify, clarify,
plan, checklist, tasks, analyze, implement, then converge. A plan that
contradicts this constitution does not proceed until the contradiction is
resolved.

## Governance

This constitution supersedes ad-hoc practice for this project. An amendment
updates this file, bumps the version, and is reviewed before the next feature
spec. MAJOR removes or redefines a principle. MINOR adds a principle or
expands a rule. PATCH is wording only. Reviews of this feature check local
binding, ignored data and secrets, child scoping, and the absence of live
school-system calls.

**Version**: 1.0.0 | **Ratified**: 2026-11-14 | **Last Amended**: 2026-11-14
