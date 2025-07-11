"""Utility functions for git-based data extraction."""

import logging
import re
from typing import Optional

from .input_validation import InputValidator

logger = logging.getLogger(__name__)


class ExtractionUtils:
    """Utility functions for extracting data from git and GitHub."""
    
    # Compiled regex patterns for better performance
    PR_NUMBER_PATTERNS = [
        re.compile(r'#(\d+)'),
        re.compile(r'Merge pull request #(\d+)'),
        re.compile(r'\(#(\d+)\)')
    ]
    
    LINEAR_TICKET_PATTERN = re.compile(r'([A-Z]+-\d+)')
    
    CO_AUTHOR_PATTERN = re.compile(r'Co-authored-by: ([^<]+<[^>]+>)')
    
    AI_ASSISTANCE_PATTERNS = [
        'copilot', 'claude', 'cursor', 'generated', 
        'ai-assisted', 'ai generated', 'ai-powered'
    ]
    
    @classmethod
    def extract_pr_number(cls, message: str) -> Optional[str]:
        """Extract PR number from commit message.
        
        Args:
            message: Commit message
            
        Returns:
            PR number or None
        """
        if not message or not isinstance(message, str):
            return None
        
        # Sanitize input to prevent ReDoS
        message = InputValidator.sanitize_regex_input(message)
        
        for pattern in cls.PR_NUMBER_PATTERNS:
            match = pattern.search(message)
            if match:
                return match.group(1)
        
        return None
    
    @classmethod
    def extract_linear_ticket_id(cls, text: str) -> Optional[str]:
        """Extract Linear ticket ID from text.
        
        Args:
            text: Text to search for Linear ticket ID
            
        Returns:
            Linear ticket ID or None
        """
        if not text or not isinstance(text, str):
            return None
        
        # Sanitize input to prevent ReDoS
        text = InputValidator.sanitize_regex_input(text)
        
        match = cls.LINEAR_TICKET_PATTERN.search(text.upper())
        if match:
            ticket_id = match.group(1)
            # Validate the extracted ticket ID
            return InputValidator.validate_linear_ticket_id(ticket_id)
        
        return None
    
    @classmethod
    def extract_co_authors(cls, message: str) -> str:
        """Extract co-authors from commit message.
        
        Args:
            message: Commit message
            
        Returns:
            Semicolon-separated co-authors string
        """
        if not message or not isinstance(message, str):
            return ''
        
        # Sanitize input to prevent ReDoS
        message = InputValidator.sanitize_regex_input(message)
        
        co_authors = cls.CO_AUTHOR_PATTERN.findall(message)
        return ';'.join(co_authors) if co_authors else ''
    
    @classmethod
    def detect_ai_assistance(cls, message: str, co_authors: str = '') -> bool:
        """Detect if AI assistance was used.
        
        Args:
            message: Commit message
            co_authors: Co-authors string
            
        Returns:
            True if AI assistance detected
        """
        if not message:
            return False
        
        text = (message + ' ' + (co_authors or '')).lower()
        
        # Use any() for efficient short-circuit evaluation
        return any(pattern in text for pattern in cls.AI_ASSISTANCE_PATTERNS)
    
    @classmethod
    def sanitize_commit_data(cls, commit_data: dict, config) -> dict:
        """Sanitize commit data for safety.
        
        Args:
            commit_data: Raw commit data dictionary
            config: Configuration instance
            
        Returns:
            Sanitized commit data
        """
        if not isinstance(commit_data, dict):
            return commit_data
        
        # Create a copy to avoid modifying original
        sanitized = commit_data.copy()
        
        # Sanitize commit message if enabled
        if config.sanitize_commit_messages and 'message' in sanitized:
            try:
                sanitized['message'] = InputValidator.validate_commit_message(
                    sanitized['message']
                )
            except Exception as e:
                logger.warning(f"Failed to sanitize commit message: {e}")
                sanitized['message'] = "[Sanitized commit message]"
        
        # Extract metadata using utility functions
        message = sanitized.get('message', '')
        
        if 'pr_number' not in sanitized:
            sanitized['pr_number'] = cls.extract_pr_number(message)
        
        if 'linear_ticket_id' not in sanitized:
            sanitized['linear_ticket_id'] = cls.extract_linear_ticket_id(message)
        
        if 'co_authors' not in sanitized:
            sanitized['co_authors'] = cls.extract_co_authors(message)
        
        if 'ai_assisted' not in sanitized:
            sanitized['ai_assisted'] = cls.detect_ai_assistance(
                message, sanitized.get('co_authors', '')
            )
        
        return sanitized
    
    @classmethod
    def batch_process_commits(cls, commits: list, batch_size: int, processor_func) -> list:
        """Process commits in batches to manage memory usage.
        
        Args:
            commits: List of commits to process
            batch_size: Size of each batch
            processor_func: Function to process each batch
            
        Returns:
            List of processed results
        """
        results = []
        
        for i in range(0, len(commits), batch_size):
            batch = commits[i:i + batch_size]
            try:
                batch_results = processor_func(batch)
                results.extend(batch_results)
            except Exception as e:
                logger.error(f"Failed to process batch {i//batch_size + 1}: {e}")
                continue
        
        return results
    
    @classmethod
    def validate_git_response_data(cls, data: dict) -> bool:
        """Validate git response data for completeness.
        
        Args:
            data: Git response data dictionary
            
        Returns:
            True if data is valid
        """
        required_fields = ['sha', 'message', 'author_name', 'committed_date']
        
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data or data[field] is None:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate SHA format
        sha = data.get('sha', '')
        if not isinstance(sha, str) or len(sha) != 40:
            logger.warning(f"Invalid SHA format: {sha}")
            return False
        
        return True
