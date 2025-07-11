"""Test fixtures for AI Analysis Engine tests."""

from datetime import UTC, datetime

# Sample PR data for different scenarios
SAMPLE_PRS = {
    "feature": {
        "id": 1001,
        "number": 1001,
        "title": "Implement user authentication system",
        "body": "This PR adds JWT-based authentication\n\nLinear: AUTH-123",
        "user": {"login": "developer1"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 500,
        "deletions": 100,
        "changed_files": 12,
        "html_url": "https://github.com/test/repo/pull/1001",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [
            {"filename": "src/auth/jwt.py"},
            {"filename": "src/auth/middleware.py"},
            {"filename": "tests/test_auth.py"},
        ],
    },
    "bugfix": {
        "id": 1002,
        "number": 1002,
        "title": "Fix null pointer exception in user service",
        "body": "Fixes NPE when user profile is missing\n\nLinear: BUG-456",
        "user": {"login": "developer2"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 50,
        "deletions": 20,
        "changed_files": 3,
        "html_url": "https://github.com/test/repo/pull/1002",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [
            {"filename": "src/services/user_service.py"},
            {"filename": "tests/test_user_service.py"},
        ],
    },
    "refactor": {
        "id": 1003,
        "number": 1003,
        "title": "Refactor database connection pooling",
        "body": "Improves performance by optimizing connection management\n\nLinear: PERF-789",
        "user": {"login": "developer3"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 300,
        "deletions": 250,
        "changed_files": 8,
        "html_url": "https://github.com/test/repo/pull/1003",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [
            {"filename": "src/db/connection_pool.py"},
            {"filename": "src/db/manager.py"},
            {"filename": "config/database.yaml"},
        ],
    },
    "testing": {
        "id": 1004,
        "number": 1004,
        "title": "Add comprehensive unit tests for payment module",
        "body": "Increases test coverage to 95%\n\nLinear: TEST-321",
        "user": {"login": "developer4"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 800,
        "deletions": 0,
        "changed_files": 5,
        "html_url": "https://github.com/test/repo/pull/1004",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [
            {"filename": "tests/test_payment_gateway.py"},
            {"filename": "tests/test_payment_processor.py"},
            {"filename": "tests/fixtures/payment_data.py"},
        ],
    },
    "documentation": {
        "id": 1005,
        "number": 1005,
        "title": "Update API documentation",
        "body": "Updates OpenAPI specs and adds examples\n\nLinear: DOC-654",
        "user": {"login": "developer5"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 200,
        "deletions": 50,
        "changed_files": 3,
        "html_url": "https://github.com/test/repo/pull/1005",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [
            {"filename": "docs/api/openapi.yaml"},
            {"filename": "README.md"},
            {"filename": "docs/examples/auth.md"},
        ],
    },
    "chore": {
        "id": 1006,
        "number": 1006,
        "title": "Update dependencies to latest versions",
        "body": "Bumps all dependencies to fix security vulnerabilities\n\nLinear: MAINT-987",
        "user": {"login": "developer6"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 100,
        "deletions": 100,
        "changed_files": 4,
        "html_url": "https://github.com/test/repo/pull/1006",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [
            {"filename": "requirements.txt"},
            {"filename": "pyproject.toml"},
            {"filename": "poetry.lock"},
        ],
    },
    "no_ticket": {
        "id": 1007,
        "number": 1007,
        "title": "Quick fix for typo",
        "body": "Fixed a typo in error message",
        "user": {"login": "developer7"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 1,
        "deletions": 1,
        "changed_files": 1,
        "html_url": "https://github.com/test/repo/pull/1007",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [{"filename": "src/utils/messages.py"}],
    },
    "ai_assisted": {
        "id": 1008,
        "number": 1008,
        "title": "Implement data validation layer",
        "body": "Adds comprehensive validation using Pydantic\n\nLinear: FEAT-111\n\n🤖 Generated with Claude Code",
        "user": {"login": "developer8"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 400,
        "deletions": 50,
        "changed_files": 6,
        "html_url": "https://github.com/test/repo/pull/1008",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [
            {"filename": "src/validators/user_validator.py"},
            {"filename": "src/validators/product_validator.py"},
        ],
    },
}

# Sample diffs for different scenarios
SAMPLE_DIFFS = {
    "small": r"""diff --git a/src/utils/helpers.py b/src/utils/helpers.py
index 1234567..abcdefg 100644
--- a/src/utils/helpers.py
+++ b/src/utils/helpers.py
@@ -10,7 +10,7 @@ def format_date(date):
     return date.strftime('%Y-%m-%d')
 
 def validate_email(email):
-    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
+    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
     return re.match(pattern, email) is not None
""",
    "medium": """diff --git a/src/auth/jwt.py b/src/auth/jwt.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/auth/jwt.py
@@ -0,0 +1,45 @@
+import jwt
+from datetime import datetime, timedelta
+from typing import Optional, Dict
+
+class JWTManager:
+    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
+        self.secret_key = secret_key
+        self.algorithm = algorithm
+        
+    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
+        payload = {
+            'user_id': user_id,
+            'exp': datetime.now(timezone.utc) + timedelta(seconds=expires_in),
+            'iat': datetime.now(timezone.utc)
+        }
+        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
+        
+    def verify_token(self, token: str) -> Optional[Dict]:
+        try:
+            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
+            return payload
+        except jwt.ExpiredSignatureError:
+            return None
+        except jwt.InvalidTokenError:
+            return None
""",
    "large": """diff --git a/src/services/payment_processor.py b/src/services/payment_processor.py
index 1234567..abcdefg 100644
--- a/src/services/payment_processor.py
+++ b/src/services/payment_processor.py
@@ -1,200 +1,350 @@
+import asyncio
+import logging
+from decimal import Decimal
+from typing import Dict, List, Optional
+from dataclasses import dataclass
+from enum import Enum
+
+from .gateway import PaymentGateway
+from .validators import PaymentValidator
+from ..models import Transaction, PaymentMethod
+
+logger = logging.getLogger(__name__)
+
+class PaymentStatus(Enum):
+    PENDING = "pending"
+    PROCESSING = "processing"
+    COMPLETED = "completed"
+    FAILED = "failed"
+    REFUNDED = "refunded"
+
+@dataclass
+class PaymentRequest:
+    amount: Decimal
+    currency: str
+    method: PaymentMethod
+    customer_id: str
+    metadata: Optional[Dict] = None
+
+class PaymentProcessor:
+    def __init__(self, gateway: PaymentGateway):
+        self.gateway = gateway
+        self.validator = PaymentValidator()
+        
+    async def process_payment(self, request: PaymentRequest) -> Transaction:
+        # Validate payment request
+        validation_result = self.validator.validate_payment_request(request)
+        if not validation_result.is_valid:
+            raise ValueError(f"Invalid payment request: {validation_result.errors}")
+            
+        # Create transaction record
+        transaction = Transaction(
+            amount=request.amount,
+            currency=request.currency,
+            status=PaymentStatus.PENDING,
+            customer_id=request.customer_id,
+            payment_method=request.method
+        )
+        
+        try:
+            # Process with gateway
+            logger.info(f"Processing payment for customer {request.customer_id}")
+            result = await self.gateway.charge(
+                amount=request.amount,
+                currency=request.currency,
+                payment_method=request.method,
+                metadata=request.metadata
+            )
+            
+            transaction.gateway_response = result
+            transaction.status = PaymentStatus.COMPLETED
+            transaction.gateway_transaction_id = result.get('transaction_id')
+            
+        except Exception as e:
+            logger.error(f"Payment processing failed: {str(e)}")
+            transaction.status = PaymentStatus.FAILED
+            transaction.error_message = str(e)
+            raise
+            
+        finally:
+            # Save transaction
+            await transaction.save()
+            
+        return transaction
+        
+    async def refund_transaction(self, transaction_id: str, amount: Optional[Decimal] = None) -> Transaction:
+        transaction = await Transaction.get(transaction_id)
+        if not transaction:
+            raise ValueError(f"Transaction {transaction_id} not found")
+            
+        if transaction.status != PaymentStatus.COMPLETED:
+            raise ValueError(f"Cannot refund transaction in {transaction.status} status")
+            
+        refund_amount = amount or transaction.amount
+        if refund_amount > transaction.amount:
+            raise ValueError("Refund amount cannot exceed original transaction amount")
+            
+        try:
+            result = await self.gateway.refund(
+                transaction_id=transaction.gateway_transaction_id,
+                amount=refund_amount
+            )
+            
+            transaction.status = PaymentStatus.REFUNDED
+            transaction.refund_amount = refund_amount
+            transaction.refund_response = result
+            
+        except Exception as e:
+            logger.error(f"Refund failed for transaction {transaction_id}: {str(e)}")
+            raise
+            
+        finally:
+            await transaction.save()
+            
+        return transaction
+"""
    + "+" * 50
    + "\n" * 100,  # Add more lines to make it large
}

# Sample API responses
SAMPLE_API_RESPONSES = {
    "feature": {
        "work_type": "New Feature",
        "complexity_score": 8,
        "risk_score": 6,
        "clarity_score": 9,
        "analysis_summary": "Implements comprehensive JWT-based authentication system with middleware support",
    },
    "bugfix": {
        "work_type": "Bug Fix",
        "complexity_score": 3,
        "risk_score": 2,
        "clarity_score": 8,
        "analysis_summary": "Fixes null pointer exception by adding proper null checks in user service",
    },
    "refactor": {
        "work_type": "Refactor",
        "complexity_score": 7,
        "risk_score": 5,
        "clarity_score": 7,
        "analysis_summary": "Refactors database connection pooling to improve performance and resource utilization",
    },
    "error": {
        "work_type": "Unknown",
        "complexity_score": 5,
        "risk_score": 5,
        "clarity_score": 5,
        "analysis_summary": "Unable to analyze due to API error",
    },
}

# Work type classification test cases
WORK_TYPE_TEST_CASES = [
    {"title": "Fix null pointer exception in payment service", "expected": "Bug Fix"},
    {"title": "Implement OAuth2 authentication", "expected": "New Feature"},
    {"title": "Add support for webhook notifications", "expected": "New Feature"},
    {"title": "Refactor database queries for performance", "expected": "Refactor"},
    {"title": "Update dependencies to latest versions", "expected": "Chore"},
    {"title": "Add unit tests for user service", "expected": "Testing"},
    {"title": "Update API documentation with examples", "expected": "Documentation"},
    {"title": "Fix typo in error message", "expected": "Bug Fix"},
    {"title": "Migrate from SQLite to PostgreSQL", "expected": "Chore"},
    {"title": "Implement caching layer", "expected": "New Feature"},
    {"title": "Clean up unused imports", "expected": "Refactor"},
    {"title": "Add integration tests for payment flow", "expected": "Testing"},
    {"title": "Update README with installation instructions", "expected": "Documentation"},
    {"title": "Fix memory leak in background worker", "expected": "Bug Fix"},
    {"title": "Optimize image processing pipeline", "expected": "Refactor"},
]

# AI-assisted PR bodies for testing detection
AI_ASSISTED_BODIES = [
    "This PR implements user authentication.\n\n🤖 Generated with Claude Code",
    "Fixes bug in payment processing.\n\nCreated using GitHub Copilot",
    "Refactoring database layer.\n\nWritten with cursor.ai assistance",
    "Updates dependencies.\n\nCo-Authored-By: Assistant <noreply@anthropic.com>",
    "Adds new feature.\n\nGenerated by AI assistant",
    "Bug fix.\n\nThis code was written with the help of an AI coding assistant",
]

# Edge case PR data
EDGE_CASE_PRS = {
    "empty_body": {
        "id": 2001,
        "number": 2001,
        "title": "Fix critical bug",
        "body": "",
        "user": {"login": "developer1"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 10,
        "deletions": 5,
        "changed_files": 1,
        "html_url": "https://github.com/test/repo/pull/2001",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [{"filename": "src/fix.py"}],
    },
    "no_files": {
        "id": 2002,
        "number": 2002,
        "title": "Empty PR",
        "body": "This PR has no file changes",
        "user": {"login": "developer2"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 0,
        "deletions": 0,
        "changed_files": 0,
        "html_url": "https://github.com/test/repo/pull/2002",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [],
    },
    "huge_changes": {
        "id": 2003,
        "number": 2003,
        "title": "Massive refactoring",
        "body": "Complete system overhaul\n\nLinear: MEGA-999",
        "user": {"login": "developer3"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 50000,
        "deletions": 30000,
        "changed_files": 500,
        "html_url": "https://github.com/test/repo/pull/2003",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [{"filename": f"src/file_{i}.py"} for i in range(500)],
    },
}


def get_truncated_diff():
    """Generate a diff that exceeds 4000 characters."""
    base_diff = """diff --git a/src/large_file.py b/src/large_file.py
index 1234567..abcdefg 100644
--- a/src/large_file.py
+++ b/src/large_file.py
@@ -1,1000 +1,2000 @@
"""
    # Add many lines to exceed 4000 chars
    for i in range(100):
        base_diff += f"+def function_{i}(param1, param2, param3):\n"
        base_diff += f"+    '''Docstring for function {i}'''\n"
        base_diff += "+    result = param1 + param2 * param3\n"
        base_diff += f"+    logger.info(f'Processing function {i} with result {{result}}')\n"
        base_diff += "+    return result\n+\n"

    return base_diff


def sample_pr_data():
    """Generate a sample PR data structure."""
    return SAMPLE_PRS["feature"]


def large_pr_data():
    """Generate a large PR data structure for load testing."""
    return {
        "id": 2001,
        "number": 2001,
        "title": "Large-scale refactoring: Modernize codebase architecture",
        "body": "This PR contains a comprehensive refactoring of the entire codebase:\n\n"
        + "- Migrates from legacy framework to modern architecture\n"
        + "- Adds comprehensive type hints and documentation\n"
        + "- Implements new design patterns\n"
        + "- Updates all dependencies\n"
        + "- Refactors database layer\n"
        + "- Adds extensive test coverage\n\n"
        + "Linear: ARCH-2001",
        "user": {"login": "senior_developer"},
        "created_at": datetime.now(UTC).isoformat() + "Z",
        "additions": 15000,
        "deletions": 8000,
        "changed_files": 150,
        "html_url": "https://github.com/test/repo/pull/2001",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [
            {"filename": f"src/module_{i}/file_{j}.py"} for i in range(1, 21) for j in range(1, 8)
        ],
    }


def sample_commit_data():
    """Generate sample commit data structure."""
    return {
        "sha": "abc123def456",
        "commit": {
            "message": "Fix user authentication bug\n\nLinear: BUG-123",
            "author": {
                "name": "Developer",
                "email": "dev@example.com",
                "date": datetime.now(UTC).isoformat() + "Z",
            },
        },
        "author": {"login": "developer1"},
        "html_url": "https://github.com/test/repo/commit/abc123def456",
        "stats": {"additions": 25, "deletions": 10, "total": 35},
        "files": [
            {"filename": "src/auth.py", "additions": 20, "deletions": 5, "changes": 25},
            {"filename": "tests/test_auth.py", "additions": 5, "deletions": 5, "changes": 10},
        ],
    }


def mock_claude_responses():
    """Generate mock Claude API responses."""
    return SAMPLE_API_RESPONSES
