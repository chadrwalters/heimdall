# North Star Metrics - Validation Procedures

Comprehensive procedures for validating the methodology, data quality, and accuracy of the North Star Metrics framework.

## Table of Contents

1. [Validation Overview](#validation-overview)
2. [Automated Validation](#automated-validation)
3. [Manual Validation](#manual-validation)
4. [Methodology Validation](#methodology-validation)
5. [Data Quality Checks](#data-quality-checks)
6. [Success Metrics](#success-metrics)
7. [Continuous Validation](#continuous-validation)

## Validation Overview

### Validation Principles

1. **Accuracy**: AI classifications should align with human assessment 80%+ of the time
2. **Consistency**: Similar work should receive similar scores across runs
3. **Completeness**: All data should be processed without significant gaps
4. **Reliability**: System should handle errors gracefully and recover properly
5. **Transparency**: Methodology should be explainable and auditable

### Validation Types

| Type | Frequency | Purpose | Automation Level |
|------|-----------|---------|------------------|
| **Automated Validation** | Every run | Data quality, calculations, patterns | Fully automated |
| **Manual Validation** | Weekly/Monthly | AI classification accuracy | Human review |
| **Methodology Validation** | Quarterly | Overall approach effectiveness | Mixed |
| **Performance Validation** | Monthly | Speed, cost, reliability | Automated |

## Automated Validation

### Running Automated Validation

```bash
# Validate a recent analysis
python scripts/validation/validate_methodology.py unified_pilot_data.csv

# Custom validation with larger sample
python scripts/validation/validate_methodology.py \
  unified_pilot_data.csv \
  --sample-size 50 \
  --output-dir validation_results \
  --log-level DEBUG

# Validate using Just
just validate-analysis unified_pilot_data.csv
```

### Validation Checks

#### 1. Impact Score Calculation
Verifies that impact scores are calculated correctly:
```
Impact Score = (Complexity × 0.4) + (Risk × 0.5) + (Clarity × 0.1)
```

**Validation Criteria**:
- ✅ All calculations within 0.01 margin of error
- ✅ All scores within valid range (1-10)
- ⚠️ Less than 5% calculation errors acceptable
- ❌ Any systematic calculation errors

#### 2. AI Detection Patterns
Validates AI assistance detection accuracy:

**Pattern Checks**:
- Co-authorship markers (`co-authored-by: github copilot`)
- Tool mentions (`generated with claude`, `cursor.ai`)
- AI developer overrides from `config/ai_developers.json`

**Validation Criteria**:
- ✅ AI detection rate 10-80% (organization dependent)
- ✅ Override system working correctly
- ⚠️ Less than 10% pattern inconsistencies
- ❌ AI rate below 5% or above 95% (likely detection issues)

#### 3. Work Type Classification
Validates work type assignments:

**Classification Checks**:
- Consistency with complexity scores
- Suspicious patterns (high complexity "Chore", low complexity "New Feature")
- Distribution across work types

**Validation Criteria**:
- ✅ Work type distribution reasonable for organization
- ✅ Complexity scores align with work types
- ⚠️ Less than 10% suspicious classifications
- ❌ Any work type completely missing or dominant (>80%)

#### 4. Process Compliance
Validates Linear ticket detection:

**Compliance Checks**:
- Ticket ID extraction from PR titles/bodies
- Ticket format patterns (ENG-123, PROJ-456, etc.)
- Process compliance rates

**Validation Criteria**:
- ✅ Process compliance rate appropriate for organization
- ✅ Ticket patterns correctly identified
- ⚠️ Compliance rate below 60% may indicate process issues
- ❌ No tickets detected (likely extraction failure)

### Interpreting Automated Results

#### Validation Report Structure
```json
{
  "validation_metadata": {
    "timestamp": "2025-01-15T10:30:00",
    "total_records": 1234,
    "sample_size": 20
  },
  "impact_score_validation": {
    "calculation_errors": [],
    "outliers": [],
    "score_distribution": {...}
  },
  "ai_detection_validation": {
    "ai_assisted_count": 456,
    "pattern_consistency": [],
    "override_analysis": {...}
  },
  "summary": {
    "critical_issues": 0,
    "warnings": 2,
    "recommendations": [...]
  }
}
```

#### Status Indicators

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| ✅ **EXCELLENT** | 0 critical issues, <5 warnings | Continue monitoring |
| ⚠️ **GOOD** | 0 critical issues, 5-20 warnings | Review recommendations |
| ❌ **NEEDS ATTENTION** | 1-5 critical issues | Address issues before next run |
| 🚨 **CRITICAL** | >5 critical issues | Stop analysis, investigate methodology |

## Manual Validation

### Manual Validation Process

#### 1. Sample Selection
The validation script automatically generates a stratified sample:

```bash
# Generate sample for manual validation
python scripts/validation/validate_methodology.py unified_pilot_data.csv --sample-size 20
```

This creates `manual_validation_sample_TIMESTAMP.csv` with:
- Representative work types
- Mix of AI-assisted and manual work
- Various complexity levels
- Recent and older records

#### 2. Manual Review Template

For each sampled record, evaluate:

```csv
source_id,work_type_ai,work_type_manual,complexity_ai,complexity_manual,risk_ai,risk_manual,clarity_ai,clarity_manual,ai_assisted_ai,ai_assisted_manual,notes
PR-1234,New Feature,New Feature,8,7,6,6,9,8,true,true,Good classification but slightly overestimated complexity
```

#### 3. Review Guidelines

**Work Type Classification**:
- **New Feature**: Adds new functionality, user-facing capabilities
- **Bug Fix**: Fixes existing functionality, resolves issues
- **Refactor**: Improves code structure without changing functionality
- **Testing**: Adds/improves tests, test infrastructure
- **Documentation**: Updates docs, comments, READMEs
- **Chore**: Maintenance, dependency updates, tooling

**Scoring Guidelines (1-10 scale)**:

**Complexity Score**:
- 1-3: Simple changes (typos, single line fixes, config updates)
- 4-6: Moderate changes (small features, straightforward bug fixes)
- 7-8: Complex changes (significant features, architectural changes)
- 9-10: Very complex (major refactors, complex algorithms, breaking changes)

**Risk Score**:
- 1-3: Low risk (documentation, tests, non-critical paths)
- 4-6: Medium risk (standard features, known patterns)
- 7-8: High risk (performance changes, external integrations)
- 9-10: Very high risk (core system changes, security-related)

**Clarity Score**:
- 1-3: Unclear (poor descriptions, no context, confusing changes)
- 4-6: Adequate (basic description, some context)
- 7-8: Clear (good description, clear intent, well-documented)
- 9-10: Excellent (comprehensive description, full context, exemplary)

**AI Assistance Detection**:
- Check commit messages for AI tool mentions
- Look for co-authorship indicators
- Consider coding patterns (rapid development, consistent style)
- Review against known AI users in team

#### 4. Manual Validation Analysis

```python
# Analyze manual validation results
import pandas as pd

# Load manual validation
manual = pd.read_csv('manual_validation_sample_with_reviews.csv')

# Calculate agreement rates
work_type_agreement = (manual['work_type_ai'] == manual['work_type_manual']).mean()
complexity_agreement = (abs(manual['complexity_ai'] - manual['complexity_manual']) <= 1).mean()
ai_agreement = (manual['ai_assisted_ai'] == manual['ai_assisted_manual']).mean()

print(f"Work Type Agreement: {work_type_agreement:.2%}")
print(f"Complexity Agreement (±1): {complexity_agreement:.2%}")
print(f"AI Detection Agreement: {ai_agreement:.2%}")
```

### Manual Validation Success Metrics

| Metric | Target | Good | Needs Improvement |
|--------|--------|------|-------------------|
| Work Type Agreement | 85%+ | 75-84% | <75% |
| Complexity Agreement (±1) | 80%+ | 70-79% | <70% |
| Risk Agreement (±1) | 75%+ | 65-74% | <65% |
| Clarity Agreement (±1) | 70%+ | 60-69% | <60% |
| AI Detection Agreement | 90%+ | 80-89% | <80% |

## Methodology Validation

### Quarterly Methodology Review

#### 1. Data Collection
Collect data over a 3-month period:

```bash
# Monthly snapshots
python main.py --org company --mode full --days 30 --output-dir q1-jan
python main.py --org company --mode full --days 30 --output-dir q1-feb  
python main.py --org company --mode full --days 30 --output-dir q1-mar

# Quarterly analysis
python scripts/validation/quarterly_analysis.py q1-*
```

#### 2. Trend Analysis

**Consistency Checks**:
- Score distributions remain stable over time
- Work type patterns align with development focus
- AI adoption trends are logical
- Process compliance improves over time

**Code Examples**:
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load quarterly data
q1_jan = pd.read_csv('q1-jan/unified_pilot_data.csv')
q1_feb = pd.read_csv('q1-feb/unified_pilot_data.csv')
q1_mar = pd.read_csv('q1-mar/unified_pilot_data.csv')

# Compare score distributions
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

q1_jan['impact_score'].hist(ax=axes[0], title='January', bins=20)
q1_feb['impact_score'].hist(ax=axes[1], title='February', bins=20)
q1_mar['impact_score'].hist(ax=axes[2], title='March', bins=20)

plt.tight_layout()
plt.savefig('quarterly_score_distribution.png')
```

#### 3. Comparative Analysis

**Cross-Team Validation**:
- Compare similar work across different teams
- Identify systematic biases
- Validate scoring consistency

**External Validation**:
- Compare with industry benchmarks when available
- Validate against other productivity metrics
- Cross-reference with team velocity data

#### 4. Methodology Adjustments

Based on validation findings, consider:

**AI Prompt Tuning**:
```python
# Test different prompts on same data
from src.analysis.prompt_engineer import PromptEngineer

pe = PromptEngineer()
# Test variations and compare results
```

**Scoring Weight Adjustments**:
```python
# Test different impact score weightings
def calculate_impact_score(complexity, risk, clarity, c_weight=0.4, r_weight=0.5, cl_weight=0.1):
    return complexity * c_weight + risk * r_weight + clarity * cl_weight

# Compare with current methodology
```

**AI Detection Improvements**:
```python
# Add new patterns to detect_ai_assistance()
new_patterns = [
    ("cursor ai", "Cursor"),
    ("ai pair programming", "Unknown AI Tool")
]
```

## Data Quality Checks

### Automated Data Quality Validation

#### 1. Completeness Checks
```bash
# Check for missing data
python -c "
import pandas as pd
df = pd.read_csv('unified_pilot_data.csv')

# Check completeness
completeness = {}
for col in df.columns:
    non_null_pct = (df[col].notna().sum() / len(df)) * 100
    completeness[col] = non_null_pct
    if non_null_pct < 95:
        print(f'WARNING: {col} only {non_null_pct:.1f}% complete')

print(f'Overall completeness: {sum(completeness.values())/len(completeness):.1f}%')
"
```

#### 2. Consistency Checks
```bash
# Check data consistency
python scripts/validation/check_data_consistency.py unified_pilot_data.csv
```

#### 3. Anomaly Detection
```bash
# Detect anomalies in scores and patterns
python scripts/validation/detect_anomalies.py unified_pilot_data.csv
```

### Data Quality Metrics

| Check | Description | Target | Action if Failed |
|-------|-------------|--------|------------------|
| **Completeness** | All required fields populated | 98%+ | Investigate extraction logic |
| **Uniqueness** | No duplicate records | 100% | Check deduplication logic |
| **Validity** | All scores in valid ranges | 99%+ | Review analysis engine |
| **Consistency** | Logical relationships maintained | 95%+ | Check business rules |
| **Timeliness** | Data reflects recent activity | Current | Verify extraction dates |

### Common Data Quality Issues

#### 1. Missing Data
**Symptoms**: Null values in critical fields
**Causes**: API failures, extraction errors, parsing issues
**Resolution**: 
```bash
# Re-run extraction for affected date range
python main.py --org company --mode full --days 7 --force
```

#### 2. Duplicate Records
**Symptoms**: Same PR/commit appearing multiple times
**Causes**: State management issues, extraction overlap
**Resolution**:
```bash
# Reset state and re-run
python -c "
from src.config.state_manager import StateManager
sm = StateManager()
sm.reset_state()
"
python main.py --org company --mode full --days 7
```

#### 3. Score Outliers
**Symptoms**: Scores outside 1-10 range
**Causes**: Analysis engine errors, prompt issues
**Resolution**: Review and fix analysis logic

#### 4. Classification Errors
**Symptoms**: Work misclassified consistently
**Causes**: AI prompt issues, insufficient context
**Resolution**: Adjust prompts, improve context preparation

## Success Metrics

### Overall Framework Success

#### Quantitative Metrics

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| **AI Classification Accuracy** | 80%+ | Manual validation agreement |
| **Processing Reliability** | 99%+ | Successful runs / total runs |
| **Data Completeness** | 98%+ | Records processed / expected |
| **Performance** | <30 min | Total pipeline execution time |
| **Cost Efficiency** | <$0.10/record | Anthropic API costs |

#### Qualitative Metrics

| Metric | Assessment Method |
|--------|-------------------|
| **User Satisfaction** | Quarterly surveys with stakeholders |
| **Actionability** | Number of decisions informed by metrics |
| **Adoption** | Usage frequency and user base growth |
| **Trust** | Confidence in data for decision making |

### Methodology Effectiveness

#### Business Impact Metrics

- **ROI Measurement**: Ability to quantify AI tool ROI
- **Process Improvement**: Compliance rate improvements
- **Team Insights**: Actionable team performance data
- **Strategic Planning**: Data-driven development decisions

#### Technical Quality Metrics

- **Consistency**: Score stability across similar work
- **Sensitivity**: Ability to detect meaningful differences
- **Specificity**: Accurate work type classification
- **Robustness**: Performance across different organizations

## Continuous Validation

### Monitoring Strategy

#### 1. Daily Monitoring
```bash
# Automated daily validation
0 7 * * * cd /path/to/metrics && python scripts/validation/daily_check.py
```

#### 2. Weekly Reviews
- Review automated validation reports
- Spot-check recent classifications
- Monitor API usage and costs
- Check error rates and recovery

#### 3. Monthly Analysis
- Manual validation sample review
- Trend analysis
- Performance optimization
- Cost analysis

#### 4. Quarterly Assessment
- Comprehensive methodology review
- Cross-team validation
- External benchmark comparison
- Methodology improvements

### Validation Dashboard

Create a monitoring dashboard tracking:

```python
# Example dashboard metrics
dashboard_metrics = {
    "data_quality": {
        "completeness_rate": 0.98,
        "error_rate": 0.02,
        "processing_time": "25 minutes"
    },
    "methodology_accuracy": {
        "ai_classification_agreement": 0.83,
        "work_type_agreement": 0.78,
        "score_consistency": 0.85
    },
    "business_metrics": {
        "ai_adoption_rate": 0.67,
        "process_compliance": 0.72,
        "team_satisfaction": 4.2
    }
}
```

### Continuous Improvement Process

1. **Monitor**: Daily automated validation
2. **Analyze**: Weekly trend analysis
3. **Validate**: Monthly manual reviews
4. **Improve**: Quarterly methodology updates
5. **Measure**: Track improvement over time

### Alerting and Response

#### Alert Conditions
- Validation failure rate > 5%
- Score calculation errors detected
- AI detection rate outside normal range
- Process compliance drop > 10%
- Processing time increase > 50%

#### Response Procedures
1. **Immediate**: Stop automated runs, investigate
2. **Short-term**: Fix issues, resume operations
3. **Medium-term**: Implement preventive measures
4. **Long-term**: Update methodology based on learnings

---

For more information:
- [Setup Guide](setup-guide.md) - Installation and configuration
- [Usage Guide](usage-guide.md) - Running analysis and interpreting results
- [Configuration Reference](configuration-reference.md) - Detailed settings
- [Troubleshooting Guide](troubleshooting.md) - Problem resolution