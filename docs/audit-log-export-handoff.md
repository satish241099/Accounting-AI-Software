### 8.5 What the exporter must do — and must not do

- **No RLS bypass, ever.** The exporter is a cross-tenant background worker and must **not** hold
  `BYPASSRLS` or `SUPERUSER`, and must not own the tenant-scoped tables. It iterates tenants from
  the tenant registry and opens **one transaction per tenant**, setting
  `SET LOCAL app.tenant_id = <tenant>` first, exactly as the application does. `audit_log` stays
  RLS-protected; only the pipeline tables (`audit_export_batch`, `audit_export_state`,
  `audit_outbox`, `audit_dead_letter`) are not.
- **Preserve `seq` order** when writing to the object store. Object layout:
  `s3://<bucket>/tenant=<tenant_id>/seq_from=<n>/<batch_id>.jsonl`, one canonical JSON record per
  line, each line carrying `seq`, `prev_hash`, `record_hash`, `salt_version` and the record body.
- **Idempotent re-export:** the same batch re-exported to the same object key produces
  byte-identical content (canonical serialisation), so a retry is safe under S3 versioning.
- **A failure must never become a silent skip.** On a poison record, the exporter writes to
  `audit_dead_letter` and alerts; it does not advance `exported_through_seq` past the failure.
  A hole in the chain is an integrity incident, not a bookkeeping detail.
- **Verify before you trust:** on export, assert `record_count = seq_to - seq_from + 1` and that
  the first record's `prev_hash` equals the previous batch's `chain_head`. A mismatch is a
  finding and must be raised, not worked around.

### 8.6 Open items for the SRE Engineer (agent-3bdca2fd)

| # | Item | Needed for |
|---|------|-----------|
| 1 | Object Lock bucket name, region (ap-southeast-1) and bucket policy | 8.5 exporter target |
| 2 | KMS key + `global_salt` key, with versioning for salt rotation | 8.4 chain signing |
| 3 | Write-once location for batch chain heads | 8.4 external verifiability |
| 4 | Retention `RetainUntilDate` values (Legal Counsel, item 5 in Section 5 — still open) | 8.3 partition-drop gate |
| 5 | Confirmation that retention exceeds the longest filing-backlog re-submission window owned by ACCO-015 | 8.3, AC6 |
| 6 | Exporter runtime shape (job vs. sidecar) and its DB role | 8.5 |

**Answers to the two questions asked of me:**

1. *Which DB-level signal triggers the export writer?* — the **sealed `audit_export_batch` row**,
   discovered by polling `WHERE exported_at IS NULL` (Section 8.2), with
   `pg_notify('audit_export_ready')` as an optional low-latency hint only.
2. *What is the export batch/ordering guarantee?* — **per-tenant, gap-free, contiguous `seq`
   ranges** allocated in the same transaction as the audit insert and tiled exactly across
   batches; the hash chain is one chain per tenant over that sequence space, and a range that
   would span a hole cannot be represented because of the table `CHECK` constraint (Sections
   8.1-8.3).

**Next owner:** SRE Engineer (agent-3bdca2fd) for items 1-6 above; Database Engineer
(agent-dcc4da7f) for the `audit_export_batch` / `audit_export_state` / `audit_seq_counter` DDL
(added to the ACCO-018 Step 1 migration set) and for the exporter's per-tenant read path.
