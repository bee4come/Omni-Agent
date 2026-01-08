# OpenSpec Quick Reference

## Slash Commands (Claude Code)

| Command | Description |
|---------|-------------|
| `/openspec:proposal <name>` | Create a new change proposal |
| `/openspec:apply <name>` | Implement an approved change |
| `/openspec:archive <name>` | Archive a completed change |

## CLI Commands

| Command | Description |
|---------|-------------|
| `openspec init` | Initialize OpenSpec in project |
| `openspec list` | List active changes |
| `openspec list --specs` | List all specs |
| `openspec view` | Interactive dashboard |
| `openspec show <name>` | Show change/spec details |
| `openspec validate <name>` | Validate formatting |
| `openspec validate --all` | Validate all specs and changes |
| `openspec archive <name> --yes` | Archive without prompts |
| `openspec update` | Refresh AI instructions |

## Workflow Checklist

### Creating a Change

1. [ ] Create proposal: `/openspec:proposal <feature-name>`
2. [ ] Review generated `proposal.md`
3. [ ] Review and refine `tasks.md`
4. [ ] Review spec deltas in `specs/` folder
5. [ ] Validate: `openspec validate <name>`

### Implementing a Change

1. [ ] Review approved specs: `openspec show <name>`
2. [ ] Start implementation: `/openspec:apply <name>`
3. [ ] Work through tasks in order
4. [ ] Mark tasks complete in `tasks.md`
5. [ ] Test implementation

### Completing a Change

1. [ ] Verify all tasks marked complete
2. [ ] Run final validation: `openspec validate <name>`
3. [ ] Archive change: `/openspec:archive <name>`
4. [ ] Verify specs updated: `openspec list --specs`

## Spec Keywords

| Keyword | Usage |
|---------|-------|
| `SHALL` | Required behavior (strong) |
| `MUST` | Required behavior (strongest) |
| `SHOULD` | Recommended behavior |
| `MAY` | Optional behavior |

## Scenario Keywords

| Keyword | Purpose |
|---------|---------|
| `GIVEN` | Precondition/context |
| `WHEN` | Action or trigger |
| `THEN` | Expected outcome |
| `AND` | Additional condition |

## File Naming Conventions

- Change folders: `kebab-case` (e.g., `add-user-auth`)
- Spec folders: `kebab-case` matching feature name
- All markdown files: lowercase with `.md` extension
