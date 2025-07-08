#!/bin/bash
# Extract PR data from all organization repositories

# Source utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils.sh"

# Configuration
OUTPUT_FILE="${OUTPUT_FILE:-org_prs.csv}"
REPOS_FILE="${REPOS_FILE:-repos.json}"
DAYS_BACK="${DAYS_BACK:-7}"
MAX_RETRIES=3

# CSV header
CSV_HEADER="Repository,PR_Number,PR_ID,Title,Author,State,Created_At,Merged_At,Closed_At,URL,Base_Branch,Head_Branch,Files_Changed,Additions,Deletions,Linear_Ticket_ID,Has_Linear_Ticket"

# Function to extract Linear ticket ID from PR title or body
extract_linear_ticket() {
    local title="$1"
    local body="$2"
    
    # Look for patterns like ENG-1234, PROJ-567, etc.
    local ticket_pattern='[A-Z]+-[0-9]+'
    
    # Check title first
    if echo "$title" | grep -qE "$ticket_pattern"; then
        echo "$title" | grep -oE "$ticket_pattern" | head -1
        return
    fi
    
    # Check body if not found in title
    if echo "$body" | grep -qE "$ticket_pattern"; then
        echo "$body" | grep -oE "$ticket_pattern" | head -1
        return
    fi
    
    echo ""
}

# Function to fetch PR details including files changed
fetch_pr_details() {
    local repo="$1"
    local pr_number="$2"
    local retry_count=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        # Fetch PR details
        local pr_details=$(gh api \
            -H "Accept: application/vnd.github+json" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            "/repos/${GITHUB_ORG}/${repo}/pulls/${pr_number}" 2>&1)
        
        # Check for rate limit
        if echo "$pr_details" | grep -q "rate limit"; then
            handle_rate_limit $retry_count || return 1
            ((retry_count++))
            continue
        fi
        
        # Check for errors
        if echo "$pr_details" | grep -q "error"; then
            echo "Error fetching PR #${pr_number} details: $pr_details" >&2
            return 1
        fi
        
        # Extract fields
        echo "$pr_details" | jq -r '{
            changed_files: .changed_files,
            additions: .additions,
            deletions: .deletions,
            body: .body
        }'
        return 0
    done
    
    return 1
}

# Function to fetch PRs for a single repository
fetch_repo_prs() {
    local repo="$1"
    local start_date="$2"
    local end_date="$3"
    local temp_file=$(mktemp)
    
    echo "Processing repository: $repo"
    
    # Use gh pr list with pagination
    local page=1
    local has_more=true
    
    while [ "$has_more" == "true" ]; do
        local prs=$(gh pr list \
            --repo "${GITHUB_ORG}/${repo}" \
            --state all \
            --limit 100 \
            --json number,id,title,author,state,createdAt,mergedAt,closedAt,url,baseRefName,headRefName \
            --search "created:>=${start_date}" 2>&1)
        
        # Check for errors
        if echo "$prs" | grep -q "error"; then
            echo "Error fetching PRs for $repo: $prs" >&2
            rm -f "$temp_file"
            return 1
        fi
        
        # Process each PR
        echo "$prs" | jq -c '.[]' | while read -r pr; do
            local pr_number=$(echo "$pr" | jq -r '.number')
            local pr_id=$(echo "$pr" | jq -r '.id')
            local title=$(echo "$pr" | jq -r '.title // ""' | sed 's/,/;/g' | sed 's/"//g')
            local author=$(echo "$pr" | jq -r '.author.login // ""')
            local state=$(echo "$pr" | jq -r '.state // ""')
            local created_at=$(echo "$pr" | jq -r '.createdAt // ""')
            local merged_at=$(echo "$pr" | jq -r '.mergedAt // ""')
            local closed_at=$(echo "$pr" | jq -r '.closedAt // ""')
            local url=$(echo "$pr" | jq -r '.url // ""')
            local base_branch=$(echo "$pr" | jq -r '.baseRefName // ""')
            local head_branch=$(echo "$pr" | jq -r '.headRefName // ""')
            
            # Skip if created before start date
            if [ -n "$created_at" ] && [ "$created_at" < "$start_date" ]; then
                continue
            fi
            
            # Fetch additional PR details (files changed, body)
            show_progress $pr_number 100 "Fetching PR #$pr_number details..."
            local details=$(fetch_pr_details "$repo" "$pr_number")
            
            if [ $? -eq 0 ]; then
                local files_changed=$(echo "$details" | jq -r '.changed_files // 0')
                local additions=$(echo "$details" | jq -r '.additions // 0')
                local deletions=$(echo "$details" | jq -r '.deletions // 0')
                local body=$(echo "$details" | jq -r '.body // ""')
                
                # Extract Linear ticket ID
                local linear_ticket=$(extract_linear_ticket "$title" "$body")
                local has_linear="false"
                if [ -n "$linear_ticket" ]; then
                    has_linear="true"
                fi
                
                # Write to temp file
                echo "${repo},${pr_number},${pr_id},${title},${author},${state},${created_at},${merged_at},${closed_at},${url},${base_branch},${head_branch},${files_changed},${additions},${deletions},${linear_ticket},${has_linear}" >> "$temp_file"
            else
                # Write with empty details if fetch failed
                echo "${repo},${pr_number},${pr_id},${title},${author},${state},${created_at},${merged_at},${closed_at},${url},${base_branch},${head_branch},0,0,0,," >> "$temp_file"
            fi
        done
        
        # Check if there are more pages (simplified - gh pr list doesn't have built-in pagination info)
        local pr_count=$(echo "$prs" | jq 'length')
        if [ "$pr_count" -lt 100 ]; then
            has_more=false
        else
            ((page++))
        fi
    done
    
    # Append to main output file
    cat "$temp_file" >> "$OUTPUT_FILE"
    rm -f "$temp_file"
    
    echo ""  # New line after progress
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
    
    # Initialize output file with header
    echo "$CSV_HEADER" > "$OUTPUT_FILE"
    
    # Get list of repositories
    local repos=$(jq -r '.[].name' "$REPOS_FILE")
    local total_repos=$(echo "$repos" | wc -l | tr -d ' ')
    local current_repo=0
    
    echo "Extracting PRs from $total_repos repositories..."
    echo "Date range: $start_date to $end_date"
    echo ""
    
    # Process each repository
    while IFS= read -r repo; do
        ((current_repo++))
        echo "[$current_repo/$total_repos] $repo"
        fetch_repo_prs "$repo" "$start_date" "$end_date"
    done <<< "$repos"
    
    # Update state file
    update_state
    
    # Summary
    local total_prs=$(($(wc -l < "$OUTPUT_FILE") - 1))  # Subtract header
    local prs_with_linear=$(grep -c ",true$" "$OUTPUT_FILE" || echo "0")
    local compliance_rate=0
    if [ "$total_prs" -gt 0 ]; then
        compliance_rate=$((prs_with_linear * 100 / total_prs))
    fi
    
    echo ""
    echo "Summary:"
    echo "  Total PRs extracted: $total_prs"
    echo "  PRs with Linear tickets: $prs_with_linear"
    echo "  Process compliance rate: ${compliance_rate}%"
    echo "  Output saved to: $OUTPUT_FILE"
}

# Run main function
main "$@"