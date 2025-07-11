# Linear Ticket Enhancement Workflow

Execute the following steps to analyze and enhance a Linear ticket with AI-powered investigation:

## 1. Initial Setup
Retrieve the Linear issue and begin systematic analysis:
- Use the provided Linear issue number/ID
- Run `mcp__linear__get_issue` with the issue ID to get full details
- Review the issue title, description, acceptance criteria, and any attachments
- Start planning tool with enhancement goal: `mcp__zen__planner` to systematically investigate and improve the ticket

## 2. Interactive Investigation (Planning Tool)
Use the planning tool to build understanding incrementally:

### Step 1: Analyze Ticket Quality
- Assess current ticket clarity, completeness, and quality
- **Evaluate title clarity**: Check if title clearly describes the problem/feature
- Identify gaps in problem statement, acceptance criteria, or technical context
- **Interactive Element**: Ask clarifying questions if ticket is vague or ambiguous
- Document quality assessment and improvement opportunities

### Step 2: Investigate Codebase Context
- Search and analyze relevant code sections mentioned or implied by the ticket
- Understand technical feasibility and current implementation
- **For Web Applications**: Use Playwright to navigate to dev environment and reproduce the issue firsthand
- **Interactive Element**: Ask about inconsistencies between ticket and code reality
- Document technical context and architectural considerations

### Step 3: Research User Intent and Requirements
- Analyze the underlying user need or business requirement
- Clarify the problem being solved and expected outcome
- **Interactive Element**: Ask for validation of user intent when unclear
- Document refined understanding of requirements

### Step 4: Assess Feasibility and Approach Options
- Evaluate technical complexity and implementation approaches
- Consider scope, dependencies, and potential risks
- **Interactive Element**: Ask about scope preferences or approach trade-offs
- Document feasibility assessment and recommendations

### Step 5: Structure Enhancement Plan
- Plan enhanced ticket content structure
- Organize improved description, acceptance criteria, and technical notes
- Consider scope suggestions or categorization improvements
- Document complete enhancement strategy

## 3. Confirmation Phase
Present proposed changes for approval before implementation:

### Confirmation Format
```
I'm going to enhance Linear ticket #[ID] with:

Enhanced Title: [If needed - clearer, more descriptive title]
Enhanced Description: [Clearer problem statement with context]
Improved Acceptance Criteria: [Specific, testable criteria]
Technical Context: [Feasibility notes, architectural considerations]
Scope Suggestions: [Any recommended scope changes or clarifications]
Categorization: [Bug/Feature/Improvement with reasoning]

Annotation: "🤖 AI Enhanced [date]: [summary of key improvements made]"

Does this look right? Any changes needed?
```

### Interactive Refinement
- Present all proposed changes at once
- Wait for approval or requested adjustments
- **For minor changes**: Adjust specific parts using existing investigation context
- **For major changes**: Re-run relevant planning steps if fundamental misunderstanding is identified
- Iterate until explicit approval ("looks good", "go ahead", etc.)

## 4. Implementation
Update the Linear ticket with approved enhancements:
- **Update Linear ticket title** if needed for clarity using `mcp__linear__update_issue`
- Update Linear ticket description with enhanced content using `mcp__linear__update_issue`
- Append AI enhancement annotation to description
- Confirm successful update and provide summary

## 5. Summary Report
Provide enhancement completion summary:
- **Linear Issue**: [Issue number and title]
- **Enhancements Made**: [Brief summary of key improvements]
- **Investigation Scope**: [Areas of codebase analyzed]
- **Clarifications Obtained**: [Key questions resolved]
- **Technical Context Added**: [Feasibility and architectural notes]
- **Ticket Quality**: Improved from [assessment] to [assessment]

## Important Notes
- **Interactive Approach**: Ask clarifying questions throughout investigation as needed
- **Investigation Depth**: Use planning tool for systematic analysis and understanding building
- **Live Investigation**: For web applications, use Playwright to reproduce issues in dev environment firsthand
- **Confirmation Required**: Never update Linear ticket without explicit approval
- **Title Enhancement**: Always evaluate and enhance title clarity alongside description improvements
- **Scope Flexibility**: Feel free to suggest scope changes or improvements beyond original ticket
- **Context Preservation**: Maintain investigation context during iterative refinements
- **Quality Focus**: Prioritize clarity, specificity, and actionability in enhancements

## Interactive Question Examples
- "The ticket mentions X, but I see Y in the code - which is correct?"
- "Should this be treated as a bug or feature enhancement?"
- "I need clarification on the expected user experience for Z"
- "The scope seems quite large - should we consider breaking this into smaller pieces?"
- "I found a potential edge case - should we include this in the requirements?"

## Enhancement Annotation Format
```
---
🤖 AI Enhanced: [YYYY-MM-DD]
Improvements: [Enhanced acceptance criteria, added technical context, clarified scope, etc.]
Investigation: [Analyzed codebase in X modules, validated feasibility, clarified user intent]
---
```

## Template Variables
When using this workflow, replace:
- `[ID]`: The specific Linear issue number provided
- `[date]`: Current date in YYYY-MM-DD format
- `[assessments]`: Actual quality assessments based on investigation
- `[summaries]`: Actual content based on ticket analysis and enhancement

## Follow-up Workflows
After completing ticket enhancement:
- Use `docs/workflows/init-create-tasks-from-linear-issue.md` to convert enhanced ticket to TaskMaster tasks
- Enhanced ticket is now ready for implementation planning or assignment
