#!/bin/bash
# North Star Metrics - Scheduling Script
# 
# This script can be used with cron to schedule regular analysis runs.
# Example crontab entry (daily at 6 AM):
# 0 6 * * * /path/to/north-star-metrics/scripts/schedule_analysis.sh

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_DIR}/logs"
OUTPUT_DIR="${PROJECT_DIR}/scheduled-output"
CONFIG_FILE="${PROJECT_DIR}/config/schedule.conf"

# Default configuration
DEFAULT_ORG="${GITHUB_ORG:-your-org-name}"
DEFAULT_MODE="incremental"
DEFAULT_LOG_LEVEL="INFO"
DEFAULT_MAX_WORKERS="5"

# Load configuration if it exists
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Use environment variables or defaults
ORG="${SCHEDULE_ORG:-$DEFAULT_ORG}"
MODE="${SCHEDULE_MODE:-$DEFAULT_MODE}"
LOG_LEVEL="${SCHEDULE_LOG_LEVEL:-$DEFAULT_LOG_LEVEL}"
MAX_WORKERS="${SCHEDULE_MAX_WORKERS:-$DEFAULT_MAX_WORKERS}"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$OUTPUT_DIR"

# Generate log filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/scheduled_analysis_${TIMESTAMP}.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to handle errors
handle_error() {
    local exit_code=$?
    log "ERROR: Scheduled analysis failed with exit code $exit_code"
    
    # Optional: Send notification (uncomment and configure as needed)
    # notify_failure "$exit_code"
    
    exit $exit_code
}

# Optional notification function (customize as needed)
notify_failure() {
    local exit_code=$1
    log "NOTIFY: Sending failure notification"
    
    # Example: Send email notification
    # echo "North Star analysis failed at $(date) with exit code $exit_code" | \
    #     mail -s "North Star Analysis Failed" admin@company.com
    
    # Example: Send to Slack
    # curl -X POST -H 'Content-type: application/json' \
    #     --data '{"text":"North Star analysis failed with exit code '$exit_code'"}' \
    #     "$SLACK_WEBHOOK_URL"
}

# Optional notification function for success
notify_success() {
    local results_file=$1
    log "NOTIFY: Sending success notification"
    
    # Example: Send summary to Slack or email
    # if [ -f "$results_file" ]; then
    #     local record_count=$(wc -l < "$results_file")
    #     echo "North Star analysis completed successfully. Processed $record_count records." | \
    #         mail -s "North Star Analysis Completed" team@company.com
    # fi
}

# Set error handler
trap handle_error ERR

# Main execution
main() {
    log "Starting scheduled North Star analysis"
    log "Organization: $ORG"
    log "Mode: $MODE"
    log "Output directory: $OUTPUT_DIR"
    log "Log file: $LOG_FILE"
    
    # Check if Python virtual environment exists
    if [ ! -d "${PROJECT_DIR}/.venv" ]; then
        log "ERROR: Python virtual environment not found at ${PROJECT_DIR}/.venv"
        log "Please run 'just setup' or 'uv venv && uv pip sync pyproject.toml' first"
        exit 1
    fi
    
    # Activate virtual environment
    source "${PROJECT_DIR}/.venv/bin/activate"
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Check required environment variables
    if [ -z "${GITHUB_TOKEN:-}" ]; then
        log "ERROR: GITHUB_TOKEN environment variable is required"
        exit 1
    fi
    
    if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
        log "ERROR: ANTHROPIC_API_KEY environment variable is required"
        exit 1
    fi
    
    log "Environment validation passed"
    
    # Run the analysis
    log "Executing main pipeline..."
    python main.py \
        --org "$ORG" \
        --mode "$MODE" \
        --output-dir "$OUTPUT_DIR" \
        --log-file "$LOG_FILE" \
        --log-level "$LOG_LEVEL" \
        --max-workers "$MAX_WORKERS"
    
    # Check if results were generated
    RESULTS_FILE="${OUTPUT_DIR}/unified_pilot_data.csv"
    if [ -f "$RESULTS_FILE" ]; then
        local record_count=$(tail -n +2 "$RESULTS_FILE" | wc -l)
        log "SUCCESS: Analysis completed. Generated $record_count records"
        
        # Optional: Send success notification
        # notify_success "$RESULTS_FILE"
        
        # Optional: Cleanup old results (keep last 30 days)
        log "Cleaning up old results..."
        find "$OUTPUT_DIR" -name "unified_pilot_data_*.csv" -mtime +30 -delete 2>/dev/null || true
        find "$LOG_DIR" -name "scheduled_analysis_*.log" -mtime +7 -delete 2>/dev/null || true
        
    else
        log "WARNING: No results file generated"
    fi
    
    log "Scheduled analysis completed successfully"
}

# Print usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Schedule and run North Star metrics analysis.

OPTIONS:
    -o, --org ORG         GitHub organization (default: $DEFAULT_ORG)
    -m, --mode MODE       Analysis mode: incremental, pilot, full (default: $DEFAULT_MODE)
    -l, --log-level LEVEL Log level: DEBUG, INFO, WARNING, ERROR (default: $DEFAULT_LOG_LEVEL)
    -w, --workers NUM     Max parallel workers (default: $DEFAULT_MAX_WORKERS)
    -h, --help           Show this help message

ENVIRONMENT VARIABLES:
    GITHUB_TOKEN         GitHub personal access token (required)
    ANTHROPIC_API_KEY    Anthropic API key (required)
    LINEAR_API_KEY       Linear API key (optional)
    
    SCHEDULE_ORG         Override default organization
    SCHEDULE_MODE        Override default mode
    SCHEDULE_LOG_LEVEL   Override default log level
    SCHEDULE_MAX_WORKERS Override default max workers

CONFIGURATION FILE:
    Create $CONFIG_FILE to set defaults:
    
    SCHEDULE_ORG="my-company"
    SCHEDULE_MODE="incremental"
    SCHEDULE_LOG_LEVEL="INFO"
    SCHEDULE_MAX_WORKERS="5"

CRON EXAMPLE:
    # Run daily at 6 AM
    0 6 * * * $0 >/dev/null 2>&1
    
    # Run Monday-Friday at 8 AM
    0 8 * * 1-5 $0 >/dev/null 2>&1
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--org)
            ORG="$2"
            shift 2
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        -w|--workers)
            MAX_WORKERS="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

# Run main function
main "$@"