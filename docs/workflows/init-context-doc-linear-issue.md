# Linear Issue Documentation Update Workflow

Execute the following steps to systematically update documentation for a Linear issue using AI-powered investigation:

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
  - Documentation requirements or specifications
  - Target audience (developers, users, admins)
  - Current documentation gaps or issues
  - Any attachments or screenshots
  - Current status and priority

## 3. Initial Documentation Analysis
Assess the documentation needs before deep investigation:
- **Documentation Type**: Determine if it's API docs, user guides, architecture docs, or workflows
- **Scope Assessment**: Identify affected documentation areas (backend/admin/mobile/workflows)
- **Content Requirements**: Clarify what documentation needs to be created or updated
- **Audience Requirements**: Note target readers and their knowledge level

## 4. Deep Documentation Investigation
Use zen analyze for systematic investigation:
- Run `mcp__zen__analyze` with parameters:
  - `step`: "Investigating documentation needs for Linear issue #[ID]: [issue title]"
  - `step_number`: 1
  - `total_steps`: 5 (adjust based on complexity)
  - `next_step_required`: true
  - `findings`: "Initial documentation analysis from Linear ticket"
  - `model`: "anthropic/claude-opus-4"
  - `analysis_type`: "general"
  - `relevant_files`: [List existing docs or code files that need documentation]

### Documentation Investigation Steps:
1. **Audit Existing Documentation**: Review current docs for gaps or outdated content
2. **Analyze Code/Features**: Understand the functionality that needs documentation
3. **Identify Documentation Patterns**: Follow existing documentation styles and structures
4. **Assess Content Structure**: Determine optimal organization and format
5. **Document Findings**: Compile comprehensive understanding of documentation needs

### Interactive Investigation:
- Use codebase search to find relevant code sections needing documentation
- Review existing documentation patterns and styles
- Check for related documentation that might need updates
- Review recent changes that might affect documentation
- Identify cross-references and navigation needs

### Testing Documentation (When Applicable)
Before finalizing documentation, **always ask the user**:
- "Would you like me to test any procedures or code examples in this documentation? If so, should I use:
  1. **Localhost** - Testing on your local development environment
  2. **Dev environment** - Testing against the deployed development server"
- "Do you need to prepare the environment first? (e.g., start local servers, reset data, etc.)"
- Wait for explicit confirmation and any preparation instructions

#### Documentation Testing Options:
- **Localhost Testing**:
  - Test code examples and procedures locally
  - Verify API endpoints and examples work
  - Faster iteration and validation
  - No impact on shared dev environment

- **Dev Environment Testing**:
  - Test against `https://dev.[domain].com` or configured dev URL
  - Closer to production behavior
  - May affect other developers if data is modified
  - Requires VPN or network access if applicable

### Documentation Validation Strategy
**Goal**: Ensure documentation is accurate, complete, and follows project standards.

#### Assess Documentation Quality:
- **Can Test Examples**:
  - Code snippets and examples
  - API endpoint documentation
  - Setup and configuration guides
  - Workflow procedures
  - Command-line instructions

- **May Not Be Testable**:
  - High-level architecture concepts
  - Design decisions and rationale
  - Historical context
  - Theoretical explanations
  - Future planning documents

#### Documentation Implementation Strategy:
1. **Identify Documentation Location**:
   - For API docs: `docs/api/` or `docs/backend/`
   - For user guides: `docs/user-guides/`
   - For workflows: `docs/workflows/`
   - For architecture: `docs/architecture/`

2. **Follow Documentation Standards**:
   ```markdown
   # Clear, Descriptive Title
   
   ## Overview
   Brief description of what this documentation covers
   
   ## Prerequisites
   What users need to know or have set up first
   
   ## Step-by-Step Instructions
   Clear, numbered steps with examples
   
   ## Examples
   Working code examples with explanations
   
   ## Troubleshooting
   Common issues and solutions
   
   ## Related Documentation
   Links to relevant docs
   ```

3. **Verify Documentation Accuracy**:
   - Test all code examples and procedures
   - Verify all links and references work
   - Check formatting and readability
   - Validate technical accuracy

4. **Ensure Documentation Completeness**:
   - Cover all aspects mentioned in the Linear issue
   - Include necessary examples and use cases
   - Provide troubleshooting information
   - Add proper cross-references

## 5. Documentation Solution Development
Based on investigation findings, develop documentation approach:
- **Content Gap Summary**: Clear explanation of what documentation is missing or outdated
- **Documentation Options**: List possible approaches to structure the content
- **Impact Analysis**: Assess how new documentation affects existing docs
- **Recommended Approach**: Select the best documentation structure with justification

## 6. Validate Documentation with Consensus
Get AI consensus on the proposed documentation approach:
- Run `mcp__zen__consensus` with parameters:
  - `step`: "Validate documentation approach for Linear #[ID]: [brief documentation summary]"
  - `step_number`: 1
  - `total_steps`: 2
  - `next_step_required`: true
  - `findings`: "[Content gap summary and proposed documentation approach]"
  - `model`: "anthropic/claude-opus-4"
  - `models`: [
      {"model": "google/gemini-2.5-pro", "stance": "user-experience-focused"},
      {"model": "openai/gpt-4o", "stance": "technical-accuracy-focused"}
    ]

### Consensus Validation Points:
- Documentation correctly addresses identified gaps
- Content is appropriately structured and organized
- Approach follows project documentation patterns and standards
- Technical accuracy and completeness verified
- User experience and accessibility considered

## 7. Generate Documentation Proposal
Create comprehensive documentation proposal for user approval:

### Documentation Proposal Format
```
## Proposed Documentation Update for Linear Issue #[ID]

### Issue Summary
**Title**: [Linear issue title]
**Documentation Gap**: [Clear explanation of missing or outdated documentation]
**Impact**: [Who is affected and how]

### Investigation Findings
1. [Key finding from documentation investigation]
2. [Additional findings...]
3. [Related discoveries...]

### Current Documentation State
**Existing Documentation**: [List current relevant docs]
**Gaps Identified**: [Specific missing content]
**Outdated Content**: [Content that needs updating]

### Proposed Documentation Updates
**Approach**: [Brief description of documentation strategy]
**Files to Create/Update**:
- File: `docs/path/to/new-doc.md`
  - [Content description]
- File: `docs/path/to/existing-doc.md`
  - [Updates needed]

### Content Structure
```markdown
# Proposed Table of Contents
## Section 1: [Title]
- [Content overview]
## Section 2: [Title]
- [Content overview]
```

### Documentation Examples
```[language]
// Show key code examples that will be included
// Include enough context for clarity
```

### Testing Plan
- [ ] Code examples to validate
- [ ] Procedures to test
- [ ] Links and references to verify

### Quality Assessment
- **Completeness**: Addresses all requirements from Linear issue
- **Accuracy**: Technical content verified
- **Usability**: Clear for target audience
- **Consistency**: Follows project documentation standards

### Consensus Validation
✅ Documentation approach validated by AI consensus
- User experience implications reviewed
- Technical accuracy assessed
- Documentation standards confirmed

**Ready to create this documentation? Please confirm to proceed.**
```

## 8. Implementation Preparation
After user approval, prepare for implementation:
- Create a TodoWrite list for documentation creation steps
- Identify all files that need creation or modification
- Plan content organization and cross-references
- Consider creating a feature branch if not already on one

## 9. Summary Report
Provide documentation investigation completion summary:
- **Linear Issue**: #[ID] - [Title]
- **Documentation Gap Identified**: [Brief gap summary]
- **Investigation Process**: [Summary of investigation steps]
- **Documentation Approach Validated**: Consensus achieved on approach
- **Implementation Ready**: Documentation proposal approved
- **Next Steps**: Ready to create documentation with TodoWrite tracking

## Important Notes
- **Context First**: Always establish project understanding before investigating
- **Systematic Analysis**: Use zen analyze for thorough investigation
- **Test When Possible**: Validate code examples and procedures before documenting
- **Consensus Validation**: Ensure documentation quality through AI consensus
- **User Approval Required**: Never implement without explicit approval
- **Documentation Standards**: Follow project documentation patterns and styles
- **Accuracy**: Verify all technical content and examples
- **Testing**: Always ask user for environment preference (localhost vs dev) and preparation needs before testing examples

## Interactive Elements
Throughout the workflow, ask clarifying questions such as:
- "Who is the primary audience for this documentation?"
- "Are there specific examples or use cases that should be included?"
- "Are there existing documentation patterns I should follow?"
- "Should this documentation include troubleshooting sections?"

## Documentation Investigation Patterns
- Start with understanding the feature/functionality needing documentation
- Review existing documentation for patterns and styles
- Check for cross-references and navigation needs
- Consider different user skill levels and use cases
- Document assumptions and validate technical accuracy

## Follow-up Workflows
After completing this workflow:
- Use `docs/workflows/init-complete-next-task.md` pattern for implementation
- Consider updating Linear ticket with documentation approach
- Run `cleanup-docs-justfile.md` if documentation introduces new patterns

## Verification Before Closing
Before marking the Linear issue as resolved:
- Verify documentation addresses all aspects mentioned in the ticket
- Confirm all examples and procedures work correctly
- Update Linear ticket with:
  - Documentation created or updated
  - Content structure and organization
  - Testing performed on examples
  - Any follow-up recommendations
