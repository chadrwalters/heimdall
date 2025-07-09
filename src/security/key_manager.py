"""Secure API key management with encryption and rotation."""

import base64
import hashlib
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class KeySecurityError(Exception):
    """Raised when key security operations fail."""

    pass


class SecureKeyManager:
    """Manages API keys with encryption, validation, and rotation."""

    def __init__(self, master_key_env_var: str = "NORTH_STAR_MASTER_KEY"):
        """
        Initialize the key manager.

        Args:
            master_key_env_var: Environment variable containing the master key
        """
        self.master_key_env_var = master_key_env_var
        self._cipher = None
        self._key_cache = {}
        self._key_metadata = {}

    def _get_cipher(self) -> Fernet:
        """Get or create the encryption cipher."""
        if self._cipher is None:
            master_key = os.getenv(self.master_key_env_var)
            if not master_key:
                # Generate a new master key if none exists
                master_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
                logger.warning(
                    f"No master key found in {self.master_key_env_var}. "
                    f"Generated new key: {master_key}"
                )
                logger.warning("Store this key securely and set it in the environment variable!")

            # Derive encryption key from master key
            from ..config.constants import security_settings

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=security_settings.ENCRYPTION_SALT.encode(),
                iterations=security_settings.PBKDF2_ITERATIONS,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
            self._cipher = Fernet(key)

        return self._cipher

    def encrypt_api_key(self, api_key: str, key_name: str) -> str:
        """
        Encrypt an API key for secure storage.

        Args:
            api_key: Plain text API key
            key_name: Name/identifier for the key

        Returns:
            Encrypted key as base64 string

        Raises:
            KeySecurityError: If encryption fails
        """
        try:
            if not api_key or not isinstance(api_key, str):
                raise KeySecurityError("API key must be a non-empty string")

            cipher = self._get_cipher()
            encrypted_key = cipher.encrypt(api_key.encode())

            # Store metadata
            self._key_metadata[key_name] = {
                "created_at": datetime.now(UTC).isoformat(),
                "last_used": None,
                "usage_count": 0,
                "key_hash": hashlib.sha256(api_key.encode()).hexdigest()[:16],
            }

            logger.info(f"API key '{key_name}' encrypted and stored")
            return base64.urlsafe_b64encode(encrypted_key).decode()

        except Exception as e:
            logger.error(f"Failed to encrypt API key '{key_name}': {e}")
            raise KeySecurityError(f"Encryption failed: {e}")

    def decrypt_api_key(self, encrypted_key: str, key_name: str) -> str:
        """
        Decrypt an API key for use.

        Args:
            encrypted_key: Base64 encoded encrypted key
            key_name: Name/identifier for the key

        Returns:
            Decrypted API key

        Raises:
            KeySecurityError: If decryption fails
        """
        try:
            cipher = self._get_cipher()
            encrypted_data = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted_key = cipher.decrypt(encrypted_data).decode()

            # Update usage metadata
            if key_name in self._key_metadata:
                self._key_metadata[key_name]["last_used"] = datetime.now(UTC).isoformat()
                self._key_metadata[key_name]["usage_count"] += 1

            logger.debug(f"API key '{key_name}' decrypted for use")
            return decrypted_key

        except Exception as e:
            logger.error(f"Failed to decrypt API key '{key_name}': {e}")
            raise KeySecurityError(f"Decryption failed: {e}")

    def validate_api_key(self, api_key: str, key_type: str = "generic") -> bool:
        """
        Validate API key format and structure.

        Args:
            api_key: API key to validate
            key_type: Type of key (anthropic, github, linear)

        Returns:
            True if key appears valid
        """
        if not api_key or not isinstance(api_key, str):
            return False

        # Basic validation rules by key type
        validation_rules = {
            "anthropic": {"prefix": "sk-ant-", "min_length": 50, "max_length": 200},
            "github": {"prefix": ("ghp_", "github_pat_"), "min_length": 36, "max_length": 255},
            "linear": {"prefix": "lin_api_", "min_length": 40, "max_length": 100},
            "generic": {"min_length": 10, "max_length": 500},
        }

        rules = validation_rules.get(key_type, validation_rules["generic"])

        # Check length
        if len(api_key) < rules["min_length"] or len(api_key) > rules["max_length"]:
            return False

        # Check prefix if specified
        if "prefix" in rules:
            prefixes = rules["prefix"]
            if isinstance(prefixes, str):
                prefixes = (prefixes,)
            if not any(api_key.startswith(prefix) for prefix in prefixes):
                return False

        # Check for suspicious patterns
        suspicious_patterns = [
            "test",
            "fake",
            "dummy",
            "example",
            "placeholder",
            "xxxxxx",
            "123456",
            "abcdef",
        ]
        if any(pattern in api_key.lower() for pattern in suspicious_patterns):
            return False

        return True

    def rotate_key(self, old_encrypted_key: str, new_api_key: str, key_name: str) -> str:
        """
        Rotate an API key (replace old with new).

        Args:
            old_encrypted_key: Current encrypted key
            new_api_key: New plain text API key
            key_name: Name/identifier for the key

        Returns:
            New encrypted key

        Raises:
            KeySecurityError: If rotation fails
        """
        try:
            # Validate new key
            if not self.validate_api_key(new_api_key):
                raise KeySecurityError("New API key failed validation")

            # Decrypt old key for comparison
            try:
                old_key = self.decrypt_api_key(old_encrypted_key, key_name)
                if old_key == new_api_key:
                    raise KeySecurityError("New key is same as old key")
            except KeySecurityError:
                # Old key might be invalid, continue with rotation
                pass

            # Encrypt new key
            new_encrypted = self.encrypt_api_key(new_api_key, key_name)

            # Update metadata
            if key_name in self._key_metadata:
                self._key_metadata[key_name]["rotated_at"] = datetime.now(UTC).isoformat()

            logger.info(f"API key '{key_name}' rotated successfully")
            return new_encrypted

        except Exception as e:
            logger.error(f"Failed to rotate API key '{key_name}': {e}")
            raise KeySecurityError(f"Key rotation failed: {e}")

    def is_key_expired(self, key_name: str, max_age_days: int = 90) -> bool:
        """
        Check if a key should be rotated based on age.

        Args:
            key_name: Name/identifier for the key
            max_age_days: Maximum age in days before rotation recommended

        Returns:
            True if key should be rotated
        """
        if key_name not in self._key_metadata:
            return True  # Unknown keys should be rotated

        created_at = datetime.fromisoformat(self._key_metadata[key_name]["created_at"])
        age = datetime.now(UTC) - created_at

        return age > timedelta(days=max_age_days)

    def get_key_metadata(self, key_name: str) -> dict[str, Any]:
        """
        Get metadata about a key (without exposing the key itself).

        Args:
            key_name: Name/identifier for the key

        Returns:
            Dictionary with key metadata
        """
        return self._key_metadata.get(key_name, {})

    def clear_cache(self) -> None:
        """Clear any cached keys from memory."""
        self._key_cache.clear()
        logger.info("API key cache cleared")


class EnvironmentKeyManager:
    """Manages API keys from environment variables with validation."""

    def __init__(self, secure_manager: SecureKeyManager = None):
        """
        Initialize with optional secure manager for caching encrypted keys.

        Args:
            secure_manager: Optional SecureKeyManager for encryption
        """
        self.secure_manager = secure_manager

    def get_api_key(
        self, env_var: str, key_type: str = "generic", required: bool = True
    ) -> str | None:
        """
        Get API key from environment variable with validation.

        Args:
            env_var: Environment variable name
            key_type: Type of key for validation
            required: Whether key is required

        Returns:
            API key if found and valid, None otherwise

        Raises:
            KeySecurityError: If required key is missing or invalid
        """
        api_key = os.getenv(env_var)

        if not api_key:
            if required:
                raise KeySecurityError(
                    f"Required API key not found in environment variable: {env_var}"
                )
            return None

        # Remove common whitespace/quote issues
        api_key = api_key.strip().strip('"').strip("'")

        # Validate key format
        if self.secure_manager and not self.secure_manager.validate_api_key(api_key, key_type):
            logger.warning(f"API key in {env_var} failed validation checks")
            if required:
                raise KeySecurityError(f"API key in {env_var} appears invalid")

        # Mask key for logging (show first 6 and last 4 characters)
        masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
        logger.info(f"Retrieved API key from {env_var}: {masked_key}")

        return api_key

    def validate_all_keys(self) -> dict[str, bool]:
        """
        Validate all known API keys in environment.

        Returns:
            Dictionary mapping env var names to validation status
        """
        key_vars = {
            "ANTHROPIC_API_KEY": "anthropic",
            "GITHUB_TOKEN": "github",
            "LINEAR_API_KEY": "linear",
            "LINEAR_TOKEN": "linear",
        }

        results = {}
        for env_var, key_type in key_vars.items():
            try:
                key = self.get_api_key(env_var, key_type, required=False)
                results[env_var] = key is not None
            except KeySecurityError:
                results[env_var] = False

        return results
