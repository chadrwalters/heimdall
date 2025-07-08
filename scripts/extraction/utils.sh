#!/bin/bash
# Common utility functions for GitHub data extraction scripts

# Detect OS and set date command appropriately
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    date_cmd() {
        if [ "$1" == "-d" ]; then
            # Convert GNU date -d syntax to macOS date -v syntax
            shift
            date -j -v"$1" "+%Y-%m-%dT%H:%M:%SZ"
        else
            date "$@"
        fi
    }
else
    # Linux
    date_cmd() {
        date "$@"
    }
fi

# Format date for GitHub API (ISO 8601)
format_date() {
    local date_str="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        date -j -f "%Y-%m-%d" "$date_str" "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "$date_str"
    else
        date -d "$date_str" "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "$date_str"
    fi
}

# Get date N days ago
days_ago() {
    local days="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        date -v-"${days}d" "+%Y-%m-%d"
    else
        date -d "${days} days ago" "+%Y-%m-%d"
    fi
}

# Progress indicator
show_progress() {
    local current="$1"
    local total="$2"
    local message="$3"
    local percent=$((current * 100 / total))
    printf "\r%-50s [%3d%%]" "$message" "$percent"
}

# Rate limit handler with exponential backoff
handle_rate_limit() {
    local retry_count="${1:-0}"
    local max_retries=5
    local base_wait=2
    
    if [ "$retry_count" -ge "$max_retries" ]; then
        echo "Error: Max retries reached. Exiting." >&2
        return 1
    fi
    
    local wait_time=$((base_wait ** retry_count))
    echo "Rate limit hit. Waiting ${wait_time} seconds before retry..." >&2
    sleep "$wait_time"
    return 0
}

# Check if gh CLI is authenticated
check_gh_auth() {
    if ! gh auth status >/dev/null 2>&1; then
        echo "Error: GitHub CLI is not authenticated. Run 'gh auth login' first." >&2
        exit 1
    fi
}

# Load configuration and state
load_config() {
    local config_dir="${CONFIG_DIR:-config}"
    local state_file="${config_dir}/analysis_state.json"
    
    if [ -f "$state_file" ]; then
        export LAST_RUN_DATE=$(jq -r '.last_run_date // empty' "$state_file" 2>/dev/null)
    fi
}

# Update state file with new run date
update_state() {
    local config_dir="${CONFIG_DIR:-config}"
    local state_file="${config_dir}/analysis_state.json"
    local current_date=$(date -u "+%Y-%m-%dT%H:%M:%SZ")
    
    if [ -f "$state_file" ]; then
        # Update existing state file
        jq --arg date "$current_date" '.last_run_date = $date' "$state_file" > "${state_file}.tmp" && \
        mv "${state_file}.tmp" "$state_file"
    else
        # Create new state file
        echo "{\"last_run_date\": \"$current_date\", \"processed_pr_ids\": [], \"processed_commit_shas\": [], \"total_records_processed\": 0}" > "$state_file"
    fi
}

# Validate required environment variables
validate_env() {
    if [ -z "$GITHUB_ORG" ]; then
        echo "Error: GITHUB_ORG environment variable not set" >&2
        echo "Usage: GITHUB_ORG=your-org-name $0" >&2
        exit 1
    fi
}

# Export functions for use in other scripts
export -f date_cmd format_date days_ago show_progress handle_rate_limit check_gh_auth load_config update_state validate_env