#!/usr/bin/env python3
"""Test script for GitHub Action Analyzer."""

import json
import os
import sys
from datetime import datetime

# Test data
test_pr_data = {
    "number": 123,
    "title": "Add user authentication feature",
    "body": "This PR implements JWT-based authentication for the API.\n\nLinear: ENG-1234",
    "user": {"login": "testuser"},
    "base": {"ref": "main"},
    "head": {"ref": "feature/auth"},
    "html_url": "https://github.com/test/repo/pull/123",
    "changed_files": 5,
    "additions": 250,
    "deletions": 50,
}

test_diff = """
diff --git a/src/auth/jwt.py b/src/auth/jwt.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/auth/jwt.py
@@ -0,0 +1,25 @@
+import jwt
+from datetime import datetime, timedelta
+
+class JWTAuth:
+    def __init__(self, secret_key):
+        self.secret_key = secret_key
+    
+    def generate_token(self, user_id):
+        payload = {
+            'user_id': user_id,
+            'exp': datetime.utcnow() + timedelta(hours=24)
+        }
+        return jwt.encode(payload, self.secret_key, algorithm='HS256')
+    
+    def verify_token(self, token):
+        try:
+            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
+            return payload['user_id']
+        except jwt.ExpiredSignatureError:
+            return None
+        except jwt.InvalidTokenError:
+            return None
"""


def main():
    """Run test of GitHub Action Analyzer locally."""
    print("Testing GitHub Action Analyzer...")

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY not set. Using mock mode.")
        # Create mock result
        result = {
            "pr_number": 123,
            "work_type": "New Feature",
            "complexity_score": 6,
            "risk_score": 7,
            "clarity_score": 8,
            "impact_score": 6.3,
            "analysis_summary": "Implements JWT-based authentication for API security",
            "ai_assisted": False,
            "ai_tool_type": None,
            "linear_ticket_id": "ENG-1234",
            "has_linear_ticket": True,
            "lines_added": 250,
            "lines_deleted": 50,
            "files_changed": 5,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        print("\nMock Analysis Result:")
        print(json.dumps(result, indent=2))

        # Test comment formatting
        print("\n" + "=" * 60)
        print("Sample PR Comment:")
        print("=" * 60)

        print(f"""
## 🤖 PR Analysis Results

**Work Type:** {result["work_type"]}  
**Summary:** {result["analysis_summary"]}

### 📊 Scores

| Metric | Score | Indicator | Description |
|--------|-------|-----------|-------------|
| **Complexity** | {result["complexity_score"]}/10 | 🟡 | How complex are the changes? |
| **Risk** | {result["risk_score"]}/10 | 🟡 | Potential for breaking changes |
| **Clarity** | {result["clarity_score"]}/10 | 🟢 | Code readability and documentation |
| **Impact** | {result["impact_score"]}/10 | - | Overall impact score |

### 📋 Additional Information

- **Files Changed:** {result["files_changed"]}
- **Lines Added:** +{result["lines_added"]}
- **Lines Deleted:** -{result["lines_deleted"]}
- **AI-Assisted:** {"Yes" if result["ai_assisted"] else "No"}
- **Linear Ticket:** [{result["linear_ticket_id"]}](https://linear.app/issue/{result["linear_ticket_id"]})
        """)

        return

    # Create test files
    with open("pr_data.json", "w") as f:
        json.dump(test_pr_data, f)

    with open("pr_diff.txt", "w") as f:
        f.write(test_diff)

    # Import and run analyzer
    try:
        from github_action_analyzer import GitHubActionAnalyzer

        analyzer = GitHubActionAnalyzer()
        result = analyzer.analyze_pr(test_pr_data, test_diff)

        print("\nAnalysis Result:")
        print(json.dumps(result, indent=2))

        # Save result
        with open("analysis_result.json", "w") as f:
            json.dump(result, f, indent=2)

        print("\n✅ Test completed successfully!")
        print("Check analysis_result.json for full output")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)

    finally:
        # Cleanup test files
        for f in ["pr_data.json", "pr_diff.txt"]:
            if os.path.exists(f):
                os.remove(f)


if __name__ == "__main__":
    main()
