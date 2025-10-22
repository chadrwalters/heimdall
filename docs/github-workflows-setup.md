# GitHub Workflows Setup Guide

Heimdall includes automated GitHub Actions workflows for AI-powered code review and quality checks.

## Available Workflows

### 1. Claude Code Review (`claude.yml`)

AI-powered code review using Claude Sonnet 4.

**Triggers:**
- Comment `@claude` on a PR or issue
- PR review mentioning `@claude`
- Issue creation/assignment mentioning `@claude`

**Capabilities:**
- Comprehensive code review
- Security analysis
- Best practices suggestions
- Test coverage recommendations
- CI results analysis

**Required Secrets:**
- `ANTHROPIC_API_KEY` - Your Anthropic API key ([Get one here](https://console.anthropic.com/))

**Permissions:**
- `contents: write` - Read/write repository code
- `pull-requests: write` - Comment on PRs
- `issues: write` - Comment on issues
- `id-token: write` - OIDC token for authentication
- `actions: read` - Read CI/CD results

### 2. Codex Review (`codex-review.yml`)

OpenAI Codex-powered code review with inline comments.

**Triggers:**
- Comment `@codex` on a PR
- Slash command `/codex` on a PR
- Manual workflow dispatch

**Capabilities:**
- Summary review comment
- Inline code comments
- Technical analysis
- Alternative perspective to Claude

**Required Secrets:**
- `OPENAI_API_KEY` - Your OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

**Permissions:**
- `contents: read` - Read repository code
- `pull-requests: write` - Post review comments
- `issues: write` - Post issue comments
- `actions: read` - Read workflow runs

### 3. CI/CD (`ci.yml`)

Automated testing and quality checks on every PR.

**Triggers:**
- Push to any branch
- Pull request creation/update

**Jobs:**
- Linting (ruff)
- Format checking (ruff format)
- Type checking (mypy)
- Unit tests (pytest)
- Security scanning (bandit)

**No secrets required** - uses repository code only

## Setup Instructions

### Step 1: Add Required Secrets

1. Go to your repository settings
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **New repository secret**
4. Add the following secrets:

#### For Claude Reviews
```
Name: ANTHROPIC_API_KEY
Value: sk-ant-xxxxxxxxxxxxxxxxxxxxx
```

#### For Codex Reviews
```
Name: OPENAI_API_KEY
Value: sk-xxxxxxxxxxxxxxxxxxxxx
```

### Step 2: Enable GitHub Actions

1. Go to **Settings → Actions → General**
2. Under **Actions permissions**, select:
   - ✅ Allow all actions and reusable workflows
3. Under **Workflow permissions**, select:
   - ✅ Read and write permissions
   - ✅ Allow GitHub Actions to create and approve pull requests

### Step 3: Test the Workflows

#### Test Claude Review
1. Create a test PR
2. Add a comment: `@claude review this PR`
3. Claude will analyze the PR and post a comprehensive review

#### Test Codex Review
1. On the same PR, add a comment: `@codex review`
2. Codex will post a summary and inline comments

#### Test CI/CD
1. Push any commit to a branch
2. CI workflow runs automatically
3. Check **Actions** tab for results

## Usage Examples

### Request Comprehensive Claude Review
```
@claude review
```

### Request Focused Review
```
@claude review the authentication logic in src/auth.py
```

### Request Codex Review
```
@codex review
```

### Check CI Results
```
@claude check the CI failures
```
(Claude can read CI results with `actions: read` permission)

## Workflow Customization

### Customize Claude Behavior

Edit `.github/workflows/claude.yml`:

```yaml
- name: Run Claude Code
  uses: anthropics/claude-code-action@beta
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    github_token: ${{ github.token }}

    # Use Claude Opus 4 for more complex reviews
    model: "claude-opus-4-20250514"

    # Custom trigger phrase
    trigger_phrase: "/review"

    # Custom instructions
    custom_instructions: |
      Focus on:
      - Data processing logic
      - Linear API integration
      - Test coverage
      - Documentation quality
```

### Customize Codex Behavior

Edit `.github/workflows/codex-review.yml`:

```yaml
- name: Codex autonomous review
  uses: gersmann/codex-review-action@v1
  with:
    mode: review
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    model: gpt-5-codex
    reasoning_effort: high  # Change to 'low', 'medium', or 'high'
    debug_level: 2          # More verbose logging
```

## Troubleshooting

### Claude Not Responding

**Check:**
1. Is `ANTHROPIC_API_KEY` secret set correctly?
2. Does the comment include `@claude`?
3. Check **Actions** tab for workflow run status
4. Verify API key has credits: https://console.anthropic.com/

**Common Issues:**
- API key expired or invalid
- Rate limiting (wait a few minutes)
- Workflow permissions not configured

### Codex Not Responding

**Check:**
1. Is `OPENAI_API_KEY` secret set correctly?
2. Does the comment include `@codex` or `/codex`?
3. Check **Actions** tab for errors
4. Verify OpenAI account has credits

**Common Issues:**
- API key missing or invalid
- Model access not enabled (gpt-5-codex)
- Organization rate limits

### CI Failures

**Common Causes:**
- Linting errors → Run `just quality lint-fix` locally
- Format issues → Run `just quality format` locally
- Type errors → Run `just quality type-check` locally
- Test failures → Run `just test` locally
- Security issues → Review bandit output

## Cost Management

### Claude Review Costs

- **Claude Sonnet 4**: ~$3-15 per review
- **Claude Opus 4**: ~$15-75 per review (if enabled)

**Cost Control:**
- Use Sonnet 4 for most reviews (default)
- Reserve Opus 4 for complex architectural changes
- Monitor usage at https://console.anthropic.com/

### Codex Review Costs

- **GPT-5 Codex**: ~$0.01-0.20 per review (varies by PR size)

**Cost Control:**
- Codex is typically much cheaper than Claude
- Good for quick second opinions
- Use for focused inline comments

## Integration with /pr:request-review Command

The `/pr:request-review` command generates review requests that trigger these workflows:

```bash
# In Claude Desktop
/pr:request-review 2

# Generates comment like:
# @claude, @codex — please review
#
# ## Changes Summary
# [AI-generated summary]
#
# ## Review Focus
# - [Specific areas to review]
```

This triggers both Claude and Codex workflows automatically.

## Best Practices

1. **Use CI First**: Let automated CI catch basic issues before requesting AI review
2. **Targeted Reviews**: Ask specific questions to get better responses
3. **Combine Perspectives**: Use both @claude and @codex for important changes
4. **Review Costs**: Monitor API usage to control costs
5. **Iterate**: Engage in conversation with Claude for deeper analysis

## Related Documentation

- [PR Workflow Commands](../.claude/README.md) - Claude commands for PR management
- [Graphite Workflow](./graphite-workflow.md) - Stacked PR development
- [CI/CD Configuration](../.github/workflows/ci.yml) - Automated quality checks
