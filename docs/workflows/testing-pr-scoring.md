# Testing PR Scoring Workflows

## Overview
Guide for testing both the automated Python analyzer and the new Claude-powered PR scoring system.

## Test Scenarios

### Test 1: Basic Functionality
1. **Create a small PR** (1-2 files, <100 lines)
2. **Observe automated analysis** (should appear within 3 minutes)
3. **Trigger Claude analysis** with `@claude-score` comment
4. **Compare results** - should be similar for simple changes

**Expected Results:**
- Both give low complexity (1-4)
- Similar work type classification
- Reasonable clarity scores (6-8)

### Test 2: Complex Changes
1. **Create a large PR** (>5 files, >500 lines)
2. **Wait for automated analysis**
3. **Request Claude analysis** with `@claude-score`
4. **Look for size-based score adjustments**

**Expected Results:**
- Both respect minimum score thresholds
- Complexity scores ≥6 for large changes
- Risk scores appropriately elevated

### Test 3: Edge Cases
1. **Documentation-only PR**
2. **Refactoring PR** (same functionality, different structure)
3. **Infrastructure changes** (workflows, configs)

**Expected Results:**
- Accurate work type classification
- Appropriate risk/complexity scoring
- Context-aware analysis from Claude

## Validation Checklist

### Automated Analyzer Validation
- [ ] **Comment appears** within 3 minutes of PR creation
- [ ] **Scores are reasonable** (1-10 scale, logical progression)
- [ ] **Labels applied** correctly (complexity, risk, work type)
- [ ] **Linear ticket detection** works when present
- [ ] **CSV format** valid for downstream analysis

### Claude Scoring Validation
- [ ] **Responds to trigger** `@claude-score` within 60 seconds
- [ ] **Uses exact format** specified in custom instructions
- [ ] **Scoring methodology** follows North Star criteria
- [ ] **Explanations provided** for scoring decisions
- [ ] **AI detection** identifies patterns when present

### Cross-Validation
- [ ] **Complexity scores** within 2-3 points of each other
- [ ] **Risk assessment** generally aligned
- [ ] **Work type classification** matches
- [ ] **Large differences explained** by context or approach

## Sample Test PRs

### Simple Bug Fix
```
Files: 1
Lines: +5/-5
Type: Bug Fix
Expected Complexity: 2-3
Expected Risk: 2-4
```

### New Feature
```
Files: 3-5
Lines: +200/-50
Type: New Feature  
Expected Complexity: 5-7
Expected Risk: 4-6
```

### Architecture Change
```
Files: 8+
Lines: +1000/-500
Type: Refactoring/Infrastructure
Expected Complexity: 7-9
Expected Risk: 6-8
```

## Troubleshooting

### Automated Analysis Not Appearing
1. Check GitHub Actions tab for workflow errors
2. Verify ANTHROPIC_API_KEY secret exists
3. Confirm pr-analysis.yml workflow is enabled

### Claude Scoring Not Responding
1. Use exact trigger phrase `@claude-score`
2. Check ANTHROPIC_API_KEY secret exists
3. Verify claude-pr-scoring.yml workflow is enabled
4. Check workflow permissions for PR comments

### Scoring Inconsistencies
1. Document the differences for calibration
2. Check if one system has additional context
3. Verify scoring criteria are consistently applied
4. Report systematic biases for investigation

## Success Criteria

### Individual System Success
- **Response Rate**: >95% successful analysis
- **Accuracy**: Scores match manual assessment
- **Consistency**: Similar PRs get similar scores
- **Performance**: Analysis completes within time limits

### Comparative Success
- **Correlation**: >0.7 correlation between scoring systems
- **Classification**: >80% work type agreement
- **Reasonableness**: No systematic bias in either direction
- **Improvement**: Claude feedback improves automated system