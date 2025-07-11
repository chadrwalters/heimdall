# Documentation and Justfile Cleanup Workflow

Execute the following steps to review and update documentation and justfile commands after completing development work:

## 1. Gather Work Context
Collect information about recent changes:
- Check current branch: `git branch --show-current`
- Review uncommitted changes: `git status --porcelain`
- Get recent commits: `git log --oneline -10`
- Check PR if exists: `gh pr view --json title,body,commits`
- Review changed files: `git diff --name-only HEAD~5..HEAD`

## 2. Analyze Changed Code Areas
For each modified file from step 1:
- Identify which system components were affected (backend, admin, mobile)
- Note any new features, APIs, or patterns introduced
- Document configuration changes or new environment variables
- List any terminal commands used during development

## 3. Review Existing Documentation
Check documentation completeness for changed areas:
- Read `docs/INDEX.md` to understand current structure
- For each affected component, check if docs exist:
  - Backend changes → Check `docs/backend/` subdirectories
  - Admin changes → Check `docs/admin/` subdirectories
  - Mobile changes → Check `docs/mobile/` subdirectories
  - Infrastructure → Check `docs/setup/` and `docs/workflows/`
  - Architecture → Check `docs/architecture/`

## 4. Identify Documentation Gaps
Create a checklist of missing or outdated documentation:

### Missing Documentation Checklist
- [ ] **New Features**: Are new features documented in appropriate requirements.md?
- [ ] **API Changes**: Are new endpoints documented in api-contracts.md?
- [ ] **Configuration**: Are new env vars documented in environment-configuration.md?
- [ ] **Architecture**: Do new patterns need architecture documentation?
- [ ] **Workflows**: Are new operational procedures documented?
- [ ] **Gotchas**: Were any tricky issues encountered that should be in gotchas/?
- [ ] **Setup Changes**: Do setup guides need updating?

### Outdated Documentation Checklist
- [ ] **Changed Behavior**: Do existing docs reflect current implementation?
- [ ] **Deprecated Features**: Are old features marked as deprecated?
- [ ] **Updated Dependencies**: Are version requirements current?
- [ ] **Modified Workflows**: Do procedures match current process?

## 5. Analyze Terminal Command Usage
Review recent terminal history for automation opportunities:
- Identify repeated command sequences
- Find complex commands that could be simplified
- Look for multi-step processes without automation
- Check for commands with environment-specific parameters

### Command Pattern Analysis
Look for patterns like:
- Multiple commands always run together
- Commands with complex flags/parameters
- Environment-specific command variations
- Commands that require specific directory context
- Debugging or inspection command sequences

## 6. Review Justfile for Gaps
Compare identified commands with existing justfile:
- Read current `justfile` to understand existing commands
- Check if new workflows have corresponding commands
- Identify missing convenience commands
- Look for commands that could be enhanced

### Justfile Enhancement Checklist
- [ ] **New Workflows**: Do new development workflows have commands?
- [ ] **Complex Operations**: Are multi-step processes automated?
- [ ] **Environment Management**: Are env-specific commands parameterized?
- [ ] **Testing Commands**: Are new test scenarios covered?
- [ ] **Debugging Tools**: Are common debugging sequences automated?
- [ ] **Documentation**: Do commands have clear descriptions?

## 7. Generate Update Recommendations
Based on analysis, create prioritized recommendations:

### Documentation Updates Needed
Format: `[Priority] Location: Description`
```
[HIGH] docs/backend/api-development.md: Add new authentication endpoint documentation
[HIGH] docs/setup/environment-configuration.md: Document NEW_API_KEY variable
[MEDIUM] docs/workflows/: Create new workflow for feature X deployment
[LOW] docs/gotchas/: Add note about Y configuration issue
```

### Justfile Commands Proposed
Format: `Command Name: Purpose (replaces terminal sequence)`
```
just db_migrate_status: Check migration status (replaces: cd apps/backend && alembic current)
just test_feature_x: Run feature X tests (replaces: pytest tests/feature_x --cov)
just deploy_check: Pre-deployment validation (replaces: multiple validation commands)
```

### INDEX.md Updates Required
- [ ] Add new document links to appropriate sections
- [ ] Update quick start paths if workflows changed
- [ ] Add new gotchas to troubleshooting section
- [ ] Update document counts in statistics

## 8. Present Findings for Review
Summarize all findings in a structured report:

```markdown
## Documentation & Justfile Cleanup Report

### Work Context
- **Branch**: feature/xyz
- **Changed Files**: 15 files across backend and admin
- **Key Changes**: Added new API endpoints, updated auth flow

### Documentation Gaps Found
1. **Missing Documentation** (5 items):
   - New API endpoints lack documentation
   - Environment variables undocumented
   - [List all gaps...]

2. **Outdated Documentation** (3 items):
   - Auth flow documentation doesn't match implementation
   - [List all outdated items...]

### Justfile Improvements Identified
1. **New Commands Needed** (4 commands):
   - Database migration helpers
   - Feature-specific test runners
   - [List all new commands...]

2. **Existing Commands to Enhance** (2 commands):
   - Add parameters to deployment commands
   - [List enhancements...]

### Proposed Actions (Awaiting Approval)
1. Create/Update Documentation:
   - [ ] Update api-development.md with new endpoints
   - [ ] Add environment variables to configuration guide
   - [ ] [List all documentation tasks...]

2. Add Justfile Commands:
   - [ ] Add `just db_migrate_status` command
   - [ ] Add `just test_feature_x` command
   - [ ] [List all justfile additions...]

3. Update INDEX.md:
   - [ ] Add links to new documentation
   - [ ] Update statistics
   - [ ] [List INDEX updates...]

**Ready to proceed with updates? Please indicate which items to implement.**
```

## 9. Implementation Guidelines
Once approved, implement updates following these patterns:

### Documentation Standards
- Follow existing document structure in target files
- Include metadata headers (version, date, status)
- Add cross-references to related documentation
- Use consistent formatting and heading levels

### Justfile Command Standards
- Include descriptive comments above commands
- Use consistent naming (snake_case)
- Group related commands together
- Include success/failure indicators
- Follow existing parameter patterns

### INDEX.md Update Pattern
- Maintain alphabetical ordering within sections
- Include brief descriptions for new entries
- Update document counts and last updated date
- Preserve existing formatting

## Important Notes
- **Review First**: Always analyze before proposing changes
- **User Approval**: Get explicit approval before implementing
- **Incremental Updates**: Can be run after each feature/PR
- **Living Documents**: Documentation should evolve with code
- **Automation Focus**: Prioritize repetitive tasks for justfile
- **Findability**: Follow INDEX.md patterns for discoverability
- **Git Context**: Always consider current branch/PR scope

## Cleanup Verification Checklist
After implementing approved updates:
- [ ] All new features have documentation
- [ ] Common command sequences have just commands
- [ ] INDEX.md accurately reflects documentation structure
- [ ] No broken cross-references in documentation
- [ ] Justfile commands tested and working
- [ ] Documentation follows established patterns
- [ ] Git status clean (all changes committed)

## Follow-up Workflows
After completing this cleanup:
- Consider running `docs/workflows/init-context.md` to verify documentation accessibility
- Use new just commands in future development
- Schedule periodic documentation reviews
