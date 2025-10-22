---
name: gt:commit
description: Smart GT commit workflow with validation, testing, and optional automatic PR submission with AI-enhanced descriptions
---

# Graphite Commit Workflow

Create well-structured commits using GT workflow with AI-powered commit message generation, automatic validation, intelligent test selection, and optional stack submission with enhanced PR descriptions.

## Usage
```
/gt:commit                         # Create local commit with validation
/gt:commit --no-verify             # Skip validation and tests
/gt:commit --model=opus            # Use Opus for complex changes

# Stack submission modes
/gt:commit --submit                # Commit + gt submit --stack
/gt:commit --submit --enhance      # Commit + submit + AI-enhanced PR title/desc
/gt:commit --submit-quick          # Validate, auto-fix, commit + submit
/gt:commit --submit-no-verify      # Skip all checks, commit + submit
```

## Implementation

### Primary Implementation
Execute the commit workflow directly:

CRITICAL: You MUST:
1. Check staged changes exist with `git status`
2. Generate commit message with `huginn git commit [--model]`
3. Run validation (unless --no-verify)
4. Execute smart test selection based on changed files (unless --no-verify)
5. Use GT workflow with `gt modify --all -m "message"`
6. If --submit flag: Execute `gt submit --stack`
7. If --enhance flag: Use pr-generator-expert to enhance PR

## Workflow Details

### Mode-Specific Behaviors

#### Standard Mode (`/gt:commit`)
1. **Pre-Commit Validation**:
   - Check staged changes exist and warn if none found
   - Warn about large changesets (>500 lines) and confirm intent
   - Validate working directory state

2. **AI-Powered Message Generation**:
   - Use `huginn git commit` for standard commits
   - Use `huginn git commit --model=opus` for complex changes
   - Ensure conventional commit format compliance
   - Follow repository commit standards

3. **Code Quality Validation** (unless --no-verify):
   - Execute `just test-unit` and ensure it passes
   - Stop process if tests fail with clear error reporting
   - Guide user to fix issues before proceeding

4. **GT Workflow Execution**:
   - Use `gt modify --all -m "message"` (never `gt create`)
   - Verify commit success and provide confirmation
   - Display commit hash and summary

#### Submit Mode (`/gt:commit --submit`)
Same as standard mode, plus:
- After successful commit, execute `gt submit --stack`
- Confirm submission success
- Display PR URLs if created

#### Enhanced Submit Mode (`/gt:commit --submit --enhance`)
Same as submit mode, plus:
- After PR creation, invoke `pr-generator-expert` agent
- Agent generates AI-powered PR title with `huginn git pr-title <number>`
- Agent generates AI-powered PR description with `huginn git pr-desc <number>`
- Agent updates PR via `gh pr edit <number> --title="..." --body="..."`
- Provides final PR link with enhanced documentation

#### Submit Quick Mode (`/gt:commit --submit-quick`)
Optimized workflow:
1. Run validation and attempt auto-fix if possible
2. Generate commit message with AI
3. Create commit with GT
4. Submit to stack immediately
5. Skip manual intervention where possible

#### Submit No-Verify Mode (`/gt:commit --submit-no-verify`)
**USE WITH CAUTION:**
- Skips all validation and testing
- Immediately creates commit and submits to stack
- Useful for documentation-only changes or urgent hotfixes
- Should be exception, not standard practice

### Smart Test Selection

Based on changed files:
- **Core Python changes** → `just test-unit`
- **Integration changes** → `just test-integration`
- **System-wide updates** → `just test`
- **Docs/config only** → Skip tests after confirming no runtime impact

## PR Enhancement Workflow

When using `--enhance` flag:

1. **Commit created and submitted** → PR created on GitHub
2. **Get PR number** from `gt submit` output or `gh pr list`
3. **Invoke pr-generator-expert** agent:
   ```
   Use Task tool with:
   - subagent_type: "pr-generator-expert"
   - description: "Generate and apply AI-powered PR title and description"
   - prompt: "Enhance PR <number> with AI-generated title and description using huginn"
   ```
4. **Agent workflow**:
   - Validates PR exists with `gh pr view <number>`
   - Generates title: `huginn git pr-title <number> [--model]`
   - Generates description: `huginn git pr-desc <number> [--model]`
   - Applies changes: `gh pr edit <number> --title="..." --body="..."`
   - Confirms success with PR link

## What Gets Checked

- Staged changes exist
- Tests pass before commit (unless --no-verify)
- Commit message follows conventions
- GT stack state is valid
- Branch is properly created/modified
- PR submission successful (if --submit)
- PR enhanced with AI (if --enhance)

## Error Handling

- **No staged changes**: Clear error, guide to `git add`
- **Tests fail**: Show failures, prevent commit
- **GT errors**: Display GT output, suggest fixes
- **Submit fails**: Show error, suggest manual submission
- **Enhance fails**: Commit/submit succeeded, enhancement can be retried

## Related Commands

- `/gt:restack` - Restack branches after commits
- `/pr:request-review` - Request review after PR creation
- `/pr:enhance` - Re-enhance PR description later (TBD)

## Requires

- git-commit-expert agent
- pr-generator-expert agent (for --enhance)
- Working GT installation
- Huginn CLI for AI generation
- Tests configured in justfile
