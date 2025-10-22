# Request Code Review Command

Generate comprehensive PR review requests with detailed analysis using the specialized pr-review-expert agent for consistent, high-quality GitHub comments that guide Claude reviewers effectively.

## Usage
```
/pr:request-review <PR_NUMBER>
/pr:request-review  # Uses current PR if on a branch
```

Triggering review bots (comment on the PR):
- `@claude review` – comprehensive review (all categories: docs, correctness, tests, performance)
- `@claude review all` – explicitly review all categories (same as above)
- `@claude review docs` – targeted documentation review only
- `@claude review correctness` – logic/API/security focus only
- `@claude review tests` – review test coverage and quality
- `@claude review performance` – flag performance issues
- `@codex review` – Codex summary + inline comments

## Implementation

### Step 1: Use pr-review-expert agent
```
Launch Task tool with:
- subagent_type: "pr-review-expert"
- description: "Analyze PR and create comprehensive review request comment"
- prompt: Include PR number and request for complete PR analysis and review request generation

CRITICAL: The agent MUST:
1. Validate PR exists and is reviewable using `gh pr view <number>`
2. Analyze PR comprehensively using GitHub CLI and huginn
3. Generate structured review request comment with @claude (primary AI reviewer) and @codex (additional AI code review perspective)
4. Post comment safely using `gh pr comment <number> --body-file=<path>`
```

## Agent Capabilities

The pr-review-expert agent will:
1. **Pre-Analysis Validation**:
   - Verify PR exists using `gh pr view <number>` or detect current PR
   - Confirm PR is in open state (not draft or closed)
   - Check that recent commits exist for meaningful analysis

2. **Comprehensive PR Analysis**:
   - Execute `gh pr view <number>` for PR summary and metadata
   - Execute `gh pr diff <number>` for detailed changes
   - Execute `huginn pr review <number>` for AI-powered analysis (if complex)
   - Analyze changed files and their impact

3. **Smart Review Focus Identification**:
   - Analyze commits for key changes
   - Identify review areas based on changed files:
     - **Python/src changes** → Logic, API design, data processing
     - **Tests** → Coverage, assertions, test design
     - **Documentation** → Accuracy, completeness, clarity
     - **Infrastructure** → Configuration, deployment impact
   - Assess complexity level and potential risk areas

4. **Structured Comment Generation**:
   - Create comprehensive review request with standard format:
     - `@claude, @codex — please review` (triggers multiple AI reviewers)
     - `@claude`: Primary AI code reviewer (Claude)
     - `@codex`: Additional AI code review agent for second opinion
     - Summary of changes and implementation approach
     - Specific review focus areas with context
     - Code examples and analysis when relevant
     - Risk assessment and areas of concern

5. **Safe GitHub Integration**:
   - Create comment files in `.build/tmp/` directory (never `/tmp/`)
   - Use `gh pr comment <number> --body-file=<path>` for posting
   - Handle all markdown formatting including code blocks
   - Verify successful posting and provide confirmation links

## Example Workflows

### Standard Review Request
```bash
# Agent workflow:
gh pr view 2                          # Validate and get PR info
gh pr diff 2 | head -100             # Preview changes
# Generate structured comment content
mkdir -p .build/tmp
# Write to .build/tmp/pr-review-request-2.md
# Recommended trigger examples to paste in the PR comment:
# - "@claude review"  # Comprehensive review (all categories)
# - "@claude review all"  # Explicit comprehensive review
# - "@claude review correctness"  # Targeted logic/API/security review
# - "@claude review docs"  # Targeted documentation review
# - "@codex review"  # Additional AI perspective
gh pr comment 2 --body-file=.build/tmp/pr-review-request-2.md
```

### Complex PR Analysis
```bash
# With AI analysis for complex changes:
huginn pr review 2                   # Comprehensive AI analysis
# ... same comment generation and posting flow
```

## Comment Structure Standards
- **Format**: `@claude, @codex — please review`
  - Multiple AI reviewers provide comprehensive analysis from different perspectives
- For Claude, use `@claude review` for comprehensive review (default: all categories) or specify individual categories for targeted review (e.g., `@claude review correctness`)
- **Sections**: Summary, Changes Made, Review Focus, Code Examples, Analysis, Areas of Concern, Context
- **Markdown**: Full support including code blocks, quotes, special characters
- **Focus**: Reviewer-oriented with specific, actionable guidance

## Error Handling
- **PR not found**: Clear error with guidance to check PR number or create PR
- **Empty commit history**: Handle PRs with no recent commits gracefully
- **File write failures**: Guide to check `.build/tmp/` directory permissions
- **Comment posting failures**: Clear error messages and retry guidance
- **Huginn failures**: Fallback to manual analysis when AI tools fail

## Safety Considerations
- **File Location**: Always uses `.build/tmp/` (never `/tmp/`)
- **Justfile First**: Uses GitHub CLI and huginn commands
- **Read-Only Analysis**: No modifications to PR or repository
- **Permission Safe**: Handles GitHub authentication gracefully

## Integration with Heimdall Patterns

- **Safety First**: Validates PR state and uses read-only analysis operations
- **Temporary Files**: Uses `.build/tmp/` directory following project standards
- **Agent Specialized**: Leverages domain expertise of pr-review-expert
- **Claude Action**: Uses official GitHub Actions with AI reviewers

## Related Commands
- **Pre-review**: `/gt:commit` - Create commits before requesting review
- **Post-review**: `/pr:enhance` - Enhance PR documentation (TBD)
- **Git Operations**: `/gt:restack` - Update branches before review requests

## Notes
- **Agent-powered workflow** - Uses pr-review-expert for all operations
- **Comprehensive analysis** - Examines commits, files, and metadata systematically
- **Smart AI integration** - Uses huginn for complex PR analysis when needed
- **Safe file handling** - Uses project-standard `.build/tmp/` directory
- **GitHub-ready formatting** - Full markdown support with proper escaping
- **Reviewer-focused** - Provides actionable guidance for effective code review

## Expected Agent Output
The pr-review-expert agent will provide:
- Pre-analysis PR validation and state confirmation
- Comprehensive commit and file change analysis
- AI-powered insights for complex PRs when appropriate
- Structured review request comment generation
- Safe GitHub comment posting with confirmation links
- Clear error reporting if analysis or posting fails
