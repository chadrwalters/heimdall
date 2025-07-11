#!/bin/bash
# Extract commit data from all organization repositories

# Source utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils.sh"

# Configuration
OUTPUT_FILE="${OUTPUT_FILE:-org_commits.csv}"
REPOS_FILE="${REPOS_FILE:-repos.json}"
DAYS_BACK="${DAYS_BACK:-7}"
MAX_RETRIES=3

# CSV header
CSV_HEADER="Repository,SHA,Author_Login,Author_Email,Author_Name,Committer_Login,Committer_Email,Date,Message,URL,PR_Number,Files_Changed,Additions,Deletions,Is_Merge_Commit,Co_Authors"

# Function to extract PR number from commit message
extract_pr_number() {
    local message="$1"
    
    # Look for patterns like (#123), #123, or Merge pull request #123
    if echo "$message" | grep -qE '#[0-9]+'; then
        echo "$message" | grep -oE '#[0-9]+' | grep -oE '[0-9]+' | head -1
    else
        echo ""
    fi
}

# Function to extract co-authors from commit message
extract_co_authors() {
    local message="$1"
    
    # Look for Co-authored-by: patterns
    local co_authors=$(echo "$message" | grep -oE 'Co-authored-by: [^<]+<[^>]+>' | \
                       sed 's/Co-authored-by: //' | tr '\n' ';')
    
    # Remove trailing semicolon
    echo "${co_authors%;}"
}

# Function to check if AI tool was used (simple pattern matching)
detect_ai_assistance() {
    local message="$1"
    local co_authors="$2"
    
    # Check for common AI tool patterns
    if echo "$message $co_authors" | grep -qiE 'copilot|claude|cursor|generated|ai-assisted'; then
        echo "true"
    else
        echo "false"
    fi
}

# Function to fetch commits for a single repository
fetch_repo_commits() {
    local repo="$1"
    local start_date="$2"
    local end_date="$3"
    local temp_file=$(mktemp)
    local page=1
    local per_page=100
    
    echo "Processing repository: $repo"
    
    while true; do
        show_progress $page 10 "Fetching commits page $page..."
        
        # Check cache for this page
        local cache_file=$(get_cache_path "commits" "${repo}_page_${page}")
        local cached_data=$(get_cached_data "$cache_file" 86400)  # 24 hours TTL
        
        if [ $? -eq 0 ]; then
            echo " (cached)"
            local commits="$cached_data"
        else
            # Fetch commits using GitHub API
            local commits=$(gh api \
                -H "Accept: application/vnd.github+json" \
                -H "X-GitHub-Api-Version: 2022-11-28" \
                "/repos/${GITHUB_ORG}/${repo}/commits?since=${start_date}&until=${end_date}&per_page=${per_page}&page=${page}" 2>&1)
        
            # Check for rate limit
            if echo "$commits" | grep -q "rate limit"; then
                handle_rate_limit 0 || continue
            fi
            
            # Check for errors
            if echo "$commits" | grep -q "Not Found"; then
                echo "Warning: Repository $repo not found or no access" >&2
                break
            fi
            
            # Check for empty repository
            if echo "$commits" | grep -q "Git Repository is empty"; then
                echo "Info: Repository $repo is empty, skipping..." >&2
                break
            fi
            
            # Check for other errors but avoid false positives from valid JSON
            if echo "$commits" | grep -qE "^Error|HTTP [45][0-9][0-9]|\"message\".*\"error\""; then
                echo "Error fetching commits for $repo: $commits" >&2
                break
            fi
            
            # Validate JSON before processing
            if ! echo "$commits" | jq empty 2>/dev/null; then
                echo "Warning: Invalid JSON response for $repo, skipping..." >&2
                break
            fi
            
            # Cache the commits for this page
            cache_response "$cache_file" "$commits" 86400
        fi
        
        # Check if we got any commits
        local commit_count=$(echo "$commits" | jq 'length' 2>/dev/null || echo "0")
        if [ -z "$commit_count" ] || [ "$commit_count" -eq 0 ] 2>/dev/null; then
            break
        fi
        
        # Process each commit
        echo "$commits" | jq -c '.[]' | while read -r commit; do
            local sha=$(echo "$commit" | jq -r '.sha // ""' | cut -c1-7)
            local full_sha=$(echo "$commit" | jq -r '.sha // ""')
            local author_login=$(echo "$commit" | jq -r '.author.login // ""')
            local author_email=$(echo "$commit" | jq -r '.commit.author.email // ""')
            local author_name=$(echo "$commit" | jq -r '.commit.author.name // ""' | sed 's/,/;/g')
            local committer_login=$(echo "$commit" | jq -r '.committer.login // ""')
            local committer_email=$(echo "$commit" | jq -r '.commit.committer.email // ""')
            local date=$(echo "$commit" | jq -r '.commit.author.date // ""')
            local message=$(echo "$commit" | jq -r '.commit.message // ""' | sed 's/,/;/g' | sed 's/"//g' | tr '\n' ' ')
            local url=$(echo "$commit" | jq -r '.html_url // ""')
            
            # Check if it's a merge commit
            local parent_count=$(echo "$commit" | jq '.parents | length' 2>/dev/null || echo "0")
            local is_merge="false"
            if [ -n "$parent_count" ] && [ "$parent_count" -gt 1 ] 2>/dev/null; then
                is_merge="true"
            fi
            
            # Extract PR number
            local pr_number=$(extract_pr_number "$message")
            
            # Extract co-authors
            local co_authors=$(extract_co_authors "$message")
            
            # Fetch commit details for file statistics
            local commit_details=$(gh api \
                -H "Accept: application/vnd.github+json" \
                -H "X-GitHub-Api-Version: 2022-11-28" \
                "/repos/${GITHUB_ORG}/${repo}/commits/${full_sha}" 2>/dev/null)
            
            local files_changed=0
            local additions=0
            local deletions=0
            
            if [ -n "$commit_details" ]; then
                files_changed=$(echo "$commit_details" | jq '.files | length' 2>/dev/null || echo "0")
                additions=$(echo "$commit_details" | jq '.stats.additions // 0' 2>/dev/null || echo "0")
                deletions=$(echo "$commit_details" | jq '.stats.deletions // 0' 2>/dev/null || echo "0")
            fi
            
            # Truncate message if too long
            if [ ${#message} -gt 200 ]; then
                message="${message:0:197}..."
            fi
            
            # Write to temp file
            echo "${repo},${full_sha},${author_login},${author_email},${author_name},${committer_login},${committer_email},${date},${message},${url},${pr_number},${files_changed},${additions},${deletions},${is_merge},${co_authors}" >> "$temp_file"
        done
        
        # Check if there are more pages
        if [ -z "$commit_count" ] || [ "$commit_count" -lt "$per_page" ] 2>/dev/null; then
            break
        fi
        
        ((page++))
    done
    
    echo ""  # New line after progress
    
    # Append to main output file
    if [ -s "$temp_file" ]; then
        cat "$temp_file" >> "$OUTPUT_FILE"
    fi
    rm -f "$temp_file"
}

# Main execution
main() {
    # Check prerequisites
    check_gh_auth
    validate_env
    
    # Check if repos file exists
    if [ ! -f "$REPOS_FILE" ]; then
        echo "Error: Repository list file not found: $REPOS_FILE" >&2
        echo "Run list_repos.sh first to generate the repository list." >&2
        exit 1
    fi
    
    # Load configuration and state
    load_config
    
    # Determine date range
    local end_date=$(date -u "+%Y-%m-%dT%H:%M:%SZ")
    local start_date
    
    if [ -n "$LAST_RUN_DATE" ]; then
        # Incremental update - start from last run date minus 1 day for overlap
        start_date=$(date -u -d "${LAST_RUN_DATE} - 1 day" "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || \
                     date -u -v-1d -j -f "%Y-%m-%dT%H:%M:%SZ" "$LAST_RUN_DATE" "+%Y-%m-%dT%H:%M:%SZ")
        echo "Incremental update from: $start_date"
    else
        # Full extraction for DAYS_BACK days
        start_date=$(days_ago "$DAYS_BACK")
        start_date=$(format_date "$start_date")
        echo "Full extraction from: $start_date"
    fi
    
    # Initialize output file with header (or append if incremental)
    if [ -n "$LAST_RUN_DATE" ] && [ -f "$OUTPUT_FILE" ]; then
        echo "Appending to existing file: $OUTPUT_FILE"
    else
        echo "$CSV_HEADER" > "$OUTPUT_FILE"
    fi
    
    # Get list of repositories
    local repos=$(jq -r '.[].name' "$REPOS_FILE")
    local total_repos=$(echo "$repos" | wc -l | tr -d ' ')
    local current_repo=0
    
    echo "Extracting commits from $total_repos repositories..."
    echo "Date range: $start_date to $end_date"
    echo ""
    
    # Process each repository
    while IFS= read -r repo; do
        ((current_repo++))
        echo "[$current_repo/$total_repos] $repo"
        fetch_repo_commits "$repo" "$start_date" "$end_date"
    done <<< "$repos"
    
    # Update state file
    update_state
    
    # Summary
    local total_commits=$(($(wc -l < "$OUTPUT_FILE") - 1))  # Subtract header
    local merge_commits=$(grep -c ",true," "$OUTPUT_FILE" || echo "0")
    local commits_with_pr=$(grep -cE ',[0-9]+,' "$OUTPUT_FILE" || echo "0")
    
    echo ""
    echo "Summary:"
    echo "  Total commits extracted: $total_commits"
    echo "  Merge commits: $merge_commits"
    echo "  Commits linked to PRs: $commits_with_pr"
    echo "  Output saved to: $OUTPUT_FILE"
}

# Run main function
main "$@"