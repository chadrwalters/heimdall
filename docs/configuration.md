# Configuration Guide

North Star Metrics uses a flexible configuration system based on Pydantic settings that allows environment-specific overrides through environment variables.

## How Configuration Works

The application configuration is now environment-specific and can be overridden at multiple levels:

1. **Default Values**: Hard-coded defaults in the Pydantic schemas
2. **Environment Variables**: Override defaults through environment variables
3. **Environment Files**: Load settings from `.env` files

## Environment Variables

All configuration values can be overridden using environment variables. The variable names follow a predictable pattern:

### Core Settings
- `NORTH_STAR_ENV`: Environment (development, staging, production, test)
- `NORTH_STAR_DEBUG`: Enable debug mode (true/false)
- `ANTHROPIC_API_KEY`: Anthropic API key (required)
- `GITHUB_TOKEN`: GitHub token (required)
- `LINEAR_API_KEY`: Linear API key (optional)

### Processing Limits
- `DIFF_LENGTH_LIMIT`: Maximum diff length to process (default: 4000)
- `CACHE_SIZE_DEFAULT`: Default cache size (default: 1000)
- `MAX_WORKERS_DEFAULT`: Default number of worker threads (default: 5)
- `MAX_MEMORY_MB`: Maximum memory usage in MB (default: 2048)
- `THREAD_TIMEOUT_SECONDS`: Thread timeout in seconds (default: 300)

### API Configuration
- `API_RATE_LIMIT_REQUESTS_PER_MINUTE`: API rate limit (default: 60)
- `API_TIMEOUT_SECONDS`: API timeout (default: 30)
- `API_RETRY_ATTEMPTS`: Number of retry attempts (default: 3)

### Pricing Configuration
- `CLAUDE_INPUT_PRICE_PER_1K`: Input token price per 1K tokens (default: 0.003)
- `CLAUDE_OUTPUT_PRICE_PER_1K`: Output token price per 1K tokens (default: 0.015)
- `DAILY_COST_WARNING_THRESHOLD`: Daily cost warning threshold (default: 100.0)
- `MONTHLY_COST_LIMIT`: Monthly cost limit (default: 1000.0)

### Security Settings
- `API_KEY_MIN_LENGTH`: Minimum API key length (default: 10)
- `SESSION_TIMEOUT_MINUTES`: Session timeout (default: 60)
- `MAX_FAILED_ATTEMPTS`: Maximum failed login attempts (default: 5)

### Metrics Configuration
- `COMPLEXITY_WEIGHT`: Complexity weight in impact scoring (default: 0.4)
- `RISK_WEIGHT`: Risk weight in impact scoring (default: 0.5)
- `CLARITY_WEIGHT`: Clarity weight in impact scoring (default: 0.1)
- `HIGH_IMPACT_THRESHOLD`: High impact threshold (default: 7.0)

### Logging Configuration
- `DEFAULT_LOG_LEVEL`: Default log level (default: INFO)
- `MAX_LOG_FILE_SIZE_MB`: Maximum log file size (default: 100)
- `ENABLE_STRUCTURED_LOGGING`: Enable structured JSON logging (default: true)

## Environment-Specific Configuration

### Development Environment
```bash
export NORTH_STAR_ENV=development
export NORTH_STAR_DEBUG=true
export DEFAULT_LOG_LEVEL=DEBUG
export MAX_WORKERS_DEFAULT=3
export CACHE_SIZE_DEFAULT=500
```

### Production Environment
```bash
export NORTH_STAR_ENV=production
export NORTH_STAR_DEBUG=false
export DEFAULT_LOG_LEVEL=INFO
export MAX_WORKERS_DEFAULT=10
export CACHE_SIZE_DEFAULT=2000
export MAX_MEMORY_MB=4096
export DAILY_COST_WARNING_THRESHOLD=500.0
export MONTHLY_COST_LIMIT=5000.0
```

### Testing Environment
```bash
export NORTH_STAR_ENV=test
export MAX_WORKERS_DEFAULT=1
export CACHE_SIZE_DEFAULT=100
export API_TIMEOUT_SECONDS=5
export THREAD_TIMEOUT_SECONDS=10
```

## Using .env Files

Create a `.env` file in the project root to set environment variables:

```bash
# Copy the example file
cp .env.example .env

# Edit with your settings
NORTH_STAR_ENV=development
ANTHROPIC_API_KEY=sk-ant-your-key-here
GITHUB_TOKEN=ghp_your-token-here
MAX_WORKERS_DEFAULT=5
CACHE_SIZE_DEFAULT=1000
```

## Configuration Validation

The configuration system includes comprehensive validation:

- **API Key Formats**: Validates API key formats for different providers
- **Range Validation**: Ensures numeric values are within acceptable ranges
- **Required Fields**: Validates required fields for production environments
- **Dependency Validation**: Ensures related settings are compatible (e.g., max > default)

## Accessing Configuration in Code

### Using the Settings Object
```python
from src.config.schemas import load_settings

settings = load_settings()
max_workers = settings.processing_limits.max_workers_default
api_timeout = settings.processing_limits.api_timeout_seconds
```

### Using the Constants (Backward Compatibility)
```python
from src.config.constants import processing_limits, pricing

max_workers = processing_limits.MAX_WORKERS_DEFAULT
input_price = pricing.CLAUDE_INPUT_PRICE_PER_1K
```

## Environment Variable Priority

The configuration system respects the following priority order:

1. **Environment Variables**: Highest priority
2. **`.env` File**: Medium priority
3. **Default Values**: Lowest priority

This allows for flexible deployment scenarios where production values can override development defaults.

## Configuration Schema

The complete configuration schema is defined in `src/config/schemas.py` using Pydantic models:

- `NorthStarSettings`: Main settings container
- `ProcessingLimitsConfig`: Processing and performance limits
- `PricingConfig`: API pricing configuration
- `SecurityConfig`: Security-related settings
- `LoggingConfig`: Logging configuration
- `MetricsConfig`: Analysis metrics configuration

## Best Practices

1. **Use Environment Variables**: Set sensitive values like API keys through environment variables
2. **Environment-Specific Settings**: Use different configurations for development/staging/production
3. **Validate Settings**: Always validate configuration before deployment
4. **Document Changes**: Update this guide when adding new configuration options
5. **Version Control**: Never commit actual API keys or sensitive values

## Migration from Hard-Coded Constants

The previous hard-coded constants in `src/config/constants.py` have been converted to use the configuration system:

- All `Final` values are now properties that read from the configuration
- Backward compatibility is maintained through singleton instances
- Environment variables can override any setting
- Configuration is validated at startup

This provides production-ready configuration management while maintaining existing API compatibility.