# Linear Issue Debug and Fix Workflow

Execute the following steps to systematically debug and fix a Linear issue using AI-powered investigation:

## 1. Initialize Project Context
Establish understanding of the current system and codebase:
- **Acknowledge & Greet**: State the current date/time and greet the user
- **Review System Documentation**:
  - Read `docs/product/product-overview.md` to understand current system
  - Read `docs/INDEX.md` for documentation navigation
  - Review `docs/architecture/` for system architecture understanding
- **Check Active Development**:
  - Look for `.taskmaster/docs/prd.txt` to understand any active development
  - Note current branch: `git branch --show-current`
  - Review recent changes: `git log --oneline -5`

## 2. Fetch Linear Issue Details
Retrieve and analyze the Linear issue:
- Use the provided Linear issue number/ID
- Run `mcp__linear__get_issue` with the issue ID to get full details
- Extract key information:
  - Issue title and description
  - Steps to reproduce (if provided)
  - Expected vs actual behavior
  - Any error messages or logs
  - Attachments or screenshots
  - Current status and priority

## 3. Initial Issue Analysis
Assess the issue before deep investigation:
- **Issue Type**: Determine if it's a bug, performance issue, or unexpected behavior
- **Scope Assessment**: Identify likely affected components (backend/admin/mobile)
- **Reproduction Path**: Clarify steps to reproduce if not clear
- **Data Requirements**: Note any specific data/environment needed

## 4. Deep Debug Investigation
Use zen debug for systematic investigation:
- Run `mcp__zen__debug` with parameters:
  - `step`: "Investigating Linear issue #[ID]: [issue title]"
  - `step_number`: 1
  - `total_steps`: 5 (adjust based on complexity)
  - `next_step_required`: true
  - `findings`: "Initial issue analysis from Linear ticket"
  - `model`: "anthropic/claude-opus-4"
  - `relevant_files`: [List files mentioned in issue or likely affected]

### Debug Investigation Steps:
1. **Reproduce the Issue**: Attempt to reproduce using provided steps
2. **Trace Execution Path**: Follow code flow from user action to error
3. **Identify Root Cause**: Pinpoint the exact code/configuration causing the issue
4. **Test Edge Cases**: Check related scenarios that might be affected
5. **Document Findings**: Compile comprehensive understanding of the problem

### Interactive Investigation:
- Use codebase search to find relevant code sections
- Analyze error logs and stack traces if available
- **For Web Issues**: Consider using browser tools to reproduce firsthand
- Check recent commits that might have introduced the issue
- Review related code for similar patterns

### Playwright Testing (For Web Issues)
Before running Playwright tests, **always ask the user**:
- "Would you like me to test this issue using Playwright? If so, should I use:
  1. **Localhost** - Running on your local development environment
  2. **Dev environment** - Testing against the deployed development server"
- "Do you need to prepare the environment first? (e.g., start local servers, reset data, etc.)"
- Wait for explicit confirmation and any preparation instructions

#### Playwright Testing Options:
- **Localhost Testing**:
  - Ensure all required services are running locally
  - Use `http://localhost:[port]` for testing
  - Faster iteration and debugging
  - No impact on shared dev environment

- **Dev Environment Testing**:
  - Test against `https://dev.[domain].com` or configured dev URL
  - Closer to production behavior
  - May affect other developers if data is modified
  - Requires VPN or network access if applicable

#### Playwright Test Implementation:
```javascript
// Example Playwright test structure for issue reproduction
const { test, expect } = require('@playwright/test');

test('Reproduce Linear Issue #[ID]', async ({ page }) => {
  // Navigate to affected area
  await page.goto('[URL based on user confirmation]');

  // Follow reproduction steps from Linear ticket
  // Document each step for clarity

  // Capture evidence (screenshots, console logs, network activity)
  await page.screenshot({ path: 'issue-reproduction.png' });
});
```

### Test-First Bug Verification (When Possible)
**Goal**: Write a failing test that proves the bug exists before implementing the fix.

#### Assess Test Feasibility:
- **Can Write Test First**:
  - Unit testable logic errors
  - API endpoint failures
  - Data processing bugs
  - Business logic violations
  - Clear input/output expectations

- **May Not Be Test-First Suitable**:
  - Complex UI interactions
  - Race conditions
  - Environment-specific issues
  - Third-party integration failures
  - Performance degradations

#### Test Implementation Strategy:
1. **Identify Test Location**:
   - For backend: `apps/backend/tests/unit/` or `tests/integration/`
   - For admin: `apps/admin/src/__tests__/`
   - For mobile: `apps/mobile/__tests__/`

2. **Write Failing Test**:
   ```python
   # Example: Backend test proving the bug
   def test_issue_[ID]_reproduces_bug():
       """Test that demonstrates Linear Issue #[ID] bug exists."""
       # Arrange - Set up conditions that trigger the bug

       # Act - Execute the problematic code

       # Assert - Verify the bug occurs (test should FAIL)
       with pytest.raises(ExpectedError):
           # or assert incorrect_behavior == True
   ```

3. **Verify Test Fails**:
   - Run the test to confirm it fails as expected
   - Document the failure output as evidence
   - Include in investigation findings

4. **Keep Test for Fix Validation**:
   - This test will pass once the fix is implemented
   - Ensures the fix actually addresses the issue
   - Prevents regression in the future

#### If Test-First Not Feasible:
- Document why a test-first approach isn't suitable
- Plan to write tests after the fix is implemented
- Consider integration or E2E tests as alternatives
- Note this in the fix proposal

## 5. Solution Development
Based on debug findings, develop solution approach:
- **Root Cause Summary**: Clear explanation of why the issue occurs
- **Solution Options**: List possible approaches to fix the issue
- **Impact Analysis**: Assess potential side effects of each approach
- **Recommended Approach**: Select the best solution with justification

## 6. Validate Solution with Consensus
Get AI consensus on the proposed solution:
- Run `mcp__zen__consensus` with parameters:
  - `step`: "Validate fix approach for Linear #[ID]: [brief solution summary]"
  - `step_number`: 1
  - `total_steps`: 2
  - `next_step_required`: true
  - `findings`: "[Root cause summary and proposed solution]"
  - `model`: "anthropic/claude-opus-4"
  - `models`: [
      {"model": "google/gemini-2.5-pro", "stance": "security-focused"},
      {"model": "openai/gpt-4o", "stance": "performance-focused"}
    ]

### Consensus Validation Points:
- Solution correctly addresses root cause
- No unintended side effects identified
- Approach follows project patterns and best practices
- Security and performance implications considered
- Edge cases properly handled

## 7. Generate Fix Proposal
Create comprehensive fix proposal for user approval:

### Fix Proposal Format
```
## Proposed Fix for Linear Issue #[ID]

### Issue Summary
**Title**: [Linear issue title]
**Root Cause**: [Clear explanation of the problem]
**Impact**: [Who/what is affected and how]

### Investigation Findings
1. [Key finding from debug investigation]
2. [Additional findings...]
3. [Related discoveries...]

### Bug Verification Test
**Test Status**: ✅ Failing test written / ❌ Test-first not feasible
- **Test Location**: `path/to/test_file.py::test_name`
- **Test Result**: [Current failure output proving bug exists]
- **Reason if not feasible**: [Explanation why test-first approach wasn't suitable]

### Proposed Solution
**Approach**: [Brief description of the fix approach]
**Changes Required**:
- File: `path/to/file.ext`
  - [Specific change description]
- File: `path/to/another/file.ext`
  - [Specific change description]

### Implementation Details
```[language]
// Show key code changes with before/after
// Include enough context for clarity
```

### Testing Plan
- [ ] Unit tests to add/update
- [ ] Integration tests needed
- [ ] Manual verification steps

### Risk Assessment
- **Risk Level**: Low/Medium/High
- **Potential Side Effects**: [List if any]
- **Mitigation**: [How risks are addressed]

### Consensus Validation
✅ Solution validated by AI consensus
- Security implications reviewed
- Performance impact assessed
- Best practices confirmed

**Ready to implement this fix? Please confirm to proceed.**
```

## 8. Implementation Preparation
After user approval, prepare for implementation:
- Create a TodoWrite list for implementation steps
- Identify all files that need modification
- Plan test coverage for the fix
- Consider creating a feature branch if not already on one

## 9. Summary Report
Provide investigation completion summary:
- **Linear Issue**: #[ID] - [Title]
- **Root Cause Found**: [Brief root cause]
- **Debug Process**: [Summary of investigation steps]
- **Solution Validated**: Consensus achieved on approach
- **Implementation Ready**: Fix proposal approved
- **Next Steps**: Ready to implement with TodoWrite tracking

## Important Notes
- **Context First**: Always establish project understanding before investigating
- **Systematic Debug**: Use zen debug for thorough investigation
- **Test-First When Possible**: Write a failing test to prove the bug exists before fixing
- **Consensus Validation**: Ensure solution quality through AI consensus
- **User Approval Required**: Never implement without explicit approval
- **Documentation**: Keep detailed notes of investigation findings
- **Reproduction**: Attempt to reproduce issue before proposing fixes
- **Test Coverage**: Always include testing in fix proposals
- **Playwright Testing**: Always ask user for environment preference (localhost vs dev) and preparation needs before running tests

## Interactive Elements
Throughout the workflow, ask clarifying questions such as:
- "Can you provide more details about when this issue occurs?"
- "Is this issue blocking any critical functionality?"
- "Are there specific environments where this happens?"
- "Have there been recent changes to this area of code?"

## Debug Investigation Patterns
- Start broad, then narrow down to specific code
- Check recent changes that might have introduced the issue
- Look for similar patterns in the codebase
- Consider environmental factors (config, data, dependencies)
- Document assumptions and validate them

## Follow-up Workflows
After completing this workflow:
- Use `docs/workflows/init-complete-next-task.md` pattern for implementation
- Consider updating Linear ticket with investigation findings
- Run `cleanup-docs-justfile.md` if fix introduces new patterns

## Verification Before Closing
Before marking the Linear issue as resolved:
- Verify fix addresses all aspects mentioned in the ticket
- Confirm no regressions introduced
- Update Linear ticket with:
  - Root cause explanation
  - Solution implemented
  - Testing performed
  - Any follow-up recommendations
