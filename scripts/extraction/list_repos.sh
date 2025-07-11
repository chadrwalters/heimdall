#!/bin/bash
# List all active repositories in the organization

# Source utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils.sh"

# Configuration
OUTPUT_FILE="${OUTPUT_FILE:-repos.json}"
INCLUDE_ARCHIVED="${INCLUDE_ARCHIVED:-false}"

# Function to fetch all repositories with pagination
fetch_all_repos() {
    local org="$1"
    local page=1
    local per_page=100
    local temp_file=$(mktemp)
    
    echo "[]" > "$temp_file"
    
    echo "Fetching repositories from organization: $org"
    
    while true; do
        echo -n "Fetching page $page... "
        
        # Fetch repositories for current page
        local response=$(gh api \
            -H "Accept: application/vnd.github+json" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            "/orgs/${org}/repos?per_page=${per_page}&page=${page}&type=all" 2>&1)
        
        # Check for rate limit
        if echo "$response" | grep -q "rate limit"; then
            handle_rate_limit 0 || exit 1
            continue
        fi
        
        # Check for errors
        if echo "$response" | grep -q "error"; then
            echo "Error: $response" >&2
            rm -f "$temp_file"
            exit 1
        fi
        
        # Parse response
        local repo_count=$(echo "$response" | jq 'length')
        echo "$repo_count repositories"
        
        # Break if no more repositories
        if [ "$repo_count" -eq 0 ]; then
            break
        fi
        
        # Filter and append to results
        if [ "$INCLUDE_ARCHIVED" == "false" ]; then
            # Exclude archived repositories
            echo "$response" | jq '[.[] | select(.archived == false)]' > "${temp_file}.page"
        else
            echo "$response" | jq '.' > "${temp_file}.page"
        fi
        
        # Merge with existing results
        jq -s 'add' "$temp_file" "${temp_file}.page" > "${temp_file}.new"
        mv "${temp_file}.new" "$temp_file"
        rm -f "${temp_file}.page"
        
        # Increment page
        ((page++))
        
        # Break if we got less than per_page (last page)
        if [ "$repo_count" -lt "$per_page" ]; then
            break
        fi
    done
    
    # Extract relevant fields and sort by activity
    echo "Processing repository data..."
    jq '[.[] | {
        name: .name,
        full_name: .full_name,
        description: .description,
        html_url: .html_url,
        clone_url: .clone_url,
        created_at: .created_at,
        updated_at: .updated_at,
        pushed_at: .pushed_at,
        size: .size,
        language: .language,
        default_branch: .default_branch,
        archived: .archived,
        disabled: .disabled,
        private: .private,
        has_issues: .has_issues,
        has_projects: .has_projects,
        has_wiki: .has_wiki
    }] | sort_by(.pushed_at) | reverse' "$temp_file" > "$OUTPUT_FILE"
    
    rm -f "$temp_file"
}

# Main execution
main() {
    # Check prerequisites
    check_gh_auth
    validate_env
    
    # Fetch repositories
    fetch_all_repos "$GITHUB_ORG"
    
    # Summary
    local total_repos=$(jq 'length' "$OUTPUT_FILE")
    local active_repos=$(jq '[.[] | select(.archived == false)] | length' "$OUTPUT_FILE")
    local languages=$(jq -r '[.[].language] | unique | map(select(. != null)) | join(", ")' "$OUTPUT_FILE")
    
    echo ""
    echo "Summary:"
    echo "  Total repositories: $total_repos"
    echo "  Active repositories: $active_repos"
    echo "  Languages: $languages"
    echo "  Output saved to: $OUTPUT_FILE"
}

# Run main function
main "$@"