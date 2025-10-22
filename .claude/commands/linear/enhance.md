---
name: linear:enhance
description: AI-enhance Linear ticket descriptions with context and acceptance criteria
---

# Linear Enhance Command

Use AI to enhance Linear ticket descriptions with rich context.

## What This Does

Takes a basic Linear ticket and adds:
- Detailed description
- Acceptance criteria
- Technical considerations
- Related tickets
- Implementation notes

## Workflow

### Step 1: Get Ticket ID

```
/linear:enhance ENG-123
```

### Step 2: Fetch Current Ticket

```bash
# Uses Linear API
just linear test  # Verify connection first
```

Read current ticket:
- Title
- Description (if any)
- Status
- Assignee
- Labels/Projects

### Step 3: Analyze Context

Search codebase for relevant:
- Related code files
- Similar past tickets
- Technical constraints
- Implementation patterns

### Step 4: Generate Enhanced Description

Template:

```markdown
## Overview
[Clear summary of what needs to be done]

## Context
[Why this is needed, background information]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Notes
- Implementation approach
- Files likely to change
- Potential challenges
- Testing requirements

## Related
- ENG-XXX: Related ticket
- PR #123: Similar implementation
```

### Step 5: Preview and Confirm

Show enhanced description.
Ask: "Update ticket with this description?"

### Step 6: Update Ticket

```bash
# Use Linear API to update
# POST to Linear GraphQL endpoint
```

Confirm success.

## Use Cases

### New Feature Tickets

Add:
- User stories
- UI/UX considerations
- API design
- Data model changes

### Bug Tickets

Add:
- Reproduction steps
- Expected vs actual behavior
- Root cause analysis
- Fix approach

### Refactoring Tickets

Add:
- Current state
- Desired state
- Migration strategy
- Risk assessment

## Usage

```
/linear:enhance <ticket-id>
```

Example:
```
/linear:enhance ENG-456
```

## Requires

- LINEAR_API_KEY environment variable
- justfile linear commands
- Access to Linear API
