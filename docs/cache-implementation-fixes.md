# Cache Implementation Fixes

## Overview
Fixed several issues identified in the code review of the caching implementation to improve security, reliability, and performance.

## Changes Made

### 1. Security Enhancement: Replaced MD5 with SHA-256
- **Files Changed**: `src/analysis/context_preparer.py`
- **Issue**: MD5 is deprecated and prone to collisions
- **Fix**: Replaced `hashlib.md5()` with `hashlib.sha256()` for cache key generation
- **Impact**: More secure and collision-resistant cache keys

### 2. Race Condition Prevention
- **Files Changed**: `scripts/extraction/utils.sh`
- **Issue**: Direct file writes could cause corruption with concurrent processes
- **Fix**: Implemented atomic writes using temp files and `mv -f`
- **Impact**: Prevents cache file corruption in multi-process scenarios

### 3. Disk Space Management
- **Files Changed**: `scripts/extraction/utils.sh`
- **Issue**: Unbounded cache growth could exhaust disk space
- **Fix**: 
  - Added 500MB default cache size limit (configurable via `MAX_CACHE_SIZE_MB`)
  - Implemented automatic cleanup of oldest files when limit exceeded
  - Added size checking before writing new cache entries
- **Impact**: Prevents runaway disk usage

### 4. Cache Metrics Improvement
- **Files Changed**: `src/analysis/analysis_engine.py`
- **Issue**: Variable named `cache_hits` actually stored cache size
- **Fix**: 
  - Added proper `cache_hits` and `cache_misses` counters
  - Updated cache access points to track hits/misses
  - Added `cache_hit_rate` calculation
  - Renamed size metric to `cache_size`
- **Impact**: Accurate performance monitoring and optimization

### 5. Cache Warming Strategy
- **Files Changed**: 
  - `src/analysis/cache_warmer.py` (new file)
  - `justfile` (added `cache-warm` command)
- **Issue**: Cold start performance could be improved
- **Fix**: 
  - Created `CacheWarmer` class for pre-population
  - Added ability to warm recent PRs
  - Added justfile command for easy warming
- **Impact**: Improved performance for scheduled analyses

## Usage Examples

### Check Cache Status
```bash
just cache-status
```

### Clean Expired Cache Entries
```bash
just cache-clean
```

### Warm Cache for Organization
```bash
just cache-warm my-org 7  # Warm last 7 days of PRs
```

### Set Custom Cache Size Limit
```bash
export MAX_CACHE_SIZE_MB=1000  # 1GB limit
```

## Configuration

### Environment Variables
- `MAX_CACHE_SIZE_MB`: Maximum file cache size in MB (default: 500)
- `CACHE_SIZE_DEFAULT`: In-memory cache entries (default: 1000)
- `CACHE_TTL_SECONDS`: Cache TTL in seconds (default: 3600)

### Cache TTL Settings
- PR lists: 1 hour
- PR details: 24 hours
- Commits: 24 hours
- Analysis results: 1 hour (in-memory)

## Monitoring

The improved metrics now track:
- `cache_hits`: Number of cache hits
- `cache_misses`: Number of cache misses
- `cache_hit_rate`: Percentage of requests served from cache
- `cache_size`: Current number of cached entries

Access these metrics via `AnalysisEngine.get_stats()`.