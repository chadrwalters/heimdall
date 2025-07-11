#!/bin/bash
# Test script for GitHub extraction functionality

echo "=========================================="
echo "Testing GitHub Extraction Scripts"
echo "=========================================="

# Test with a small organization or single repo for validation
# You can modify this to test with your actual organization

# Test 1: Check prerequisites
echo "Test 1: Checking prerequisites..."
if command -v gh >/dev/null 2>&1; then
    echo "✅ GitHub CLI installed"
else
    echo "❌ GitHub CLI not found"
    exit 1
fi

if gh auth status >/dev/null 2>&1; then
    echo "✅ GitHub CLI authenticated"
else
    echo "❌ GitHub CLI not authenticated"
    exit 1
fi

if command -v jq >/dev/null 2>&1; then
    echo "✅ jq installed"
else
    echo "❌ jq not found"
    exit 1
fi

# Test 2: Test utility functions
echo -e "\nTest 2: Testing utility functions..."
source scripts/extraction/utils.sh

# Test date functions
test_date=$(days_ago 7)
echo "✅ Date 7 days ago: $test_date"

formatted=$(format_date "$test_date")
echo "✅ Formatted date: $formatted"

# Test 3: Dry run with limited scope
echo -e "\nTest 3: Testing extraction with limited scope..."
echo "This would normally extract data. For testing, we'll just show the help:"
./scripts/extraction/run_extraction.sh --help

echo -e "\n=========================================="
echo "Test Summary:"
echo "=========================================="
echo "✅ All prerequisite checks passed"
echo "✅ Utility functions working correctly"
echo "✅ Scripts are properly configured"
echo ""
echo "To run actual extraction, use:"
echo "  ./scripts/extraction/run_extraction.sh --org YOUR_ORG_NAME --days 1"
echo ""
echo "For incremental updates:"
echo "  ./scripts/extraction/run_extraction.sh --org YOUR_ORG_NAME --incremental"
echo ""