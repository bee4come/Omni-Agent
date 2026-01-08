---
name: openspec
description: Spec-driven development workflow for AI coding assistants. Use when creating proposals, managing specs, implementing changes, or archiving completed features. Triggers on keywords like proposal, spec, change, plan, architecture.
---

# OpenSpec Skill

OpenSpec aligns humans and AI coding assistants with spec-driven development so you agree on what to build before any code is written.

## Core Workflow

```
Draft Proposal -> Review & Align -> Implement Tasks -> Archive & Update Specs
```

1. **Draft a change proposal** - Capture the spec updates you want
2. **Review with AI** - Iterate until everyone agrees
3. **Implement tasks** - Reference the agreed specs
4. **Archive** - Merge approved updates back into source-of-truth specs

## Directory Structure

```
openspec/
├── specs/           # Source of truth (current specs)
│   └── <feature>/
│       └── spec.md
├── changes/         # Proposed updates (active work)
│   └── <change-name>/
│       ├── proposal.md    # Why and what changes
│       ├── tasks.md       # Implementation checklist
│       ├── design.md      # Technical decisions (optional)
│       └── specs/         # Delta showing additions/modifications
└── archive/         # Completed changes
```

## Commands

### Creating a Proposal

When user asks to create a proposal or plan a feature:

```
/openspec:proposal <feature-name>
```

Or naturally: "Create an OpenSpec change proposal for adding [feature]"

This creates:
- `openspec/changes/<feature-name>/proposal.md`
- `openspec/changes/<feature-name>/tasks.md`
- `openspec/changes/<feature-name>/specs/` (delta specs)

### Applying/Implementing a Change

When user wants to implement an approved proposal:

```
/openspec:apply <change-name>
```

Or naturally: "Let's implement the [change-name] change"

Work through tasks in `tasks.md`, marking them complete as you go.

### Archiving a Completed Change

When all tasks are done:

```
/openspec:archive <change-name>
```

Or use CLI: `openspec archive <change-name> --yes`

This merges spec deltas back into source specs and moves the change to archive.

## CLI Commands Reference

```bash
openspec init                    # Initialize OpenSpec in project
openspec list                    # View active change folders
openspec list --specs            # View all specs
openspec view                    # Interactive dashboard
openspec show <change>           # Display change details
openspec validate <change>       # Check spec formatting
openspec archive <change> --yes  # Archive completed change
openspec update                  # Refresh AI instructions
```

## Spec Format

### Source Spec (`openspec/specs/<feature>/spec.md`)

```markdown
# Feature Specification

## Purpose
Brief description of the feature.

## Requirements
### Requirement: Requirement Name
The system SHALL/MUST [behavior].

#### Scenario: Scenario Name
- GIVEN [precondition]
- WHEN [action]
- THEN [expected outcome]
```

### Delta Spec (`openspec/changes/<name>/specs/<feature>/spec.md`)

```markdown
# Delta for Feature

## ADDED Requirements
### Requirement: New Capability
The system MUST [new behavior].

#### Scenario: New scenario
- WHEN [action]
- THEN [outcome]

## MODIFIED Requirements
### Requirement: Changed Behavior
The system SHALL [updated behavior].

## REMOVED Requirements
### Requirement: Deprecated Feature
```

## Tasks Format (`tasks.md`)

```markdown
## 1. Phase Name
- [ ] 1.1 First task
- [ ] 1.2 Second task

## 2. Next Phase
- [ ] 2.1 Task description
- [x] 2.2 Completed task
```

## When to Use OpenSpec

Use OpenSpec when the request:
- Mentions planning or proposals
- Introduces new capabilities or features
- Involves breaking changes or architecture shifts
- Requires big performance/security work
- Sounds ambiguous and needs spec clarification before coding

## Best Practices

1. **Always draft specs before coding** - Agree on requirements first
2. **Keep proposals focused** - One feature per change folder
3. **Use clear requirement language** - SHALL/MUST for requirements
4. **Include scenarios** - Every requirement needs test scenarios
5. **Archive promptly** - Keep `changes/` clean by archiving completed work
6. **Validate often** - Run `openspec validate` to catch formatting issues
