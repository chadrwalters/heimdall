# 🚫 ABSOLUTE SAFETY RULES

## NEVER WITHOUT PERMISSION:
1. **Source Control**: NO git commands except read-only (`git status`, `git diff`)
2. **Production Operations**: NO pipeline commands on production data
3. **API Keys**: NO exposure or logging of secrets in code/output
4. **Data Deletion**: NO destructive operations on analysis data

## 🛡️ PRODUCTION SAFETY CRITICAL RULES:
- **NEVER DELETE** production analysis data or state files
- **NEVER COMMIT** API keys or sensitive configuration
- **CAN ANALYZE** development/staging data freely
- **MUST VERIFY** data scope before large-scale operations

## ✅ ALWAYS ASK FIRST:
- "Should I run analysis on [scope]?" → Wait for explicit "yes"
- "Should I commit these changes?" → Wait for user confirmation
- "Should I process [large dataset]?" → Confirm scope and impact

## 🚨 SPECIFIC DANGEROUS COMMANDS - NEVER RUN WITHOUT PERMISSION:

### Git Operations (Except Read-Only)
- `git push` → Can affect shared repository
- `git commit` → Only with explicit user request  
- `git reset --hard` → Destroys uncommitted work
- `git branch -D` → Deletes branches permanently

### Data Operations
- `rm -rf analysis_state.json` → Destroys analysis state
- `rm -rf data/` → Removes extracted data
- `rm -rf logs/` → Removes analysis logs
- Any operation that deletes CSV files or analysis results

### API Operations  
- Mass API calls without rate limiting
- Batch operations across multiple organizations
- Any operation that could hit API rate limits

### File System Operations
- `rm -rf` → Permanent file deletion
- `sudo` commands → System-level changes
- Any operation outside project directory → System impact

### Analysis Pipeline
- `just pipeline [org] [large-days]` → Resource-intensive operations
- Large-scale data extraction → Potential API quota issues
- Multi-org batch processing → Risk of rate limiting