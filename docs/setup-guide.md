# Heimdall - Setup Guide

This guide provides detailed setup instructions for the Heimdall Engineering Observability Framework.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [API Setup](#api-setup)
5. [Verification](#verification)
6. [First Run](#first-run)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, or Windows (with WSL recommended)
- **Python**: 3.12 or higher
- **Git**: Latest version
- **Disk Space**: At least 2GB free space
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Network**: Internet connection for API calls

### Developer Tools

#### Required
- **uv**: Python package manager
- **just**: Command runner
- **git**: Version control

#### Recommended
- **Graphite CLI**: Stacked PR workflow
- **Huginn CLI**: AI-assisted PR/git operations
- **GitHub CLI**: PR and Actions management

#### Optional
- **Claude Desktop**: For .claude commands and agents
- **pre-commit**: Git hooks for quality

### Required Tools

1. **Python 3.12+**
   ```bash
   # Check Python version
   python3 --version
   
   # Install Python 3.12 if needed
   # macOS (using Homebrew)
   brew install python@3.12
   
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.12 python3.12-pip
   ```

2. **uv Package Manager** (replaces pip/venv)
   ```bash
   # Install uv (recommended method)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Alternative: via Homebrew (macOS)
   brew install uv
   
   # Verify installation
   uv --version
   # Should show version 0.1.0 or higher
   ```

3. **Just Command Runner**
   ```bash
   # macOS
   brew install just
   
   # Linux
   curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin
   
   # Windows (using Chocolatey)
   choco install just
   
   # Verify installation
   just --version
   ```

4. **GitHub CLI**
   ```bash
   # macOS
   brew install gh
   
   # Ubuntu/Debian
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update
   sudo apt install gh
   
   # Verify installation
   gh --version
   ```

5. **Git**
   ```bash
   # Should already be installed, but verify
   git --version

   # If not installed:
   # macOS: install Xcode Command Line Tools
   xcode-select --install

   # Ubuntu/Debian
   sudo apt install git
   ```

### Recommended Tools

6. **Graphite CLI** (for stacked PR workflow)
   ```bash
   # macOS
   brew install graphite

   # Verify installation
   gt --version

   # Initialize in repo (after cloning)
   gt repo init
   ```

7. **Huginn CLI** (AI-assisted PR/git operations)
   ```bash
   # Installed via justfile after project setup
   just env install-huginn

   # Verify installation
   huginn --help
   ```

## Installation

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/YOUR_ORG/heimdall.git
cd heimdall

# Verify you're in the right directory
ls -la
# Should see justfile, src/, docs/, .claude/, etc.
```

### 2. Set Up Python Environment with UV

```bash
# Setup project environment (automatically creates venv and installs deps)
just setup

# This runs:
# uv sync (automatically creates .venv/ and installs dependencies)

# Verify the environment was created
ls -la .venv/
```

### 3. Using UV Environment (No Manual Activation Needed)

UV automatically manages the environment for you:

```bash
# Run commands with UV (automatically uses correct environment)
uv run python --version
# Shows Python from the virtual environment

# All project commands use UV automatically via justfile
just env-check
just verify-apis
```

**Note**: With UV, you don't need to manually activate/deactivate virtual environments. UV automatically uses the correct environment when you run `uv run` commands or use the justfile commands.

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Create .env file
cp .env.example .env  # if example exists
# OR
touch .env
```

Add the following to your `.env` file:

```bash
# Required: GitHub Personal Access Token
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Required: Anthropic API Key for Claude
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Linear API Key (for ticket linking)
LINEAR_API_KEY=your_linear_api_key_here
# OR
LINEAR_TOKEN=your_linear_token_here
```

### 2. AI Developer Configuration

Configure AI developer overrides in `config/ai_developers.json`:

```json
{
  "always_ai_developers": [
    {
      "username": "your-username",
      "email": "you@company.com",
      "ai_tool": "Claude/Cursor",
      "percentage": 100
    }
  ]
}
```

### 3. Scheduling Configuration (Optional)

For scheduled runs, copy and customize the schedule configuration:

```bash
# Set up scheduling configuration
just schedule-setup

# Edit the configuration
edit config/schedule.conf
```

## API Setup

### 1. GitHub Token

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Click "Generate new token (classic)"
3. Select these scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read org and team membership)
   - `read:user` (Read user profile data)
4. Copy the token and add it to your `.env` file

### 2. Anthropic API Key

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Create a new API key
3. Copy the key and add it to your `.env` file
4. Ensure you have sufficient credits for analysis

### 3. Linear API Key (Optional)

1. Go to Linear Settings > API
2. Create a new API key
3. Copy the key and add it to your `.env` file

### 4. Authenticate GitHub CLI

```bash
# Authenticate with GitHub CLI
gh auth login

# Follow the prompts to authenticate
# Choose "GitHub.com"
# Choose "HTTPS"
# Choose "Login with a web browser"
```

## Verification

### 1. Check Environment

```bash
# Check all environment variables
just env-check

# Expected output:
# ✅ Environment Variables:
#    GitHub Token: ✅ Set
#    Anthropic API Key: ✅ Set
#    Linear API Key: ✅ Set (optional)
```

### 2. Verify API Connections

```bash
# Test all API connections
just verify-apis

# This will test:
# - GitHub API access
# - Anthropic API access
# - Linear API access (if configured)
```

### 3. Run Tests

```bash
# Run the test suite
just test

# Run specific tests
just test-unit
just test-integration
```

## First Run

### 1. Dry Run Test

```bash
# Test the main script without actually processing (using UV)
uv run python main.py --org your-org-name --dry-run

# Expected output:
# 🌟 North Star Metrics - Engineering Impact Framework
# Organization: your-org-name
# Mode: pilot
# 🔍 DRY RUN MODE - No actual processing will occur
# ✅ Dry run complete - environment and configuration validated
```

### 2. Small Pilot Run

```bash
# Run a small pilot analysis (7 days)
just pilot your-org-name

# OR using the main script directly with UV
uv run python main.py --org your-org-name --mode pilot

# This will:
# 1. Extract GitHub data (repos, PRs, commits)
# 2. Run AI analysis on the data
# 3. Generate unified output files
# 4. Create developer metrics
```

### 3. Review Results

After a successful run, you should see these files:

```bash
ls -la *.csv
# Expected files:
# - org_commits.csv       (raw commit data)
# - org_prs.csv          (raw PR data) 
# - unified_pilot_data.csv (AI-analyzed results)
# - developer_metrics.csv  (aggregated metrics)
```

## Troubleshooting

### Common Issues

#### 1. Python Version Issues

```bash
# Error: Python 3.12+ required
# Solution: Install Python 3.12+

# Check current version
python3 --version

# Install via pyenv (recommended)
curl https://pyenv.run | bash
pyenv install 3.12.0
pyenv global 3.12.0
```

#### 2. UV Not Found

```bash
# Error: uv command not found
# Solution: Install uv

curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

#### 3. GitHub API Authentication

```bash
# Error: GitHub API authentication failed
# Solution: Re-authenticate

gh auth logout
gh auth login
# Follow prompts again
```

#### 4. Missing Environment Variables

```bash
# Error: Missing required environment variables
# Solution: Check .env file

just env-check
# Fix any missing variables
```

#### 5. Anthropic API Issues

```bash
# Error: Anthropic API rate limiting or insufficient credits
# Solution: Check account status

# Verify API key format (should start with 'sk-ant-')
echo $ANTHROPIC_API_KEY | cut -c1-7
# Should output: sk-ant-

# Check account: https://console.anthropic.com/
```

#### 6. Linear API Issues

```bash
# Error: Linear API connection failed
# Solution: Verify API key and permissions

# Linear is optional - you can skip it
# Remove LINEAR_API_KEY from .env if not needed
```

### Debug Mode

Run with debug logging for detailed troubleshooting:

```bash
# Enable debug logging (using UV)
uv run python main.py --org your-org-name --log-level DEBUG --log-file debug.log

# Review the log file
tail -f debug.log
```

### Getting Help

1. **Check Documentation**
   ```bash
   just docs-list
   just docs-serve  # Browse at http://localhost:8000
   ```

2. **Run Help Commands**
   ```bash
   uv run python main.py --help
   just --list
   just help  # Shows organized command help
   ```

3. **Check Project Status**
   ```bash
   just stats
   just env-check
   just verify-apis
   ```

### Clean Start

If you need to start over:

```bash
# Clean all generated files
just clean

# Remove virtual environment and UV cache
rm -rf .venv
uv cache clean

# Re-run setup with UV
just setup
```

## Next Steps

After successful setup:

1. **Run Regular Analysis**: Set up scheduled runs with `just schedule-help`
2. **Explore Data**: Review the generated CSV files
3. **Configure Organization**: Add your team to `config/ai_developers.json`
4. **Set Up Monitoring**: Configure GitHub Actions for automated runs
5. **Read Advanced Documentation**: Check `docs/` for detailed guides

## Performance Notes

- **First Run**: May take 10-30 minutes depending on organization size
- **Incremental Updates**: Usually 2-10 minutes
- **API Rate Limits**: GitHub: 5000/hour, Anthropic: varies by plan
- **Cost Estimates**: ~$0.01-0.10 per analyzed PR/commit (Anthropic costs)
- **UV Performance**: 10-100x faster dependency installation compared to pip
- **Memory Usage**: UV typically uses ~50MB RAM vs ~200MB for pip

---

For more detailed information, see:
- [UV Migration Guide](setup/uv-migration.md) - UV package manager migration
- [Import Conflicts Guide](troubleshooting/import-conflicts.md) - Resolving Python import issues
- [Main Usage Guide](usage-guide.md)
- [Configuration Reference](configuration-reference.md)
- [API Documentation](api-reference.md)