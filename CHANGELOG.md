# Changelog

All notable changes to the Golden Test System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Canary week auto-promotion system
- 7-day window evaluation for automatic threshold upgrades
- Consecutive failures safety net with escalation
- Comprehensive Slack notification system for weekly reports
- Dashboard integration for Canary 7-Day Window status

### Changed
- Enhanced notification system with canary/normal week differentiation
- Improved safety checks with automatic escalation on consecutive failures

## [v3.0-threshold-0.7] - 2025-08-29

### 🎉 Phase 3 Production Release

#### Major Achievements
- **Threshold Upgrade**: Successfully promoted from 0.5 to 0.7 (40% improvement)
- **Canary Week Completion**: 7-day monitoring period with all conditions met
- **Quality Metrics**: Achieved 85%+ pass rate, <5% flaky rate, ≤60% new fail ratio

#### Added
- **Canary Week System**: 7-day monitoring with enhanced criteria (85% vs 80%)
- **Auto-promotion Pipeline**: Automatic PR approval and merge on success
- **Weekly Slack Reports**: Rich notifications with KPI tables and action buttons
- **Shadow Evaluation**: Predictive analysis for threshold 0.7 impact
- **Comprehensive Dashboard**: Real-time KPI visualization with Streamlit
- **Safety Mechanisms**: Automatic rollback on consecutive failures

#### Enhanced
- **Normalization Engine**: NFKC, casefold, space compression, punctuation/unit mapping
- **Evaluator Improvements**: Similarity gate (0.92 threshold), numerical approximation, synonym expansion
- **Prompt Optimization**: Compound word preservation rules, particle exclusion
- **Root Cause Analysis**: Automatic classification with freshness tagging (NEW/REPEAT)

#### Quality Improvements
- **new_fail_ratio**: Reduced from 100% to 50% (50% improvement)
- **Predicted@0.7**: Maintained 60-70% stability
- **Flaky Rate**: Consistently <5% with retry mechanisms
- **Model Consistency**: Enhanced prompt engineering for compound words

#### Infrastructure
- **GitHub Actions**: Weekly automated checks with artifact preservation
- **Pre-commit Hooks**: Security scanning with gitleaks and detect-secrets
- **CI/CD Pipeline**: Comprehensive testing with unit, API, and golden tests
- **Monitoring**: Prometheus/Grafana integration for system metrics

#### Documentation
- **Operation Runbook**: Comprehensive canary week procedures
- **Testing Strategy**: Detailed golden test methodology
- **API Documentation**: Complete endpoint specifications
- **Troubleshooting**: Common issues and resolution procedures

### Technical Details

#### Normalization Rules Enhanced
```yaml
normalization:
  nfkc_enabled: True
  casefold_enabled: True
  space_compression: True
  punctuation_mapping:
    "［": "["
    "（": "("
  unit_mapping:
    "％": "%"
    "㌫": "%"

synonyms:
  "分析ダッシュボード":
    - "分析"
    - "ダッシュボード"
    - "解析画面"
```

#### Prompt Optimization Results
- **Before**: 複合語分割問題 (score: 0.25)
- **After**: 複合語保持ルール (score: 1.0)
- **Improvement**: 300% score increase for compound word cases

#### Canary Week Metrics
- **Evaluation Period**: 7 days continuous monitoring
- **Success Criteria**: 
  - Average pass rate ≥ 85%
  - Flaky rate < 5%
  - New fail ratio ≤ 60%
- **Safety Net**: Automatic rollback on 2 consecutive failures

### Migration Guide

#### From Phase 2 (0.5) to Phase 3 (0.7)
1. **Automatic**: System handles migration via canary week process
2. **Manual Verification**: Check dashboard for metrics confirmation
3. **Rollback Available**: `scripts/rollback_threshold.sh --from 0.7 --to 0.5`

#### Configuration Updates
- Update `tests/golden/config.yml` threshold to 0.7
- Verify normalization rules in `out/norm_rule_candidates.yaml`
- Check Slack webhook configuration for notifications

### Breaking Changes
- None - backward compatible upgrade

### Security
- Enhanced secret detection with detect-secrets baseline
- GitHub push protection for sensitive data
- Webhook URL security via GitHub Secrets

### Performance
- **Test Execution**: Optimized with retry mechanisms
- **Dashboard Loading**: Cached data for faster visualization
- **Notification Delivery**: Async processing for better responsiveness

### Known Issues
- Dashboard requires manual refresh for real-time updates
- Shadow evaluation limited to single threshold prediction
- Webhook notifications require manual secret configuration

### Contributors
- AI Assistant: System design and implementation
- User: Requirements definition and validation

---

## [v2.0-threshold-0.5] - 2025-08-22

### Added
- Basic golden test framework
- Threshold management system
- Weekly observation logging
- Initial normalization rules

### Changed
- Upgraded from threshold 0.3 to 0.5
- Enhanced keyword extraction

## [v1.0-threshold-0.3] - 2025-08-15

### Added
- Initial golden test implementation
- Basic evaluator with Jaccard similarity
- Simple test case management
- Manual threshold configuration

---

*This changelog is automatically maintained as part of the Golden Test System.*
