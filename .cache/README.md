# Cache Directory

This directory contains cached GitHub API responses to minimize API calls and avoid rate limits.

## Structure

```
.cache/
├── repos/           # Repository metadata and lists
│   ├── {org}.json   # Organization repository list (TTL: 6h)
│   └── meta_{repo}.json  # Repository metadata (TTL: 24h)
├── prs/             # Pull request data
│   └── {repo}/
│       ├── list_p{page}.json     # PR lists by page (TTL: 1h)
│       └── details_{pr_id}.json  # PR details (TTL: 24h for open, permanent for closed)
└── commits/         # Commit data (permanent cache)
    └── {repo}/
        └── {sha}.json  # Commit details (permanent - immutable)
```

## TTL (Time To Live) Rules

- **Repository Lists**: 6 hours (moderate change frequency)
- **Repository Metadata**: 24 hours (low change frequency)
- **PR Lists**: 1 hour (active development)
- **PR Details**: 24 hours for open PRs, permanent for closed/merged
- **Commit Details**: Permanent (immutable once created)

## Cache Management

```bash
just cache-status    # Show cache statistics
just cache-validate  # Verify cache integrity
just cache-clean     # Remove expired entries
just cache-rebuild   # Force fresh extraction
```

## Cache Files

Each cache file contains:
- `cached_at`: ISO timestamp when cached
- `ttl_seconds`: Time-to-live in seconds
- `data`: The actual API response data
- `etag`: GitHub API etag for conditional requests (when available)