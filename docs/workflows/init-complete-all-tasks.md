# Task Execution Workflow

Execute the following steps to work through project tasks systematically:

## 1. Initialize Task Context
First, read the project requirements and identify the next task:
- Read `.taskmaster/docs/prd.txt` to understand the environment variable consistency project
- Run `task-master next` to get the next available task
- Run `task-master show <task-id>` to view detailed task information
- **MANDATORY**: Update TaskMaster status: `task-master set-status --id=<task-id> --status=in_progress`

## 2. Learn Documentation Navigation
Read the documentation index to understand how to find information:
- Read `docs/INDEX.md` completely to understand documentation structure
- Pay attention to:
  - Lines 24-34: Quick Start Paths by role
  - Lines 36-52: Documentation Structure overview
  - Lines 54-70: Product Documentation section
  - Lines 90-128: Environment Setup section
  - Lines 130-156: Backend Development section
  - Lines 190-213: Operational Workflows section

## 3. Read Task-Specific Documentation
Based on your task from step 1 and using the navigation from step 2:
- For environment/config tasks → Read `docs/setup/environment-configuration.md` and `docs/gotchas/variable-name-mismatches.md`
- For backend implementation → Read `docs/backend/api-development.md` and `docs/backend/architecture/backend-container-architecture.md`
- For testing requirements → Read `docs/workflows/testing-guide.md` and `docs/workflows/testing-strategy.md`
- For deployment tasks → Read `docs/workflows/deployment-guide.md` and `docs/workflows/aws-deployment-guide.md`
- Always check the relevant README.md in each directory for additional context

## 4. Implement the Task
For each task or subtask:
- Create a TodoWrite list to track implementation steps
- Implement the required changes based on documentation
- Follow existing code patterns and conventions
- Run `just lint` after changes to validate environment variables

## 5. Verify Implementation (MANDATORY)
**CRITICAL**: You cannot mark a task as "done" without verification. Choose appropriate verification method:

### Automated Testing (Preferred)
- `just test_unit` for backend unit tests
- `just test_integration` for integration tests
- `just test_system` for system tests
- Create new tests if needed following patterns in `backend/tests/`

### Manual Verification (If No Tests Exist)
- Document specific manual testing steps performed
- Test the implementation against expected behavior
- Verify no regressions or breaking changes
- Include verification evidence in your response

### Verification Evidence Required
- Document test results or manual verification steps
- Include evidence: "Verified by: [test command] - Results: [all tests pass/manual steps completed]"

## 6. Complete Current Work Item
**ONLY after verification passes completely:**
- If working on a subtask: `task-master set-status --id=<subtask-id> --status=done`
- If completing a full task, proceed to step 7 for review
- **Required Response Format for Each Completion**:
  ```
  TaskMaster #<task-id> updated to done. Implemented [brief description].
  Verified by: [specific verification method used].
  Results: [test results or manual verification evidence].
  ```

## 7. Review Full Task Completion (Only for Full Tasks)
When all subtasks are complete:
- Use `mcp__zen__codereview` with parameters:
  - `step`: "Review implementation of <task description>"
  - `step_number`: 1
  - `total_steps`: 3
  - `next_step_required`: true
  - `findings`: "Initial review of task implementation"
  - `model`: "anthropic/claude-opus-4"
  - `relevant_files`: [list of changed files]

## 8. Validate Completion (Only for Full Tasks)
After code review passes:
- Use `mcp__zen__consensus` with parameters:
  - `step`: "Validate task '<task-id>' is complete"
  - `step_number`: 1
  - `total_steps`: 2
  - `next_step_required`: true
  - `findings`: "Task implementation reviewed and tested"
  - `model`: "anthropic/claude-opus-4"
  - `models`: [{"model": "google/gemini-2.5-pro", "stance": "neutral"}]

## 9. Mark Task Complete and Continue
**ONLY after full verification and validation:**
- Set task complete: `task-master set-status --id=<task-id> --status=done`
- **Required Response Format**:
  ```
  TaskMaster #<task-id> updated to done. Full task completed after code review and consensus validation.
  Verified by: [test suite + code review + consensus validation].
  Results: [All verifications passed, task fully validated].
  ```
- Get next task: `task-master next`
- Update TaskMaster to "in_progress" for next task: `task-master set-status --id=<new-task-id> --status=in_progress`
- Return to step 1 with the new task

## Important Notes
- **VERIFICATION IS MANDATORY**: Never claim "done" without testing/verification
- Always use `task-master` commands (not `tm`)
- **TaskMaster Status**: Update to "in_progress" at start, "done" only after verification
- Run `just lint` frequently to catch environment variable issues early
- Use TodoWrite to track progress within each task
- **Required Response Format**: Include verification evidence for every completion
- Only run code review and consensus for full task completion, not subtasks
- Follow existing patterns in the codebase rather than creating new approaches
- Run `cleanup-docs-justfile.md` periodically to keep documentation synchronized with code

## Verification Requirements Summary
Following CLAUDE.md verification standards:
- "Done" = verified working, NOT "looks correct"
- Run tests OR document manual verification steps
- Include verification evidence: "Verified by: [method] - Results: [evidence]"
- Update TaskMaster status only after verification passes
- For full tasks: Additional code review and consensus validation required
