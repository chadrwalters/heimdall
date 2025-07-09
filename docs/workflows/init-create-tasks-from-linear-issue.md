# Linear Issue to TaskMaster Workflow

Execute the following steps to convert a Linear issue into TaskMaster tasks:

## 1. Fetch Linear Issue Details
Retrieve the Linear issue information:
- Use the provided Linear issue number/ID
- Run `mcp__linear__get_issue` with the issue ID to get full details
- Review the issue title, description, acceptance criteria, and any attachments

## 2. Create PRD from Template
Generate Product Requirements Document:
- Create `.taskmaster/docs/prd.txt` using `.taskmaster/templates/example_prd.txt` as the template
- Fill in each section based on the Linear issue details:
  - **Overview**: Translate issue description into clear problem statement
  - **Core Features**: Break down requirements into specific features
  - **User Experience**: Define user flows from issue context
  - **Technical Architecture**: Outline system components and data models
  - **Development Roadmap**: Create logical phases prioritizing MVP
  - **Logical Dependency Chain**: Define build order
  - **Risks and Mitigations**: Identify technical challenges
  - **Appendix**: Include any technical specifications from the issue

## 3. Generate Initial TaskMaster Tasks
Parse the PRD to automatically create tasks:
- Use `mcp_taskmaster-ai_parse_prd` with the PRD file path to automatically generate tasks
- **IMPORTANT**: The parse-prd operation can take up to 2 minutes to complete
- **Wait Protocol**:
  1. Execute the parse-prd command
  2. Wait 2 minutes (use `vibe-tools wait 120`)
  3. Check if tasks were generated successfully
  4. If not complete, wait another 2 minutes (use `vibe-tools wait 120`)
  5. If still not complete after 4 minutes total, ask the user for help
- The command will automatically:
  - Extract features from the PRD
  - Create appropriately scoped tasks
  - Assign initial priorities based on roadmap order
  - Include technical details from the PRD

## 4. Analyze Task Complexity
For each created task, assess complexity:
- Review task scope and technical requirements
- Assign complexity score 1-10 (1=trivial, 10=extremely complex)
- Consider factors:
  - Technical difficulty
  - Number of components involved
  - Dependencies on other systems
  - Amount of new code required
  - Integration complexity

## 5. Expand Complex Tasks into Subtasks
For any task with complexity ≥ 5:
- Use `task-master create-subtask --parent-id=<task-id>` to break it down
- Create focused subtasks that:
  - Are complexity ≤ 4 each
  - Have clear, specific scope
  - Can be completed independently
  - Follow logical development order
- Reassess subtask complexity and expand further if needed

## 6. Review All Tasks and Subtasks
Validate the complete task breakdown:
- Review all created tasks and subtasks for completeness
- Verify all Linear issue acceptance criteria are covered
- Confirm complexity scores are appropriate (all ≤ 4)
- Check logical dependency order makes sense
- Ensure tasks are properly scoped and actionable

## 7. Summary Report
Provide project initialization summary:
- **Linear Issue**: [Issue number and title]
- **PRD Created**: `.taskmaster/docs/prd.txt` with scope description
- **Tasks Generated**: [Number] initial tasks created via automated PRD parsing
- **Parse Time**: Total time taken for PRD parsing (should be 2-4 minutes)
- **Complex Tasks Expanded**: [Number] tasks broken into subtasks
- **Total Task Count**: [Number] tasks ready for development
- **Task Review**: Confirmed all tasks are properly scoped and cover acceptance criteria
- **First Task Available**: TaskMaster #[task-id] - [task title] (ready to start when user chooses)

## Important Notes
- **Focus**: This workflow only creates PRD and tasks - no system context needed yet
- **Parse-PRD Timing**: The automated task generation can take 2-4 minutes - be patient and follow the wait protocol
- **Complexity Analysis**: Critical step to ensure tasks are appropriately sized
- **Subtask Expansion**: Any task ≥ 5 complexity must be broken down
- **Task Sizing**: Final tasks should be complexity ≤ 4 for manageable development
- **PRD Quality**: Should guide automated task creation but doesn't need full system understanding
- **Linear Mapping**: Ensure all acceptance criteria are covered in task breakdown
- **Wait Protocol**: Always use `vibe-tools wait 120` for timing delays rather than assuming immediate completion

## Template Variables
When using this workflow, replace:
- `<linear-issue-id>`: The specific Linear issue number provided
- `<task-id>`: The generated TaskMaster task ID
- `[descriptions]`: Actual content based on Linear issue details

## Follow-up Workflows
After completing this initialization:
- Use `docs/workflows/init-complete-next-task.md` to execute the first task
- Use `docs/workflows/cleanup-docs-justfile.md` to ensure documentation stays synchronized
