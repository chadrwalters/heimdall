"""GraphQL query validation and sanitization."""

import re
from typing import Any

from .input_validator import ValidationError


class GraphQLValidator:
    """Validates and sanitizes GraphQL queries to prevent injection attacks."""

    # Maximum allowed query complexity (number of fields/operations)
    MAX_QUERY_COMPLEXITY = 100

    # Maximum query depth
    MAX_QUERY_DEPTH = 10

    # Allowed GraphQL operations
    ALLOWED_OPERATIONS = {"query", "mutation", "subscription"}

    # Dangerous patterns in GraphQL queries
    DANGEROUS_PATTERNS = [
        r"__schema",  # Schema introspection
        r"__type",  # Type introspection
        r"eval\s*\(",  # Eval calls
        r"exec\s*\(",  # Exec calls
        r"import\s+",  # Import statements
        r"require\s*\(",  # Require calls
        r"process\.",  # Process access
        r"global\.",  # Global access
        r"window\.",  # Window access (if somehow executed client-side)
    ]

    # Allowed Linear API fields (whitelist approach)
    ALLOWED_LINEAR_FIELDS = {
        "query": {
            "viewer",
            "user",
            "users",
            "team",
            "teams",
            "issue",
            "issues",
            "project",
            "projects",
            "workflowState",
            "workflowStates",
            "issueLabel",
            "issueLabels",
            "cycle",
            "cycles",
            "comment",
            "comments",
        },
        "fields": {
            "id",
            "name",
            "title",
            "description",
            "url",
            "identifier",
            "number",
            "state",
            "priority",
            "estimate",
            "assignee",
            "creator",
            "team",
            "project",
            "labels",
            "comments",
            "createdAt",
            "updatedAt",
            "completedAt",
            "startedAt",
            "dueDate",
            "parent",
            "children",
            "archivedAt",
            "canceledAt",
            "boardOrder",
            "sortOrder",
            "color",
            "key",
            "teamKey",
            "issueCount",
            "completedIssueCount",
            "scope",
            "progress",
            "startDate",
            "targetDate",
            "status",
            "health",
            # Cycle-specific fields
            "startsAt",
            "endsAt",
            "priorityLabel",
            "email",
            "type",
            "lead",
            "nodes",
            "first",
            "filter",
            "eq",
            "isActive",
            "position",
        },
    }

    @classmethod
    def validate_query(
        cls, query: str, variables: dict[str, Any] = None
    ) -> tuple[str, dict[str, Any]]:
        """
        Validate and sanitize a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Tuple of (sanitized_query, sanitized_variables)

        Raises:
            ValidationError: If query is invalid or dangerous
        """
        if not isinstance(query, str):
            raise ValidationError("Query must be a string")

        if len(query) > 10000:  # Reasonable limit for query size
            raise ValidationError("Query too long")

        # Remove comments and normalize whitespace
        sanitized_query = cls._normalize_query(query)

        # Check for dangerous patterns
        cls._check_dangerous_patterns(sanitized_query)

        # Validate query structure
        cls._validate_query_structure(sanitized_query)

        # Validate query complexity and depth
        cls._validate_query_complexity(sanitized_query)

        # Validate fields against whitelist
        cls._validate_fields(sanitized_query)

        # Sanitize variables
        sanitized_variables = cls._sanitize_variables(variables or {})

        return sanitized_query, sanitized_variables

    @classmethod
    def _normalize_query(cls, query: str) -> str:
        """Normalize query by removing comments and extra whitespace."""
        # Remove GraphQL comments
        query = re.sub(r"#.*?$", "", query, flags=re.MULTILINE)

        # Normalize whitespace
        query = re.sub(r"\s+", " ", query).strip()

        return query

    @classmethod
    def _check_dangerous_patterns(cls, query: str) -> None:
        """Check for dangerous patterns in the query."""
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                raise ValidationError(f"Dangerous pattern detected in query: {pattern}")

    @classmethod
    def _validate_query_structure(cls, query: str) -> None:
        """Validate basic GraphQL query structure."""
        # Check for valid operation type
        operation_match = re.search(r"^\s*(query|mutation|subscription)\s*", query, re.IGNORECASE)
        if operation_match:
            operation = operation_match.group(1).lower()
            if operation not in cls.ALLOWED_OPERATIONS:
                raise ValidationError(f"Operation type not allowed: {operation}")

        # Check for balanced braces
        open_braces = query.count("{")
        close_braces = query.count("}")
        if open_braces != close_braces:
            raise ValidationError("Unbalanced braces in query")

        # Check for balanced parentheses
        open_parens = query.count("(")
        close_parens = query.count(")")
        if open_parens != close_parens:
            raise ValidationError("Unbalanced parentheses in query")

    @classmethod
    def _validate_query_complexity(cls, query: str) -> None:
        """Validate query complexity to prevent DoS attacks."""
        # Count fields (approximate complexity)
        field_count = len(re.findall(r"\w+\s*(?:\([^)]*\))?\s*{", query))
        if field_count > cls.MAX_QUERY_COMPLEXITY:
            raise ValidationError(f"Query too complex: {field_count} > {cls.MAX_QUERY_COMPLEXITY}")

        # Count nesting depth
        max_depth = 0
        current_depth = 0
        for char in query:
            if char == "{":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == "}":
                current_depth -= 1

        if max_depth > cls.MAX_QUERY_DEPTH:
            raise ValidationError(f"Query too deep: {max_depth} > {cls.MAX_QUERY_DEPTH}")

    @classmethod
    def _validate_fields(cls, query: str) -> None:
        """Validate that only allowed fields are requested."""
        # Extract field names from the query
        field_pattern = r"\b(\w+)\s*(?:\([^)]*\))?\s*(?:{|$)"
        fields = re.findall(field_pattern, query)

        allowed_all = cls.ALLOWED_LINEAR_FIELDS["query"] | cls.ALLOWED_LINEAR_FIELDS["fields"]

        for field in fields:
            # Skip query/mutation/subscription operation names (e.g., "query GetIssue")
            # These will start with capital letter after the operation keyword
            if field[0].isupper():
                continue

            if field not in allowed_all and not field.startswith(
                tuple(cls.ALLOWED_LINEAR_FIELDS["query"])
            ):
                # Allow some flexibility for nested fields and standard GraphQL fields
                if field not in {
                    "node",
                    "edges",
                    "pageInfo",
                    "hasNextPage",
                    "hasPreviousPage",
                    "cursor",
                    "query",  # GraphQL operation keyword
                    "mutation",  # GraphQL operation keyword
                    "subscription",  # GraphQL operation keyword
                }:
                    raise ValidationError(f"Field not allowed: {field}")

    @classmethod
    def _sanitize_variables(cls, variables: dict[str, Any]) -> dict[str, Any]:
        """Sanitize query variables."""
        if not isinstance(variables, dict):
            raise ValidationError("Variables must be a dictionary")

        sanitized = {}
        for key, value in variables.items():
            # Validate key names
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", key):
                raise ValidationError(f"Invalid variable name: {key}")

            # Sanitize values based on type
            if isinstance(value, str):
                if len(value) > 1000:  # Reasonable limit for string variables
                    raise ValidationError(f"Variable '{key}' value too long")
                # Basic string sanitization
                sanitized[key] = value.strip()
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif value is None:
                sanitized[key] = None
            elif isinstance(value, (list, dict)):
                # For complex types, convert to string and validate length
                str_value = str(value)
                if len(str_value) > 5000:
                    raise ValidationError(f"Variable '{key}' too complex")
                sanitized[key] = value
            else:
                raise ValidationError(f"Unsupported variable type for '{key}': {type(value)}")

        return sanitized

    @classmethod
    def create_safe_query(
        cls, operation: str, fields: list[str], filters: dict[str, Any] = None
    ) -> str:
        """
        Create a safe GraphQL query from validated components.

        Args:
            operation: Operation name (must be in allowed list)
            fields: List of field names to query
            filters: Optional filters to apply

        Returns:
            Safe GraphQL query string

        Raises:
            ValidationError: If components are invalid
        """
        if operation not in cls.ALLOWED_LINEAR_FIELDS["query"]:
            raise ValidationError(f"Operation not allowed: {operation}")

        # Validate all fields
        for field in fields:
            if field not in cls.ALLOWED_LINEAR_FIELDS["fields"]:
                raise ValidationError(f"Field not allowed: {field}")

        # Build query
        fields_str = " ".join(fields)

        if filters:
            # Sanitize filters
            sanitized_filters = cls._sanitize_variables(filters)
            filter_args = []
            for key, value in sanitized_filters.items():
                if isinstance(value, str):
                    filter_args.append(f'{key}: "{value}"')
                else:
                    filter_args.append(f"{key}: {value}")
            filter_str = f"({', '.join(filter_args)})"
        else:
            filter_str = ""

        query = f"""
        query {{
            {operation}{filter_str} {{
                {fields_str}
            }}
        }}
        """.strip()

        return query
