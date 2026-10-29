# SRE Foundation Handoff Templates

## Purpose
Define four handoff templates that compile necessary information for SRE deliverables, making handoffs self‑contained and auditable.

## Scope
SRE Foundation slice under mission M-MVKTMUFU-000V-OQTS (Malaysia Accounting SaaS Core Foundation).

## 1. Observability Stack Handoff

| Field | Description |
|-------|-------------|
| `component` | Component name (e.g., `logging`, `metrics`, `tracing`). |
| `version` | Version number of the component. |
| `deployment_env` | Target environment (`dev`, `staging`, `prod`). |
| `log_schema_version` | Schema version referenced in `docs/sre/standards/log-schema.md`. |
| `metrics_catalog_ref` | Link to metrics catalogue file/path. |
| `tracing_config_ref` | Link to tracing configuration. |
| `alert_rules_ref` | Link to alert rules definition. |
| `retention_days` | Log retention period in days. |
| `pdpa_redaction_verified` | Boolean. |
| `correlation_id_propagation_verified` | Boolean. |
| `test_report_link` | Link to test result. |
| `owner` | Person or team. |
| `date` | Hand-off date. |

## 2. SLO Handoff

| Field | Description |
|-------|-------------|
| `slo_id` | SLA ID. |
| `service` | Service name. |
| `target` | Desired target value. |
| `window` | Monitoring window. |
| `error_budget_remaining_pct` | Remaining budget. |
| `burn_rate_alerts_configured` | Boolean. |
| `measurement_source` | Origin of metrics. |
| `exclusion_windows` | Time windows to exclude. |
| `review_cadence` | Cadence in days. |
| `owner` | Owner. |
| `date` | Date. |

## 3. Incident Response Handoff

| Field | Description |
|-------|-------------|
| `runbook_id` | Runbook ID. |
| `severity` | Severity level (SEV‑1, …). |
| `trigger_scenario` | Description of trigger. |
| `detection_method` | How we detect the incident. |
| `mitigation_summary` | Summary of mitigation steps. |
| `recovery_verification` | Verification steps. |
| `postmortem_link` | Link to postmortem. |
| `action_items_open` | List of pending action items. |
| `on_call_contact` | On‑call contact. |
| `owner` | Owner. |
| `date` | Date. |

## 4. Deployment Safety Handoff

| Field | Description |
|-------|-------------|
| `deployment_id` | Deployment ID. |
| `canary_config_ref` | Canary config. |
| `feature_flags_toggled` | Feature flags toggled. |
| `migration_strategy` | Expand/contract. |
| `rollback_time_target_s` | Seconds to rollback. |
| `chaos_experiment_ref` | Chaos experiment reference. |
| `pre_deployment_checklist_passed` | Boolean. |
| `slo_status_at_deploy` | SLO status at deploy. |
| `error_budget_at_deploy` | Error budget at deploy. |
| `on_call_verified` | On‑call verified. |
| `owner` | Owner. |
| `date` | Date. |

## 5. Template Usage

1. Create a new markdown file in the appropriate `docs` sub‑folder.
2. Copy the relevant section from this file.
3. Populate field placeholders with real data.
4. Save file and reference it in PR description.
5. Document waiver if any fields are omitted due to emergency.

## References
- Mission M-MVKTMUFU-000V-OQTS (Malaysia Accounting SaaS Core Foundation)
- KB-023 (Observability Stack)
- KB-024 (SLOs & Error Budgets)
- KB-026 (Incident Response & Runbooks)
- KB-028 (Production Readiness & Deployment Safety)
