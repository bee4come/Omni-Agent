# OpenSpec Templates

## Proposal Template (`proposal.md`)

```markdown
## Why

<!-- Explain the motivation for this change -->

## What Changes

<!-- Describe what will change -->

## Impact

<!-- List affected areas -->
```

## Tasks Template (`tasks.md`)

```markdown
## 1. <!-- Task Group Name -->

- [ ] 1.1 <!-- Task description -->
- [ ] 1.2 <!-- Task description -->

## 2. <!-- Task Group Name -->

- [ ] 2.1 <!-- Task description -->
- [ ] 2.2 <!-- Task description -->
```

## Spec Delta Template (`specs/<feature>/spec.md`)

```markdown
## ADDED Requirements

### Requirement: <!-- requirement name -->
<!-- requirement text using SHALL/MUST -->

#### Scenario: <!-- scenario name -->
- **WHEN** <!-- condition -->
- **THEN** <!-- expected outcome -->
```

## Full Spec Template (for source specs)

```markdown
# <Feature> Specification

## Purpose

<!-- Brief description of what this feature does -->

## Requirements

### Requirement: <Requirement Name>
The system SHALL/MUST <behavior description>.

#### Scenario: <Scenario Name>
- **GIVEN** <precondition>
- **WHEN** <action or event>
- **THEN** <expected outcome>

### Requirement: <Another Requirement>
The system SHALL <another behavior>.

#### Scenario: <Scenario Name>
- **WHEN** <action>
- **THEN** <outcome>
```

## Design Template (optional, `design.md`)

```markdown
# Design: <Change Name>

## Overview

<!-- High-level technical approach -->

## Architecture Decisions

### Decision 1: <Topic>
- **Context**: <!-- Why this decision is needed -->
- **Decision**: <!-- What was decided -->
- **Consequences**: <!-- Trade-offs and implications -->

## Implementation Notes

<!-- Specific implementation details, diagrams, or references -->
```

## Delta Sections Reference

Use these section headers in delta specs:

- `## ADDED Requirements` - New capabilities being added
- `## MODIFIED Requirements` - Changes to existing requirements (include full updated text)
- `## REMOVED Requirements` - Deprecated or deleted requirements
