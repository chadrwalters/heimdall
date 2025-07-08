#!/usr/bin/env python3
"""Integration test for the AI Analysis Engine."""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.analysis_engine import AnalysisEngine
from src.analysis.prompt_engineer import PromptEngineer


def test_analysis_engine():
    """Test the analysis engine with sample data."""
    print("Testing AI Analysis Engine...")

    # Sample PR data
    sample_pr = {
        "id": 999,
        "number": 999,
        "title": "Implement user profile feature",
        "body": "This PR adds user profile functionality\n\nLinear: ENG-5678",
        "user": {"login": "developer1"},
        "created_at": "2025-01-15T10:00:00Z",
        "additions": 250,
        "deletions": 50,
        "changed_files": 8,
        "html_url": "https://github.com/test/repo/pull/999",
        "base": {"ref": "main", "repo": {"name": "test-repo"}},
        "files": [
            {"filename": "src/profile/models.py"},
            {"filename": "src/profile/views.py"},
            {"filename": "tests/test_profile.py"},
        ],
    }

    # Sample diff
    sample_diff = """diff --git a/src/profile/models.py b/src/profile/models.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/profile/models.py
@@ -0,0 +1,25 @@
+from django.db import models
+from django.contrib.auth.models import User
+
+class UserProfile(models.Model):
+    user = models.OneToOneField(User, on_delete=models.CASCADE)
+    bio = models.TextField(max_length=500, blank=True)
+    location = models.CharField(max_length=100, blank=True)
+    birth_date = models.DateField(null=True, blank=True)
+    
+    def __str__(self):
+        return f"{self.user.username}'s profile"
"""

    # Test prompt engineering
    print("\n1. Testing Prompt Engineering...")
    engineer = PromptEngineer()
    prompt = engineer.create_analysis_prompt(
        title=sample_pr["title"],
        description=sample_pr["body"],
        diff=sample_diff,
        file_changes=[f["filename"] for f in sample_pr["files"]],
    )
    print(f"Created prompt ({len(prompt)} chars)")

    # Test response parsing
    sample_response = json.dumps(
        {
            "work_type": "New Feature",
            "complexity_score": 6,
            "risk_score": 4,
            "clarity_score": 8,
            "analysis_summary": "Adds user profile model with basic fields",
        }
    )

    result = engineer.parse_response(sample_response)
    print(f"Parsed response: {result.work_type}, complexity={result.complexity_score}")

    # Calculate impact score
    impact = engineer.calculate_impact_score(
        result.complexity_score, result.risk_score, result.clarity_score
    )
    print(f"Impact score: {impact:.2f}")

    # Test with actual API if key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print("\n2. Testing with actual Claude API...")
        try:
            engine = AnalysisEngine(api_key=api_key)

            # Analyze the sample PR
            analysis = engine.analyze_pr(sample_pr, diff=sample_diff)

            print("\nAnalysis Results:")
            print(f"  Work Type: {analysis['work_type']}")
            print(f"  Complexity: {analysis['complexity_score']}/10")
            print(f"  Risk: {analysis['risk_score']}/10")
            print(f"  Clarity: {analysis['clarity_score']}/10")
            print(f"  Impact Score: {analysis['impact_score']:.2f}")
            print(f"  Summary: {analysis['analysis_summary']}")
            print(f"  Linear Ticket: {analysis['linear_ticket_id']}")
            print(f"  Process Compliant: {analysis['process_compliant']}")

            # Get usage stats
            stats = engine.get_stats()
            print("\nUsage Stats:")
            print(f"  Total API calls: {stats['total_api_calls']}")
            print(f"  Total tokens used: {stats['total_tokens_used']}")
            print(f"  Estimated cost: ${stats['estimated_cost']:.4f}")

        except Exception as e:
            print(f"Error during API test: {e}")
    else:
        print("\n2. Skipping API test (no ANTHROPIC_API_KEY found)")
        print("   Set ANTHROPIC_API_KEY environment variable to test with real API")

    print("\n✅ Integration test completed!")


if __name__ == "__main__":
    test_analysis_engine()
