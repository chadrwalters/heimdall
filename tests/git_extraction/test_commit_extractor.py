import git
import pytest
from src.git_extraction.commit_extractor import CommitExtractor
from src.git_extraction.config import GitExtractionConfig


def test_get_commits_since_includes_all_main_branch_commits(tmp_path):
    """Test that get_commits_since returns ALL commits to main, not just PR merges."""
    # Create test repo with direct commits and PR merges
    repo = git.Repo.init(tmp_path)

    # Create main branch with direct commit
    (tmp_path / "file1.txt").write_text("initial")
    repo.index.add(["file1.txt"])
    _commit1 = repo.index.commit("Direct commit to main")  # noqa: F841

    # Ensure we're on 'main' branch (git init default branch varies)
    repo.git.branch("-M", "main")

    # Create feature branch with PR merge
    repo.git.checkout("-b", "feature")
    (tmp_path / "file2.txt").write_text("feature")
    repo.index.add(["file2.txt"])
    _feature_commit = repo.index.commit("Feature work")  # noqa: F841

    # Merge back to main (creates merge commit)
    repo.git.checkout("main")
    repo.git.merge("feature", "--no-ff", "-m", "Merge PR #1")

    # Add another direct commit after merge
    (tmp_path / "file3.txt").write_text("post-merge")
    repo.index.add(["file3.txt"])
    _commit3 = repo.index.commit("Another direct commit")  # noqa: F841

    # Extract commits
    config = GitExtractionConfig()
    extractor = CommitExtractor(config)
    commits = extractor.get_commits_since(str(tmp_path), since_date="2000-01-01")

    # Should get ALL 4 commits: 2 direct + 1 feature + 1 merge
    assert len(commits) == 4
    commit_messages = [c["message"] for c in commits]
    assert "Direct commit to main" in commit_messages
    assert "Another direct commit" in commit_messages
    assert "Feature work" in commit_messages
    assert "Merge PR #1" in commit_messages
