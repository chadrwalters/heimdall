# Git Cache Troubleshooting Guide

## Purpose
Comprehensive troubleshooting guide for git-based extraction system issues, including repository cache problems, performance optimization, and recovery procedures.

## When to Use This
- Git-based extraction is failing or slow
- Repository cache corruption or inconsistencies
- Storage space issues with git cache
- Performance degradation over time

**Keywords:** git cache, repository issues, performance problems, cache corruption, troubleshooting

---

## 🚨 Common Issues & Solutions

### Repository Clone Failures

**Symptoms**:
- "Authentication failed" errors during extraction
- "Repository not found" messages
- Partial repository clones or missing repositories

**Diagnosis**:
```bash
just env-check              # Check GitHub token status
just verify-apis            # Test API connectivity
just git-status             # Check repository health
```

**Solutions**:

**1. Authentication Issues**
```bash
# Check token validity
echo $GITHUB_TOKEN | cut -c1-10  # Should show: ghp_xxxxxx

# Test token permissions
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Update token if expired
export GITHUB_TOKEN=ghp_new_token_here
just extract org-name       # Retry extraction
```

**2. Repository Access Issues**
```bash
# Clean corrupted repositories
just git-cleanup org-name

# Force fresh clone
rm -rf .git_cache/repos/org-name/problem-repo
just extract org-name       # Re-clone specific repositories
```

**3. Network Connectivity Issues**
```bash
# Test network connectivity
ping github.com

# Test git clone directly
git clone https://github.com/org-name/test-repo.git /tmp/test-clone

# If successful, issue is with extraction script
just verify-apis            # Re-test API connections
```

---

### Cache Corruption Issues

**Symptoms**:
- Inconsistent extraction results
- "Not a git repository" errors
- Missing or incomplete commit data
- Extraction suddenly very slow

**Diagnosis**:
```bash
just cache-status           # Check cache state
just git-status             # Repository health check

# Manual repository validation
cd .git_cache/repos/org-name/repo-name
git status                  # Should show clean working directory
git log --oneline -5        # Should show recent commits
```

**Solutions**:

**1. Individual Repository Corruption**
```bash
# Identify corrupted repository
just git-status             # Look for error repositories

# Remove corrupted repository
rm -rf .git_cache/repos/org-name/corrupted-repo

# Re-clone during next extraction
just extract org-name       # Will re-clone missing repositories
```

**2. Systematic Cache Corruption**
```bash
# Nuclear option: complete cache rebuild
just cache-rebuild

# Selective organization cleanup
rm -rf .git_cache/repos/org-name
just extract org-name       # Re-clone entire organization
```

**3. State File Corruption**
```bash
# Clear state files
rm -rf .git_cache/state/org-name_*.json

# Run fresh extraction (will rebuild state)
just extract org-name
```

---

### Performance Degradation

**Symptoms**:
- Extraction taking much longer than usual
- High disk I/O during extraction
- Memory usage growing during extraction
- System becoming unresponsive

**Diagnosis**:
```bash
# Check cache size
just cache-status
du -sh .git_cache/          # Total git cache size

# Check disk space
df -h                       # Available disk space

# Monitor extraction performance
time just extract-incremental org-name
```

**Solutions**:

**1. Large Cache Size**
```bash
# Check cache breakdown
just cache-status           # Detailed cache statistics

# Clean unused organizations
just git-cleanup old-org-name

# Clean API cache
just cache-clean

# If still large, consider storage expansion
```

**2. Repository Size Issues**
```bash
# Identify large repositories
du -sh .git_cache/repos/org-name/* | sort -hr | head -10

# For very large repositories, consider:
# - Increasing shallow clone depth
# - Excluding binary files
# - Repository-specific optimization
```

**3. Incremental Processing Issues**
```bash
# Reset incremental state
rm .git_cache/state/org-name_large-repo.json

# Force full re-analysis
just extract org-name       # Will rebuild incremental state
```

---

### Disk Space Issues

**Symptoms**:
- "No space left on device" errors
- Extraction failing mid-process
- System performance degradation

**Diagnosis**:
```bash
# Check disk usage
df -h                       # Overall disk space
du -sh .git_cache/          # Git cache size
du -sh .cache/              # API cache size

# Find largest repositories
du -sh .git_cache/repos/*/* | sort -hr | head -20
```

**Solutions**:

**1. Cache Cleanup**
```bash
# Step 1: Clean API cache
just cache-clean

# Step 2: Remove unused organizations
ls .git_cache/repos/        # List cached organizations
just git-cleanup unused-org-name

# Step 3: Selective repository cleanup
rm -rf .git_cache/repos/org-name/very-large-repo
```

**2. Storage Optimization**
```bash
# Compress git repositories (experimental)
cd .git_cache/repos/org-name
for repo in */; do
    cd "$repo"
    git gc --aggressive --prune=now
    cd ..
done

# Monitor space savings
du -sh .git_cache/repos/org-name/
```

**3. External Storage**
```bash
# Move git cache to external storage
mv .git_cache /external/drive/git_cache
ln -s /external/drive/git_cache .git_cache

# Verify extraction still works
just cache-status
just extract-incremental org-name
```

---

### State Management Issues

**Symptoms**:
- Extraction always processing full history
- "Last analyzed commit not found" warnings
- Inconsistent incremental behavior

**Diagnosis**:
```bash
# Check state files
ls -la .git_cache/state/

# Examine state file content
cat .git_cache/state/org-name_repo-name.json

# Verify state consistency
just git-status             # Should show last analyzed commits
```

**Solutions**:

**1. Missing State Files**
```bash
# State files missing - normal for first run
just extract org-name       # Will create state files

# Manual state verification
ls .git_cache/state/org-name_*.json | wc -l
ls .git_cache/repos/org-name/ | wc -l
# These numbers should match (one state file per repository)
```

**2. Corrupted State Files**
```bash
# Identify corrupted state files
for file in .git_cache/state/*.json; do
    jq . "$file" >/dev/null || echo "Corrupted: $file"
done

# Remove corrupted state files
rm .git_cache/state/corrupted-file.json

# Rebuild state during next extraction
just extract org-name
```

**3. Inconsistent State**
```bash
# Reset all state for organization
rm .git_cache/state/org-name_*.json

# Run full extraction to rebuild state
just extract org-name       # Will process full history and rebuild state
```

---

## 🔧 Advanced Troubleshooting

### Manual Repository Inspection

**Git Repository Health Check**:
```bash
# Navigate to specific repository
cd .git_cache/repos/org-name/repo-name

# Verify git repository integrity
git fsck --full              # Check repository integrity
git status                   # Should be clean
git remote -v                # Verify remote URLs
git branch -a                # Check available branches
git log --oneline -10        # Recent commits
```

**Repository Update Issues**:
```bash
# Manual repository update
cd .git_cache/repos/org-name/repo-name
git fetch origin             # Fetch latest changes
git status                   # Check for conflicts
git reset --hard origin/main # Force clean state (if needed)
```

### Performance Profiling

**Extraction Performance Analysis**:
```bash
# Time individual components
time just list-repos org-name          # Repository discovery
time git clone <repo-url> /tmp/test    # Clone performance
time just extract-incremental org-name  # Incremental processing

# Monitor system resources during extraction
top -p $(pgrep -f extract_git.py)      # CPU/memory usage
iostat -x 1                            # Disk I/O monitoring
```

**Cache Hit Rate Analysis**:
```bash
# API cache performance
find .cache -name "*.json" -mtime -1 | wc -l    # Recent cache hits

# Git cache freshness
find .git_cache/repos -name ".git" -mtime -1 | wc -l  # Recently updated repos
```

### Network Troubleshooting

**GitHub API Issues**:
```bash
# Test API rate limits
curl -H "Authorization: token $GITHUB_TOKEN" \
     -I https://api.github.com/rate_limit

# Test repository access
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/org-name/repo-name
```

**Git Clone Issues**:
```bash
# Test direct git access
GIT_TRACE=1 git clone https://$GITHUB_TOKEN@github.com/org/repo.git /tmp/test

# Check for proxy issues
git config --global http.proxy         # Should be empty unless using proxy
git config --global https.proxy        # Should be empty unless using proxy
```

---

## 🚀 Recovery Procedures

### Complete System Recovery

**Full Cache Reset** (Nuclear Option):
```bash
# 1. Backup important data
cp -r .git_cache/state/ .git_cache_state_backup/

# 2. Clear all caches
just cache-rebuild

# 3. Verify environment
just env-check
just verify-apis

# 4. Test with small extraction
just extract test-org 1     # Test with 1 day extraction

# 5. Restore full operations
just extract production-org 7
```

### Selective Recovery

**Organization-Specific Reset**:
```bash
# 1. Backup organization state
cp .git_cache/state/org-name_*.json /tmp/state_backup/

# 2. Clean organization cache
just git-cleanup org-name

# 3. Test extraction
just extract org-name 1     # Small test first

# 4. Full extraction
just extract org-name 7     # Production extraction
```

### Emergency Procedures

**Disk Space Emergency**:
```bash
# 1. Immediate space recovery
just cache-clean             # Clean API cache
rm -rf .git_cache/repos/largest-org/  # Remove largest organization

# 2. Continue operations with remaining cache
just extract-incremental remaining-org

# 3. Plan storage expansion or archive old data
```

**Performance Emergency**:
```bash
# 1. Stop current extraction
pkill -f extract_git.py

# 2. Quick performance recovery
just cache-clean
rm -rf .git_cache/repos/problematic-org/

# 3. Resume with clean cache
just extract org-name 1     # Quick test
```

---

## 📊 Monitoring & Prevention

### Regular Health Checks

**Daily Monitoring**:
```bash
# Add to cron job or daily script
just cache-status           # Monitor cache growth
just git-status             # Check repository health
df -h | grep git_cache      # Disk usage monitoring
```

**Weekly Maintenance**:
```bash
# Weekly cleanup routine
just cache-clean             # Clean expired API cache
just git-refresh org-name    # Refresh repositories
du -sh .git_cache/repos/*    # Monitor organization sizes
```

### Preventive Measures

**Storage Management**:
- Monitor `.git_cache/` size growth patterns
- Set up disk space alerts at 80% capacity
- Implement automated cleanup of old organizations
- Consider git cache compression for large installations

**Performance Optimization**:
- Use incremental extractions for daily operations
- Schedule large extractions during off-peak hours
- Monitor extraction time trends
- Optimize repository clone depth based on analysis needs

**System Health**:
- Regular API token rotation
- Network connectivity monitoring
- Git repository integrity checks
- State file validation

---

## 📚 Related Documentation

- **[Git-Based Architecture](../architecture/git-based-extraction.md)** - System design and components
- **[Git Extraction Workflow](../workflows/git-extraction-workflow.md)** - Standard procedures
- **[System Architecture](../architecture/system-architecture.md)** - Overall system design
- **[Common Problems](./common-problems.md)** - General troubleshooting

---

**🛠️ Most git cache issues can be resolved with selective cleanup and re-extraction. The system is designed to be resilient and self-healing through the standard extraction workflows.**