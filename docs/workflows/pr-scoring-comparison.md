# PR Scoring Comparison: Automated vs Claude-Powered

## Overview
We now have two complementary approaches for analyzing pull requests with North Star Metrics scoring:

1. **Automated Python Analyzer** - Runs automatically on every PR
2. **Claude-Powered Scoring** - On-demand analysis with `@claude-score`

## Comparison Table

| Aspect | Automated Analyzer | Claude Scoring |
|--------|-------------------|----------------|
| **Trigger** | Automatic on PR open/update | Manual with `@claude-score` |
| **Response Time** | ~2-3 minutes | ~30-60 seconds |
| **Scoring Method** | Python script + Anthropic API | Direct Claude analysis |
| **Consistency** | High (same logic every time) | Variable (AI interpretation) |
| **Context Awareness** | Code diff + metadata | Full codebase context |
| **Cost** | Higher (extraction + analysis) | Lower (single API call) |
| **Use Case** | Production scoring | Validation & comparison |

## Usage Workflows

### Standard Workflow (Automated)
```bash
# Create PR → Automatic analysis appears
# No action needed - analysis posted as comment
```

### Validation Workflow (Claude)
```bash
# In PR comment, type: @claude-score
# Claude analyzes with same criteria
# Compare results with automated analysis
```

### Side-by-Side Comparison
1. Create a PR (automated analysis runs)
2. Comment `@claude-score` for Claude analysis
3. Compare the two scoring approaches
4. Look for patterns in differences

## Expected Differences

### Where Automated Analyzer Excels
- **Consistency**: Same logic applied every time
- **Speed at Scale**: Handles high PR volume
- **Metadata Integration**: Links to Linear tickets
- **Trend Analysis**: Consistent scoring for metrics

### Where Claude Scoring Excels
- **Context Understanding**: Better grasp of business logic
- **Nuanced Analysis**: Considers architectural implications
- **Flexibility**: Adapts to unique situations
- **Documentation Quality**: Better assessment of clarity

## Scoring Calibration

### Use Both Approaches To:
- **Validate Scoring Logic**: Are the scores generally aligned?
- **Identify Edge Cases**: Where do they disagree significantly?
- **Improve Automation**: Learn from Claude's reasoning
- **Quality Assurance**: Catch analyzer issues

### Red Flags (Large Differences)
- **Complexity**: >3 point difference suggests sizing issues
- **Risk**: >2 point difference indicates context misunderstanding
- **Work Type**: Different classifications need investigation
- **Impact**: >2.0 difference suggests scoring calibration issues

## Calibration Examples

### Well-Aligned Scoring
```
Automated: Complexity 6, Risk 5, Clarity 8, Impact 5.5
Claude:    Complexity 7, Risk 5, Clarity 7, Impact 5.8
→ Good alignment, minor interpretation differences
```

### Significant Divergence
```
Automated: Complexity 4, Risk 3, Clarity 6, Impact 3.6
Claude:    Complexity 7, Risk 8, Clarity 5, Impact 7.1
→ Major disagreement - investigate why
```

## Improvement Process

### Weekly Review
1. Compare 5-10 PR analyses from both systems
2. Identify patterns in scoring differences
3. Document edge cases and unusual scenarios
4. Adjust automated analyzer logic if needed

### Monthly Calibration
1. Run side-by-side analysis on 20+ PRs
2. Calculate correlation between scoring approaches
3. Update scoring criteria based on learnings
4. Document best practices from comparison

## Commands Reference

### Automated Analysis
- Triggered automatically on all PRs
- Updates comment on PR changes
- Applies labels for work type, complexity, risk
- Links to Linear tickets when found

### Claude Scoring
```bash
# Basic scoring request
@claude-score

# Scoring with specific focus
@claude-score Focus on architectural impact

# Scoring comparison request  
@claude-score Compare with automated analysis
```

## Troubleshooting

### If Scores Are Consistently Different
1. **Check PR Size**: Large PRs often cause divergence
2. **Review Context**: Claude sees more architectural context
3. **Validate Criteria**: Ensure both use same scoring scale
4. **Update Automation**: Improve Python analyzer logic

### If Claude Scoring Fails
1. **Check API Keys**: Ensure ANTHROPIC_API_KEY is configured
2. **Review Trigger**: Use exact phrase `@claude-score`
3. **Check Permissions**: Ensure workflow has PR write access
4. **Monitor Logs**: Check GitHub Actions logs for errors

## Success Metrics

### Good Calibration Indicators
- **Correlation >0.7**: Strong alignment between approaches
- **Mean Difference <1.5**: Scores are reasonably close
- **Classification Agreement >80%**: Work types mostly match
- **No Systematic Bias**: Neither consistently higher/lower

### Areas for Investigation
- **Large Complexity Differences**: Check size calculation
- **Risk Assessment Gaps**: Review architectural context
- **Work Type Mismatches**: Improve classification logic
- **AI Detection Variance**: Validate detection patterns

This dual approach gives us both reliable automation and intelligent validation, helping improve our scoring accuracy over time.