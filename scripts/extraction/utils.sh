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

# Cache management functions
CACHE_DIR=".cache"

# Get cache file path for a resource
get_cache_path() {
    local resource_type="$1"  # repos, prs, commits
    local resource_key="$2"   # repo name, pr_id, sha, etc.
    echo "${CACHE_DIR}/${resource_type}/${resource_key}.json"
}

# Check if cache entry is valid (not expired)
is_cache_valid() {
    local cache_file="$1"
    local ttl_seconds="$2"
    
    if [ ! -f "$cache_file" ]; then
        return 1
    fi
    
    local cached_at=$(jq -r '.cached_at // empty' "$cache_file" 2>/dev/null)
    if [ -z "$cached_at" ]; then
        return 1
    fi
    
    local cached_timestamp=$(date -d "$cached_at" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$cached_at" +%s 2>/dev/null)
    local current_timestamp=$(date +%s)
    local age_seconds=$((current_timestamp - cached_timestamp))
    
    [ "$age_seconds" -lt "$ttl_seconds" ]
}

# Get cached data if valid
get_cached_data() {
    local cache_file="$1"
    local ttl_seconds="$2"
    
    if is_cache_valid "$cache_file" "$ttl_seconds"; then
        jq -r '.data' "$cache_file" 2>/dev/null
        return 0
    fi
    return 1
}

# Cache API response
cache_response() {
    local cache_file="$1"
    local data="$2"
    local ttl_seconds="$3"
    local etag="${4:-}"
    
    # Create cache directory if it doesn't exist
    mkdir -p "$(dirname "$cache_file")"
    
    # Create cache entry
    local cache_entry=$(jq -n \
        --arg cached_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg ttl_seconds "$ttl_seconds" \
        --arg etag "$etag" \
        --argjson data "$data" \
        '{
            cached_at: $cached_at,
            ttl_seconds: ($ttl_seconds | tonumber),
            etag: $etag,
            data: $data
        }')
    
    echo "$cache_entry" > "$cache_file"
}

# Get cache statistics
get_cache_stats() {
    local cache_dir="${CACHE_DIR}"
    local total_files=0
    local total_size=0
    
    if [ -d "$cache_dir" ]; then
        total_files=$(find "$cache_dir" -name "*.json" | wc -l | tr -d ' ')
        total_size=$(du -sm "$cache_dir" 2>/dev/null | cut -f1 || echo "0")
    fi
    
    echo "Cache files: $total_files, Size: ${total_size}MB"
}

# Clean expired cache entries
clean_cache() {
    local cache_dir="${CACHE_DIR}"
    local cleaned_count=0
    
    if [ ! -d "$cache_dir" ]; then
        return 0
    fi
    
    # Find all cache files and check if they're expired
    find "$cache_dir" -name "*.json" | while read -r cache_file; do
        local cached_at=$(jq -r '.cached_at // empty' "$cache_file" 2>/dev/null)
        local ttl_seconds=$(jq -r '.ttl_seconds // 3600' "$cache_file" 2>/dev/null)
        
        if [ -n "$cached_at" ] && ! is_cache_valid "$cache_file" "$ttl_seconds"; then
            rm -f "$cache_file"
            ((cleaned_count++))
        fi
    done
    
    echo "Cleaned $cleaned_count expired cache entries"
}

# Export functions for use in other scripts
export -f date_cmd format_date days_ago show_progress handle_rate_limit check_gh_auth load_config update_state validate_env
export -f get_cache_path is_cache_valid get_cached_data cache_response get_cache_stats clean_cache