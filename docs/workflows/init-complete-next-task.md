# Single Task Execution Workflow

Execute the following steps to complete the next available task or subtask:

## 1. Initialize Task Context
First, read the project requirements and identify the next task:
- Read `.taskmaster/docs/prd.txt` to understand the environment variable consistency project
- Run `task-master next` to get the next available task or subtask
- Run `task-master show <task-id>` to view detailed task information
- **MANDATORY**: Update TaskMaster status: `task-master set-status --id=<task-id> --status=in_progress`
- Create a TodoWrite list with the task ID and description

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
For the current task or subtask:
- Update TodoWrite list with implementation steps
- Implement the required changes based on documentation
- Follow existing code patterns and conventions
- Run `just lint` after changes to validate environment variables
- Mark each TodoWrite item as complete as you finish it

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
- Update TodoWrite with verification method used
- Document test results or manual verification steps
- Include evidence: "Verified by: [test command] - Results: [all tests pass/manual steps completed]"

## 6. Complete Current Work Item
**ONLY after verification passes completely:**
- Run `task-master set-status --id=<task-id> --status=done`
- Show completion status: `task-master list --status=done | tail -5`
- **Required Response Format**:
  ```
  TaskMaster #<task-id> updated to done. Implemented [brief description].
  Verified by: [specific verification method used].
  Results: [test results or manual verification evidence].
  ```

## 7. Request User Guidance
Report task completion and ask for next steps:
- Provide a brief summary of what was completed
- List any notable changes or decisions made
- Ask: "I've completed task <task-id>. Would you like me to:
  1. Continue with the next task automatically
  2. Wait for you to review the changes
  3. Run additional validation (code review/consensus)
  4. Something else?"

## Important Notes
- This workflow completes ONLY ONE task or subtask
- **VERIFICATION IS MANDATORY**: Never claim "done" without testing/verification
- Always use `task-master` commands (not `tm`)
- **TaskMaster Status**: Update to "in_progress" at start, "done" only after verification
- Run `just lint` frequently to catch environment variable issues early
- Use TodoWrite to track progress within the task
- **Required Response Format**: Include verification evidence in completion message
- Stop after step 7 and wait for user instructions
- Do NOT automatically continue to the next task
- Consider running `cleanup-docs-justfile.md` after significant features to update documentation

## Verification Requirements Summary
Following CLAUDE.md verification standards:
- "Done" = verified working, NOT "looks correct"
- Run tests OR document manual verification steps
- Include verification evidence: "Verified by: [method] - Results: [evidence]"
- Update TaskMaster status only after verification passes
