#!/bin/bash
# Master script to run all extraction processes

# Source utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils.sh"

# Configuration
DAYS_BACK="${DAYS_BACK:-7}"
CONFIG_DIR="${CONFIG_DIR:-config}"
OUTPUT_DIR="${OUTPUT_DIR:-.}"

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Run GitHub data extraction for organization repositories.

OPTIONS:
    -o, --org ORGANIZATION     GitHub organization name (required)
    -d, --days DAYS           Number of days to look back (default: 7)
    -i, --incremental         Run incremental update based on last run
    -c, --config-dir DIR      Configuration directory (default: config)
    -O, --output-dir DIR      Output directory (default: current directory)
    -h, --help               Display this help message

EXAMPLES:
    # Initial full extraction for 7 days
    $0 --org mycompany

    # Full extraction for 30 days
    $0 --org mycompany --days 30

    # Incremental update since last run
    $0 --org mycompany --incremental

ENVIRONMENT VARIABLES:
    GITHUB_ORG               Alternative to --org flag
    DAYS_BACK               Alternative to --days flag
    CONFIG_DIR              Alternative to --config-dir flag
    OUTPUT_DIR              Alternative to --output-dir flag
EOF
}

# Parse command line arguments
INCREMENTAL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--org)
            GITHUB_ORG="$2"
            shift 2
            ;;
        -d|--days)
            DAYS_BACK="$2"
            shift 2
            ;;
        -i|--incremental)
            INCREMENTAL=true
            shift
            ;;
        -c|--config-dir)
            CONFIG_DIR="$2"
            shift 2
            ;;
        -O|--output-dir)
            OUTPUT_DIR="$2"
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

# Export environment variables
export GITHUB_ORG
export DAYS_BACK
export CONFIG_DIR
export OUTPUT_DIR

# Check prerequisites
check_gh_auth
validate_env

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Load state for incremental updates
if [ "$INCREMENTAL" == "true" ]; then
    load_config
    if [ -z "$LAST_RUN_DATE" ]; then
        echo "Warning: No previous run found. Running full extraction instead."
        INCREMENTAL=false
    else
        echo "Running incremental update from: $LAST_RUN_DATE"
    fi
fi

# Start time
START_TIME=$(date +%s)

echo "=========================================="
echo "GitHub Data Extraction"
echo "=========================================="
echo "Organization: $GITHUB_ORG"
echo "Configuration: $CONFIG_DIR"
echo "Output directory: $OUTPUT_DIR"
if [ "$INCREMENTAL" == "true" ]; then
    echo "Mode: Incremental update"
else
    echo "Mode: Full extraction ($DAYS_BACK days)"
fi
echo "=========================================="
echo ""

# Step 1: List repositories
echo "Step 1: Fetching repository list..."
echo "------------------------------------------"
OUTPUT_FILE="${OUTPUT_DIR}/repos.json" "${SCRIPT_DIR}/list_repos.sh"
if [ $? -ne 0 ]; then
    echo "Error: Failed to fetch repository list" >&2
    exit 1
fi
echo ""

# Step 2: Extract PRs
echo "Step 2: Extracting Pull Requests..."
echo "------------------------------------------"
REPOS_FILE="${OUTPUT_DIR}/repos.json" \
OUTPUT_FILE="${OUTPUT_DIR}/org_prs.csv" \
"${SCRIPT_DIR}/extract_prs.sh"
if [ $? -ne 0 ]; then
    echo "Error: Failed to extract PRs" >&2
    exit 1
fi
echo ""

# Step 3: Extract commits
echo "Step 3: Extracting Commits..."
echo "------------------------------------------"
REPOS_FILE="${OUTPUT_DIR}/repos.json" \
OUTPUT_FILE="${OUTPUT_DIR}/org_commits.csv" \
"${SCRIPT_DIR}/extract_commits.sh"
if [ $? -ne 0 ]; then
    echo "Error: Failed to extract commits" >&2
    exit 1
fi
echo ""

# Calculate execution time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

# Final summary
echo "=========================================="
echo "Extraction Complete!"
echo "=========================================="
echo "Execution time: ${MINUTES}m ${SECONDS}s"
echo ""
echo "Output files:"
echo "  - ${OUTPUT_DIR}/repos.json"
echo "  - ${OUTPUT_DIR}/org_prs.csv"
echo "  - ${OUTPUT_DIR}/org_commits.csv"
echo ""

# Update Python state file for compatibility
if command -v python3 >/dev/null 2>&1; then
    python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.config.state_manager import StateManager
    sm = StateManager('${CONFIG_DIR}/analysis_state.json')
    print('State file updated for Python compatibility')
except Exception as e:
    print(f'Warning: Could not update Python state file: {e}')
"
fi

echo "Next steps:"
echo "  1. Run the analysis scripts to process this data"
echo "  2. For incremental updates, run: $0 --org $GITHUB_ORG --incremental"
echo ""