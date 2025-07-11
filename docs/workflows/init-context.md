# Project Context Initialization

**Purpose**: Initialize Claude with current project state and context.

## Execution Steps

1. **Acknowledge & Greet**: State the current date/time and greet the user.

2. **Review System Documentation**:
   - Review key files in `docs/` to understand the current system architecture
   - Focus on `docs/product/product-overview.md` (current system) and `docs/INDEX.md` for navigation

3. **Check Current Work Context**:
   - Look for PRD at `.taskmaster/docs/prd.txt` - if it exists, this is what we're currently building
   - If no PRD exists, note that we're in maintenance/exploration mode

4. **Get Taskmaster Status**:
   - Use `get_tasks` MCP tool with `withSubtasks: true` to get current task list
   - Use `next_task` MCP tool to identify the next recommended task
   - For any unclear tasks, use `get_task` MCP tool with specific IDs

5. **Summarize Current State**:
   - Brief overview of project progress (completed vs pending tasks)
   - Identify the next recommended task(s) with ID, title, and description
   - Note any active development areas or focus points

6. **Incorporate Project Personality**:
   - Reference `.cursor/rules/personality.mdc` for communication style
   - Be collaborative, direct, and constructive per project guidelines

7. **Offer Assistance**:
   - Clearly state you're now equipped with project context
   - Ask the user what they need help with
   - Suggest specific areas where you can assist based on current project state

## Expected Outcome

You should have a clear understanding of:
- Current system architecture and capabilities
- Active work (PRD-driven development vs maintenance)
- Task progress and next steps
- How to best assist the user given the current project state
