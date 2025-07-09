# GitHub Actions PR Analysis Bot

This directory contains the GitHub Actions workflow for automated PR analysis using AI.

## Overview

The PR Analysis Bot automatically analyzes pull requests when they are opened, synchronized, or reopened. It uses Claude AI to evaluate code changes and provides:

- Work type classification (New Feature, Bug Fix, Refactor, etc.)
- Complexity scoring (1-10)
- Risk assessment (1-10)
- Clarity evaluation (1-10)
- Overall impact score
- AI-assistance detection
- Linear ticket compliance checking

## Setup

### Required Secrets

Configure these secrets in your repository settings:

1. **ANTHROPIC_API_KEY** - Your Anthropic API key for Claude AI
   - Get one at https://console.anthropic.com/
   - Add via Settings → Secrets and variables → Actions

### Optional Configuration

The workflow uses the default `GITHUB_TOKEN` which is automatically provided. No additional GitHub token setup is required.

## Usage

### Automatic Triggering

The bot automatically runs when:
- A new PR is opened
- An existing PR is updated (new commits pushed)
- A closed PR is reopened

### Manual Triggering

You can manually trigger the analysis:

1. Go to Actions tab in your repository
2. Select "PR Analysis Bot" workflow
3. Click "Run workflow"
4. Optionally enter a PR number to analyze
5. Click "Run workflow" button

### Understanding the Results

The bot adds a comment to each PR with:

- **Work Type**: The primary category of changes
- **Scores Table**: Visual indicators for complexity, risk, and clarity
  - 🟢 Low (1-3)
  - 🟡 Medium (4-7)
  - 🔴 High (8-10)
- **Additional Information**: File counts, line changes, AI assistance, Linear ticket
- **Labels**: Automatically applied based on analysis

### Labels Applied

The bot applies these label categories:

- **Type Labels**: `type: new-feature`, `type: bug-fix`, `type: refactor`, etc.
- **Complexity Labels**: `complexity: low`, `complexity: medium`, `complexity: high`
- **Risk Labels**: `risk: low`, `risk: medium`, `risk: high`
- **AI Labels**: `ai-assisted` (if AI tools detected)
- **Process Labels**: `has-ticket`, `needs-ticket` (based on Linear ticket presence)

## Troubleshooting

### Common Issues

1. **"No PR number provided"**
   - Ensure the workflow is triggered by a PR event
   - For manual runs, provide the PR number input

2. **API Key Errors**
   - Verify ANTHROPIC_API_KEY is set in repository secrets
   - Check the API key is valid and has credits

3. **Comment Not Appearing**
   - Check Actions tab for workflow run status
   - Ensure the workflow has `pull-requests: write` permission

### Debugging

View detailed logs:
1. Go to Actions tab
2. Click on the workflow run
3. Click on "Analyze Pull Request" job
4. Expand individual steps to see detailed output

## Customization

### Modifying Analysis Criteria

Edit `scripts/github_action_analyzer.py` to adjust:
- Work type categories
- Scoring algorithms
- AI detection patterns
- Linear ticket patterns

### Changing Comment Format

Edit the "Format Comment" step in `.github/workflows/pr-analysis.yml` to customize:
- Comment structure
- Visual indicators
- Information displayed

### Adjusting Labels

Modify the "Apply Labels" step to change:
- Label naming conventions
- Threshold values for categories
- Additional label types

## Cost Considerations

Each PR analysis uses one Claude API call. With Claude 3.5 Sonnet:
- Average cost: ~$0.003-0.015 per PR (depending on diff size)
- Diffs are truncated to 4000 characters to control costs
- Consider using webhooks for high-volume repositories

## Security Notes

- The workflow has minimal permissions (read contents, write PRs/issues)
- API keys are stored as encrypted secrets
- No repository code is sent outside of the diff analysis
- The bot cannot modify code, only add comments and labels# Fix for PR description parsing
