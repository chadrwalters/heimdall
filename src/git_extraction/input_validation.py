"""Input validation for git operations to prevent security vulnerabilities."""

import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """Validates inputs for git operations and data processing."""
    
    # GitHub organization/repository name constraints
    GITHUB_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-_.]){0,38}$')
    
    # Linear ticket ID pattern (more restrictive)
    LINEAR_TICKET_PATTERN = re.compile(r'^[A-Z]{2,10}-\d{1,6}$')
    
    # Safe commit message patterns (avoid ReDoS)
    SAFE_COMMIT_MESSAGE_PATTERN = re.compile(r'^[^\x00-\x08\x0B\x0C\x0E-\x1F\x7F]*$')
    
    # Maximum lengths to prevent DoS
    MAX_ORG_NAME_LENGTH = 39
    MAX_REPO_NAME_LENGTH = 100
    MAX_COMMIT_MESSAGE_LENGTH = 65536  # 64KB
    MAX_PR_TITLE_LENGTH = 256
    
    @classmethod
    def validate_organization_name(cls, org: str) -> str:
        """Validate GitHub organization name.
        
        Args:
            org: Organization name to validate
            
        Returns:
            Validated organization name
            
        Raises:
            ValidationError: If validation fails
        """
        if not org or not isinstance(org, str):
            raise ValidationError("Organization name must be a non-empty string")
        
        if len(org) > cls.MAX_ORG_NAME_LENGTH:
            raise ValidationError(f"Organization name too long (max {cls.MAX_ORG_NAME_LENGTH} chars)")
        
        # Check for path traversal attempts
        if '..' in org or '/' in org or '\\' in org:
            raise ValidationError("Organization name contains invalid path characters")
        
        # Validate against GitHub naming rules
        if not cls.GITHUB_NAME_PATTERN.match(org):
            raise ValidationError("Organization name contains invalid characters")
        
        return org.strip().lower()
    
    @classmethod
    def validate_repository_name(cls, repo: str) -> str:
        """Validate GitHub repository name.
        
        Args:
            repo: Repository name to validate
            
        Returns:
            Validated repository name
            
        Raises:
            ValidationError: If validation fails
        """
        if not repo or not isinstance(repo, str):
            raise ValidationError("Repository name must be a non-empty string")
        
        if len(repo) > cls.MAX_REPO_NAME_LENGTH:
            raise ValidationError(f"Repository name too long (max {cls.MAX_REPO_NAME_LENGTH} chars)")
        
        # Check for path traversal attempts
        if '..' in repo or '/' in repo or '\\' in repo:
            raise ValidationError("Repository name contains invalid path characters")
        
        # Validate against GitHub naming rules
        if not cls.GITHUB_NAME_PATTERN.match(repo):
            raise ValidationError("Repository name contains invalid characters")
        
        return repo.strip()
    
    @classmethod
    def validate_commit_message(cls, message: str) -> str:
        """Validate commit message for safety.
        
        Args:
            message: Commit message to validate
            
        Returns:
            Validated commit message
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(message, str):
            raise ValidationError("Commit message must be a string")
        
        if len(message) > cls.MAX_COMMIT_MESSAGE_LENGTH:
            logger.warning(f"Commit message truncated (was {len(message)} chars)")
            message = message[:cls.MAX_COMMIT_MESSAGE_LENGTH]
        
        # Check for control characters that could cause issues
        if not cls.SAFE_COMMIT_MESSAGE_PATTERN.match(message):
            raise ValidationError("Commit message contains unsafe control characters")
        
        return message.strip()
    
    @classmethod
    def validate_pr_title(cls, title: str) -> str:
        """Validate PR title for safety.
        
        Args:
            title: PR title to validate
            
        Returns:
            Validated PR title
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(title, str):
            raise ValidationError("PR title must be a string")
        
        if len(title) > cls.MAX_PR_TITLE_LENGTH:
            logger.warning(f"PR title truncated (was {len(title)} chars)")
            title = title[:cls.MAX_PR_TITLE_LENGTH]
        
        return title.strip()
    
    @classmethod
    def validate_linear_ticket_id(cls, ticket_id: str) -> Optional[str]:
        """Validate Linear ticket ID format.
        
        Args:
            ticket_id: Linear ticket ID to validate
            
        Returns:
            Validated ticket ID or None if invalid
        """
        if not ticket_id or not isinstance(ticket_id, str):
            return None
        
        ticket_id = ticket_id.strip().upper()
        
        if cls.LINEAR_TICKET_PATTERN.match(ticket_id):
            return ticket_id
        
        return None
    
    @classmethod
    def validate_file_path(cls, file_path: str, base_path: Optional[str] = None) -> str:
        """Validate file path for safety.
        
        Args:
            file_path: File path to validate
            base_path: Optional base path to constrain within
            
        Returns:
            Validated file path
            
        Raises:
            ValidationError: If validation fails
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("File path must be a non-empty string")
        
        # Normalize path
        normalized_path = os.path.normpath(file_path)
        
        # Check for path traversal attempts
        if '..' in normalized_path or normalized_path.startswith('/'):
            raise ValidationError("File path contains path traversal sequences")
        
        # If base path provided, ensure we stay within it
        if base_path:
            base_path = os.path.normpath(base_path)
            full_path = os.path.join(base_path, normalized_path)
            
            # Ensure resolved path is within base path
            if not os.path.commonpath([base_path, full_path]) == base_path:
                raise ValidationError("File path escapes base directory")
        
        return normalized_path
    
    @classmethod
    def sanitize_regex_input(cls, pattern: str) -> str:
        """Sanitize regex input to prevent ReDoS attacks.
        
        Args:
            pattern: Regex pattern to sanitize
            
        Returns:
            Sanitized pattern
        """
        if not isinstance(pattern, str):
            return ""
        
        # Limit pattern length
        if len(pattern) > 1000:
            logger.warning("Regex pattern truncated to prevent ReDoS")
            pattern = pattern[:1000]
        
        # Remove potentially dangerous regex constructs
        dangerous_patterns = [
            r'\(\?\<\!',  # Negative lookbehind
            r'\(\?\<\=',  # Positive lookbehind
            r'\(\?\!',    # Negative lookahead (some cases)
            r'\*\+',      # Nested quantifiers
            r'\+\*',      # Nested quantifiers
            r'\{\d+,\}',  # Unbounded quantifiers
        ]
        
        for dangerous in dangerous_patterns:
            if re.search(dangerous, pattern):
                logger.warning(f"Removed dangerous regex construct: {dangerous}")
                pattern = re.sub(dangerous, '', pattern)
        
        return pattern


def validate_git_operation_inputs(org: str, repo: str) -> tuple[str, str]:
    """Validate inputs for git operations.
    
    Args:
        org: Organization name
        repo: Repository name
        
    Returns:
        Tuple of validated (org, repo)
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        validated_org = InputValidator.validate_organization_name(org)
        validated_repo = InputValidator.validate_repository_name(repo)
        return validated_org, validated_repo
    except ValidationError as e:
        logger.error(f"Input validation failed: {e}")
        raise
