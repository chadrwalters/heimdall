# 🤖 Automation Guide

Simple automation for daily metrics updates.

---

## 📋 Daily Update Script

The `scripts/daily_update.sh` script automates the complete workflow:
1. **Extract data** from GitHub organization
2. **Generate charts** from extracted data
3. **Log results** with timestamps and stats

### Quick Usage

```bash
# Set organization name
export ORGANIZATION_NAME=your-org-name

# Run daily update (30 days by default)
./scripts/daily_update.sh
```

### Configuration

Configure via environment variables:

```bash
# Required
export ORGANIZATION_NAME=your-org-name       # GitHub organization

# Optional
export METRICS_DAYS=30                        # Days to extract (default: 30)
export METRICS_OUTPUT_DIR=charts              # Output directory (default: charts)
export GITHUB_TOKEN=your_token                # GitHub API token (or in .env)
```

### Example: Custom Configuration

```bash
# Extract last 7 days, output to weekly_reports/
ORGANIZATION_NAME=my-org \
METRICS_DAYS=7 \
METRICS_OUTPUT_DIR=weekly_reports \
./scripts/daily_update.sh
```

---

## ⏰ Scheduled Automation

### Using Cron (Linux/macOS)

Run metrics update automatically every day at 6 AM:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths to match your installation)
0 6 * * * cd /path/to/heimdall && ORGANIZATION_NAME=your-org ./scripts/daily_update.sh >> logs/daily_update.log 2>&1
```

#### Cron Schedule Examples

```bash
# Every day at 6 AM
0 6 * * * cd /path/to/project && ORGANIZATION_NAME=org ./scripts/daily_update.sh

# Every Monday at 9 AM (weekly reports)
0 9 * * 1 cd /path/to/project && ORGANIZATION_NAME=org METRICS_DAYS=7 ./scripts/daily_update.sh

# First day of month at 10 AM (monthly reports)
0 10 1 * * cd /path/to/project && ORGANIZATION_NAME=org METRICS_DAYS=30 ./scripts/daily_update.sh
```

### Environment Variables in Cron

Create a `.env` file with your configuration:

```bash
# .env
ORGANIZATION_NAME=your-org-name
GITHUB_TOKEN=your_github_token
LINEAR_API_KEY=your_linear_key  # Optional
METRICS_DAYS=30
```

Then source it in your cron job:

```bash
# Cron entry
0 6 * * * cd /path/to/project && source .env && ./scripts/daily_update.sh >> logs/daily.log 2>&1
```

### Using Task Scheduler (Windows)

1. **Open Task Scheduler**
2. **Create Basic Task**
   - Name: "GitHub Metrics Daily Update"
   - Trigger: Daily at 6:00 AM
3. **Action**: Start a program
   - Program: `C:\path\to\git-bash.exe` or `wsl.exe`
   - Arguments: `-c "cd /path/to/project && ORGANIZATION_NAME=your-org ./scripts/daily_update.sh"`
4. **Conditions**: Uncheck "Start only if on AC power" if running on laptop

---

## 📊 Output

### Generated Files

After each run, you'll have:

```
charts/
├── commits_d_count_stacked.png       # Daily commits by developer
├── commits_d_count_cumulative.png    # Cumulative daily commits
├── commits_d_size_cumulative.png     # Cumulative lines changed
├── commits_w_count_stacked.png       # Weekly commits by developer
├── commits_w_count_cumulative.png    # Cumulative weekly commits
├── commits_w_size_cumulative.png     # Cumulative weekly lines
├── prs_d_count_stacked.png           # Daily PRs by developer
├── prs_d_count_cumulative.png        # Cumulative daily PRs
├── prs_d_size_cumulative.png         # Cumulative daily PR size
├── prs_w_count_stacked.png           # Weekly PRs by developer
├── prs_w_count_cumulative.png        # Cumulative weekly PRs
└── prs_w_size_cumulative.png         # Cumulative weekly PR size

src/
├── org_commits.csv                   # Extracted commit data
└── org_prs.csv                       # Extracted PR data
```

### Logging

Redirect output to log files for monitoring:

```bash
# Create logs directory
mkdir -p logs

# Run with logging
./scripts/daily_update.sh >> logs/daily_update.log 2>&1

# View recent logs
tail -f logs/daily_update.log

# Check last run
tail -20 logs/daily_update.log
```

---

## 🔍 Monitoring

### Check Last Run Status

```bash
# Check if script succeeded (exit code 0)
echo $?

# View log file
tail -50 logs/daily_update.log | grep -E "(INFO|ERROR|WARN)"

# Check generated charts
ls -lh charts/*.png

# Verify data freshness
stat -c '%y' src/org_commits.csv   # Linux
stat -f '%Sm' src/org_commits.csv  # macOS
```

### Error Handling

The script will:
- ✅ Exit with error code if extraction fails
- ✅ Exit with error code if chart generation fails
- ✅ Log all errors with timestamps
- ✅ Validate required environment variables

Monitor for errors:

```bash
# Check for errors in logs
grep ERROR logs/daily_update.log

# Alert on failures (example)
if ! ./scripts/daily_update.sh; then
    echo "Daily update failed!" | mail -s "Metrics Update Failed" you@example.com
fi
```

---

## 🚀 Advanced Usage

### Multiple Organizations

```bash
# Create wrapper script for multiple orgs
cat > scripts/update_all_orgs.sh << 'EOF'
#!/usr/bin/env bash
for org in org1 org2 org3; do
    echo "Updating $org..."
    ORGANIZATION_NAME=$org \
    METRICS_OUTPUT_DIR="charts_$org" \
    ./scripts/daily_update.sh
done
EOF

chmod +x scripts/update_all_orgs.sh
```

### Custom Time Periods

```bash
# Weekly report (last 7 days)
ORGANIZATION_NAME=my-org METRICS_DAYS=7 METRICS_OUTPUT_DIR=weekly ./scripts/daily_update.sh

# Monthly report (last 30 days)
ORGANIZATION_NAME=my-org METRICS_DAYS=30 METRICS_OUTPUT_DIR=monthly ./scripts/daily_update.sh

# Quarterly report (last 90 days)
ORGANIZATION_NAME=my-org METRICS_DAYS=90 METRICS_OUTPUT_DIR=quarterly ./scripts/daily_update.sh
```

### Post-Processing

Add custom steps after chart generation:

```bash
#!/usr/bin/env bash
# Custom automation script

# Run daily update
./scripts/daily_update.sh

# Copy to shared directory
cp charts/*.png /shared/metrics/latest/

# Generate summary report
echo "Report generated at $(date)" > /shared/metrics/last_update.txt

# Upload to cloud storage (example)
# aws s3 sync charts/ s3://my-bucket/metrics/
```

---

## ⚙️ Troubleshooting

### Common Issues

**Script fails with "ORGANIZATION_NAME not set"**
- Set environment variable: `export ORGANIZATION_NAME=your-org`
- Or add to `.env` file

**Permission denied**
- Make script executable: `chmod +x scripts/daily_update.sh`

**Charts not generated**
- Check CSV files exist in `src/` directory
- Verify extraction completed successfully
- Check logs for errors

**Cron job not running**
- Use full paths in cron entries
- Check cron logs: `grep CRON /var/log/syslog` (Linux)
- Ensure environment variables are set in cron context

---

## 📝 Best Practices

### Recommended Schedules

- **Daily Updates**: Run at 6 AM (before team starts work)
- **Weekly Reports**: Monday morning (review previous week)
- **Monthly Reports**: 1st of month (monthly review meetings)

### Data Retention

Keep historical data for trend analysis:

```bash
# Archive old data before update
DATE=$(date +%Y%m%d)
mkdir -p archives/$DATE
cp src/org_*.csv archives/$DATE/
cp charts/*.png archives/$DATE/
```

### Notification Integration

```bash
# Send notification after successful update
if ./scripts/daily_update.sh; then
    # Slack notification example
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"Daily metrics updated successfully"}' \
        YOUR_SLACK_WEBHOOK_URL
fi
```

---

**🎯 Quick Start**: Set `ORGANIZATION_NAME` and run `./scripts/daily_update.sh` to get started!
