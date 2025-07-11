# Git-Based Extraction Workflow

## Purpose
Step-by-step procedures for using the git-based extraction system, including setup, execution, monitoring, and troubleshooting of the local git repository approach.

## When to Use This
- Running git-based data extraction for the first time
- Executing regular analysis workflows
- Troubleshooting extraction issues
- Optimizing extraction performance

**Keywords:** git extraction, workflow procedures, extraction commands, cache management

---

## 🚀 Quick Start Workflow

### First-Time Setup

**1. Environment Verification**
```bash
just env-check
```
**Expected Output**:
- ✅ GitHub Token: Set
- ✅ Anthropic API Key: Set
- ✅ Linear API Key: Set (optional)

**2. API Connectivity Test**
```bash
just verify-apis
```
**Expected Output**:
- ✅ GitHub API: Connected
- ✅ Anthropic API: Connected
- ✅ Linear API: Connected (if configured)

**3. First Extraction (Pilot)**
```bash
just pilot organization-name
```
**What This Does**:
- Discovers all active repositories for the organization
- Clones repositories to `.git_cache/repos/organization-name/`
- Extracts 7 days of commit and PR data
- Runs AI analysis on extracted data
- Generates analysis reports

---

## 📊 Standard Extraction Workflows

### 7-Day Pilot Analysis
```bash
just pilot organization-name
```

**Process Flow**:
1. **Repository Discovery** (1 API call)
   - Fetches list of active repositories from GitHub
   - Saves repository metadata to `organization-name_repos.json`

2. **Repository Cloning** (0 API calls)
   - Clones each repository to `.git_cache/repos/organization-name/`
   - Uses shallow clone (depth=100) for performance
   - Skips if repository already exists locally

3. **Commit Extraction** (0 API calls)
   - Extracts commits from last 7 days using git log
   - Calculates file statistics from git diff
   - Identifies merge commits and PR numbers

4. **PR Metadata Enrichment** (~50 API calls)
   - Fetches GitHub PR metadata for merge commits found in git
   - Correlates git commits with PR titles, descriptions, labels

5. **Data Output**
   - Saves commit data to `org_commits.csv`
   - Saves PR data to `org_prs.csv`
   - Both files compatible with existing analysis pipeline

6. **AI Analysis**
   - Processes extracted data through Claude analysis engine
   - Generates unified analysis results

**Expected Timeline**: 5-15 minutes for 50-100 repositories

### 30-Day Full Analysis
```bash
just pipeline organization-name 30
```

**Enhanced Process**:
- Same workflow as pilot but with 30-day extraction window
- More comprehensive data for trend analysis
- Longer processing time but better insights

**Expected Timeline**: 15-45 minutes for 50-100 repositories

### Incremental Updates
```bash
just extract-incremental organization-name
```

**Optimization Features**:
- Loads last analyzed commit SHA from `.git_cache/state/`
- Processes only new commits since last run
- Updates existing repositories with `git fetch`
- Significantly faster than full extraction

**Expected Timeline**: 2-5 minutes for incremental updates

---

## 🔄 Advanced Workflows

### Custom Time Ranges
```bash
just extract organization-name 14    # 14-day extraction
just extract organization-name 90    # 90-day extraction (large)
```

**Performance Considerations**:
- Days > 30: May require extended processing time
- Days > 90: Consider running overnight
- Large organizations: Scale linearly with repository count

### Single Repository Analysis
```bash
just extract-repo organization/repository 7
```

**Use Cases**:
- Testing extraction on specific repository
- Debugging repository-specific issues
- Focused analysis on critical repositories

### Repository Discovery Only
```bash
just list-repos organization-name
```

**Output**:
- List of all active repositories
- Repository descriptions
- Quick overview without full extraction

---

## 📁 Cache Management Workflows

### Cache Status Monitoring
```bash
just cache-status
```

**Comprehensive Output**:
```
📊 Cache Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 API Cache (.cache/):
  42 cache files
  15MB total size

📁 Git Cache (.git_cache/):
  25 repositories cloned
  1.2GB total size
  3 organizations

📊 Git Cache Details:
  Total repositories: 25
  Total size: 1250.3 MB
  acme-corp: 15 repos
  startup-inc: 10 repos
```

### Git Repository Health Check
```bash
just git-status
```

**Health Metrics**:
- Repository clone status
- Last update timestamps
- Disk usage per organization
- Corrupted repository detection

### Cache Cleanup
```bash
just cache-clean           # Clean expired API cache
just git-cleanup org-name  # Clean specific organization
just cache-rebuild         # Nuclear option: clear everything
```

**Cleanup Strategy**:
- API cache: Remove expired entries (24-48 hour TTL)
- Git cache: Remove unused organizations
- Full rebuild: Start fresh (useful for major issues)

---

## 📊 Monitoring & Performance

### Extraction Statistics
```bash
just extract-stats organization-name
```

**Performance Metrics**:
- API calls made vs avoided
- Extraction time breakdown
- Cache hit rates
- Data volume processed

### Performance Benchmarking
```bash
just benchmark-extraction organization-name
```

**Comparison Analysis**:
- Git-based vs traditional API extraction
- Time per repository analysis
- API usage efficiency metrics
- Storage vs speed trade-offs

### Git Cache Refresh
```bash
just git-refresh organization-name
```

**Force Update Scenarios**:
- Repositories haven't updated in several days
- Suspected cache corruption
- Major changes to repository structure
- After organization repository changes

---

## 🚨 Troubleshooting Workflows

### Common Issue Resolution

**Problem**: Extraction fails with authentication error
```bash
just env-check              # Verify GitHub token
just verify-apis            # Test API connectivity
export GITHUB_TOKEN=ghp_... # Set/update token
just extract org-name       # Retry extraction
```

**Problem**: Repository clone fails
```bash
just git-status             # Check repository health
just git-cleanup org-name   # Clean corrupted repositories
just extract org-name       # Re-clone repositories
```

**Problem**: Slow extraction performance
```bash
just cache-status           # Check cache size
just cache-clean            # Clean old cache entries
just git-cleanup org-name   # Remove unused repositories
```

**Problem**: Inconsistent data results
```bash
just git-refresh org-name   # Force repository updates
just cache-rebuild          # Clear all caches
just extract org-name       # Fresh extraction
```

### Diagnostic Procedures

**1. System Health Check**
```bash
just health
```

**2. Log Analysis**
```bash
just logs extraction        # Extraction-specific logs
just logs git              # Git operation logs
```

**3. Full System Validation**
```bash
just test-integration      # Test all API connections
just test-extraction       # Test extraction pipeline
```

---

## 🎯 Best Practices

### Daily Operations

**Morning Workflow**:
```bash
just health                 # Check system status
just extract-incremental org-name  # Get latest changes
just analyze               # Process new data
```

**Weekly Workflow**:
```bash
just cache-status          # Review cache health
just git-refresh org-name  # Refresh repositories
just pipeline org-name 7   # Weekly comprehensive analysis
```

**Monthly Workflow**:
```bash
just cache-clean           # Cleanup old cache
just pipeline org-name 30  # Monthly trend analysis
just benchmark-extraction org-name  # Performance review
```

### Performance Optimization

**Storage Management**:
- Monitor `.git_cache/` size growth
- Clean up unused organizations regularly
- Consider storage expansion for large organizations

**Network Optimization**:
- Run large extractions during off-peak hours
- Use incremental updates for daily operations
- Batch multiple organizations if needed

**Resource Planning**:
- 100 repositories ≈ 2-5 GB storage
- Initial clone: 15-30 minutes
- Incremental updates: 2-5 minutes
- Analysis processing: 10-20 minutes

---

## 🔗 Integration Points

### Analysis Pipeline Integration
```bash
just extract org-name 7     # Git-based extraction
just analyze org_prs.csv    # Compatible with existing analysis
just generate-reports       # Standard report generation
```

### CI/CD Integration
```bash
# Automated daily analysis
0 8 * * * cd /path/to/project && just extract-incremental org-name
0 9 * * * cd /path/to/project && just analyze && just generate-reports
```

### Custom Workflows
```bash
# Custom analysis pipeline
just extract org-name 14
python custom_analysis.py org_commits.csv org_prs.csv
just generate-reports custom_results.csv
```

---

## 📚 Related Documentation

- **[Git-Based Architecture](../architecture/git-based-extraction.md)** - System design and components
- **[Git Cache Issues](../troubleshooting/git-cache-issues.md)** - Troubleshooting guide
- **[System Architecture](../architecture/system-architecture.md)** - Overall system design
- **[Justfile Usage](../justfile-usage.md)** - Command reference

---

**🎯 The git-based extraction workflow delivers enterprise-scale analysis with minimal API dependencies, providing reliable and efficient data collection for engineering impact analytics.**