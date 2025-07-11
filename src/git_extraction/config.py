"""Configuration management for git-based extraction."""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GitExtractionConfig:
    """Configuration for git-based extraction operations."""
    
    # Git repository settings
    clone_depth: int = 100
    max_commits_per_query: int = 1000
    single_branch_clone: bool = True
    
    # Performance settings
    max_concurrent_repos: int = 5
    memory_limit_mb: int = 1024
    batch_size: int = 50
    
    # Rate limiting settings
    api_rate_limit_buffer: int = 100
    initial_backoff_delay: float = 1.0
    max_backoff_delay: float = 60.0
    backoff_factor: float = 2.0
    max_retries: int = 3
    
    # Cache settings
    cache_dir: str = ".git_cache"
    enable_compression: bool = False
    cache_ttl_hours: int = 24
    
    # Security settings
    validate_inputs: bool = True
    sanitize_commit_messages: bool = True
    max_commit_message_length: int = 65536
    
    # Logging settings
    log_level: str = "INFO"
    log_git_operations: bool = True
    log_api_calls: bool = True
    
    @classmethod
    def from_environment(cls) -> 'GitExtractionConfig':
        """Create configuration from environment variables.
        
        Returns:
            Configuration instance with values from environment
        """
        config = cls()
        
        # Git repository settings
        config.clone_depth = int(os.getenv('GIT_CLONE_DEPTH', config.clone_depth))
        config.max_commits_per_query = int(os.getenv('GIT_MAX_COMMITS', config.max_commits_per_query))
        config.single_branch_clone = os.getenv('GIT_SINGLE_BRANCH', 'true').lower() == 'true'
        
        # Performance settings
        config.max_concurrent_repos = int(os.getenv('GIT_MAX_CONCURRENT', config.max_concurrent_repos))
        config.memory_limit_mb = int(os.getenv('GIT_MEMORY_LIMIT_MB', config.memory_limit_mb))
        config.batch_size = int(os.getenv('GIT_BATCH_SIZE', config.batch_size))
        
        # Rate limiting settings
        config.api_rate_limit_buffer = int(os.getenv('API_RATE_LIMIT_BUFFER', config.api_rate_limit_buffer))
        config.initial_backoff_delay = float(os.getenv('API_INITIAL_BACKOFF', config.initial_backoff_delay))
        config.max_backoff_delay = float(os.getenv('API_MAX_BACKOFF', config.max_backoff_delay))
        config.backoff_factor = float(os.getenv('API_BACKOFF_FACTOR', config.backoff_factor))
        config.max_retries = int(os.getenv('API_MAX_RETRIES', config.max_retries))
        
        # Cache settings
        config.cache_dir = os.getenv('GIT_CACHE_DIR', config.cache_dir)
        config.enable_compression = os.getenv('GIT_ENABLE_COMPRESSION', 'false').lower() == 'true'
        config.cache_ttl_hours = int(os.getenv('GIT_CACHE_TTL_HOURS', config.cache_ttl_hours))
        
        # Security settings
        config.validate_inputs = os.getenv('GIT_VALIDATE_INPUTS', 'true').lower() == 'true'
        config.sanitize_commit_messages = os.getenv('GIT_SANITIZE_MESSAGES', 'true').lower() == 'true'
        config.max_commit_message_length = int(os.getenv('GIT_MAX_MESSAGE_LENGTH', config.max_commit_message_length))
        
        # Logging settings
        config.log_level = os.getenv('GIT_LOG_LEVEL', config.log_level).upper()
        config.log_git_operations = os.getenv('GIT_LOG_OPERATIONS', 'true').lower() == 'true'
        config.log_api_calls = os.getenv('GIT_LOG_API_CALLS', 'true').lower() == 'true'
        
        return config
    
    def validate(self) -> None:
        """Validate configuration values.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if self.clone_depth <= 0:
            raise ValueError("clone_depth must be positive")
        
        if self.max_commits_per_query <= 0:
            raise ValueError("max_commits_per_query must be positive")
        
        if self.max_concurrent_repos <= 0:
            raise ValueError("max_concurrent_repos must be positive")
        
        if self.memory_limit_mb <= 0:
            raise ValueError("memory_limit_mb must be positive")
        
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        
        if self.api_rate_limit_buffer < 0:
            raise ValueError("api_rate_limit_buffer must be non-negative")
        
        if self.initial_backoff_delay <= 0:
            raise ValueError("initial_backoff_delay must be positive")
        
        if self.max_backoff_delay <= 0:
            raise ValueError("max_backoff_delay must be positive")
        
        if self.backoff_factor <= 1:
            raise ValueError("backoff_factor must be greater than 1")
        
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        if self.cache_ttl_hours <= 0:
            raise ValueError("cache_ttl_hours must be positive")
        
        if self.max_commit_message_length <= 0:
            raise ValueError("max_commit_message_length must be positive")
        
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"Invalid log_level: {self.log_level}")
    
    def configure_logging(self) -> None:
        """Configure logging based on settings."""
        log_level = getattr(logging, self.log_level)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Adjust third-party library logging
        if not self.log_git_operations:
            logging.getLogger('git').setLevel(logging.WARNING)
        
        if not self.log_api_calls:
            logging.getLogger('requests').setLevel(logging.WARNING)
            logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'clone_depth': self.clone_depth,
            'max_commits_per_query': self.max_commits_per_query,
            'single_branch_clone': self.single_branch_clone,
            'max_concurrent_repos': self.max_concurrent_repos,
            'memory_limit_mb': self.memory_limit_mb,
            'batch_size': self.batch_size,
            'api_rate_limit_buffer': self.api_rate_limit_buffer,
            'initial_backoff_delay': self.initial_backoff_delay,
            'max_backoff_delay': self.max_backoff_delay,
            'backoff_factor': self.backoff_factor,
            'max_retries': self.max_retries,
            'cache_dir': self.cache_dir,
            'enable_compression': self.enable_compression,
            'cache_ttl_hours': self.cache_ttl_hours,
            'validate_inputs': self.validate_inputs,
            'sanitize_commit_messages': self.sanitize_commit_messages,
            'max_commit_message_length': self.max_commit_message_length,
            'log_level': self.log_level,
            'log_git_operations': self.log_git_operations,
            'log_api_calls': self.log_api_calls
        }
