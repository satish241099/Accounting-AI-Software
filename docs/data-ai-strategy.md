# Data & AI Strategy — Malaysia Accounting SaaS

**Version:** v0.1 · **Date:** 2026-10-21 · **Author:** Data Lead (Fullstack Forge)
**Status:** Proposal — input to the main Architecture & Compliance Design Doc.
**Audience:** CTO (decision owner), Backend Lead, Infrastructure Lead, Security Lead.

---

## 1. Scope

This brief covers the data and AI layer for the two data-intensive wedges in
`docs/competitive-analysis.md`:

- **W2 — AI bookkeeping copilot** (auto-categorisation, statement→journal suggestions, anomaly flags, cited compliance Q&A).
- **W3 — Migration importers** (AutoCount / SQL Account / UBS data import).

It deliberately **excludes** payroll (C3), SST engine internals (C2), and e-Invois submission mechanics (C1) — those are backend/compliance concerns. It **includes** the data plumbing those features depend on.

It does **not** treat "ML" as a product by itself. Every data capability below must reduce one of three costs: *time-to-first-books*, *compliance-deadline risk*, or *migration switching cost*.

## 2. Critique of the current plan (read this first)

The competitive analysis is strong on **market** evidence and thin on **data feasibility**. Three gaps I want corrected before build starts:

1. **"AI bookkeeping copilot" is currently a promise, not an architecture.** W2 is the lead differentiator but has no stated inference substrate, no evaluation criteria, and no accuracy bar. Without a stated bar, "AI categorisation" is unfalsifiable and will ship as an embarrassment. **Correction:** every AI feature ships with a golden-set evaluation harness (Sec. 6) and a stated precision floor *before* it is exposed to a user.
2. **Cold-start is unacknowledged.** We have zero proprietary training data and no customers. Any plan that assumes fine-tuned models on client books is fantasy at launch. **Correction:** Phase 1 is retrieval + rules + prompt, *not* training. Fine-tuning is a 2027+ option, contingent on volume and consent.
3. **Data residency vs. AI inference is an unresolved contradiction.** PDPA 2024 plus the project's ap-southeast-1 residency rule means client financial data cannot leave the region — which rules out most hosted third-party LLM APIs. The competitive analysis lists "AI" as a wedge without ever naming who performs inference. **Correction:** inference substrate is a **CTO decision that blocks W2** (Sec. 4).

A fourth, softer point: **W3 (migration) is undervalued.** It is rated W3 but it is the wedge that produces the *data* (historical transactions) that makes W2 trainable later. Migration importers should be sequenced **before or in parallel with** the copilot, not after — they are both a moat and our only future data source.

## 3. Data architecture baseline

**Principle: one Postgres cluster, tenant isolation above the app layer, three data zones.**

| Zone | Store | Purpose | Retention |
|---|---|---|---|
| **Transactional (OLTP)** | Postgres (RDS) | Ledger, journals, invoices, payroll refs, clients | Indefinite (statutory) |
| **Raw / immutable** | S3 object storage (ap-southeast-1, SSE-KMS) | Original uploaded files, importer source exports, bank statements, AI request/response archive | 7 years (audit) |
| **Curated / analytical** | Postgres read-replica schema + materialised views | Categorisation features, reconciliation aggregates, model eval sets | Rebuildable from raw |

Non-negotiables (all inherited from project memory, restated for the data layer):

- **Tenant context is a first-class column and a first-class query filter.** Every curated table carries `tenant_id`; RLS is defence-in-depth, not the primary control.
- **Firm edition introduces a second isolation axis**: `tenant_id` (the firm) *and* `client_id` (the client book). The e-Invois Intermediary workflow (W1) is the first consumer — no cross-client data leakage in batch submission or in AI features that touch a firm's client books.
- **Audit trail is append-only and immutable.** AI outputs that touch the ledger (suggested journals, category changes) are recorded as first-class audit rows with model id, prompt hash, input hash, confidence, and the human decision. If we cannot reconstruct *why* a journal was posted, the product is not audit-grade.
- **No client data in logs, traces, or analytics.** Strip at the instrumentation layer, not at the application layer.

**Recommendation:** do **not** introduce a warehouse/feature-store/dedicated vector DB at this stage. The analytical load here is small (thousands of SMEs, one firm tenant may hold thousands of client books) and Postgres + pgvector covers retrieval, feature serving, and eval-set storage. A separate OLAP stack is a 2027+ concern; adding it now buys complexity and residency surface for no gain.

## 4. Inference substrate — decision required (blocking W2)

| Option | Residency | Latency | Cost | Verdict |
|---|---|---|---|---|
| **Hosted 3rd-party LLM API (US/EU)** | ❌ Violates residency | Low | Low | **Reject** for any client data. Acceptable only for public-corpus work with no client content (e.g. LHDN/SST reference Q&A drafting). |
| **AWS Bedrock in-region (ap-southeast-1)** | ✅ if region pinned | Med | Med | **Candidate**, pending a written PDPA review of the exact model + subprocessor chain. |
| **Self-hosted open-weights model on EC2/EKS (ap-southeast-1)** | ✅ Full control | Med-high | Med-high (GPU) | **Candidate.** Best compliance posture; ops burden falls on Infrastructure Lead. |
| **Hybrid routing (small local model for classification + regional API for long-form reasoning)** | ✅ | Low for hot path | Low | **Preferred shape** if both candidates pass review — see below. |

**Recommended architecture (subject to Security + Legal sign-off):**

- **Hot path = self-hosted small open-weights model** (transaction categorisation, duplicate detection, field extraction from importer files). These are high-volume, low-latency, and deterministic-checkable. Local inference also removes per-token cost from the reconciliation loop.
- **Cold path = regional hosted model** (compliance Q&A with citations, journal-reasoning explanations, migration mapping review). Low volume, high reasoning quality needed, human reads the output anyway.
- **Never** let the model decide to post, file, or submit. It proposes; a human approves. This is not a UX nicety — it is the compliance answer to §2's PDPA/AML exposure, and it is also what makes the "always human-approved" claim in W2 defensible in sales conversations.

**Blocking dependencies:** Legal review of PDPA 2024 cross-border/subprocessor exposure; Security Lead review of prompt-injection surface on ingested bank statements and importer files; Infrastructure Lead confirmation that the chosen substrate can be pinned to ap-southeast-1 with no cross-region fallback.

## 5. Capability map → wedge → owner

| # | Capability | Wedge | Data needed | Owner | Phase |
|---|---|---|---|---|---|
| D1 | Bank statement ingestion + normalisation (CSV/MBFP/OFX/PDF→text) | W2 | Raw files in S3 | Data Engineer | P1 |
| D2 | Transaction auto-categorisation + rule override learning | W2 | Labelled journals per tenant | ML Engineer | P2 |
| D3 | Statement→journal suggestions with confidence + evidence | W2 | D1 + D2 | AI Engineer | P2 |
| D4 | Anomaly / duplicate / unusual-vendor flags | W2 | Ledger history | ML Engineer | P3 |
| D5 | Compliance Q&A with citations to LHDN/SST/SSM source text | W2 | Public regulatory corpus (no client data) | AI Engineer | P1 |
| D6 | Importer framework: AutoCount / SQL Account / UBS export parsers | W3 | Third-party file formats | Data Engineer | P1 |
| D7 | Importer mapping suggestions (source field → target chart of accounts) | W3 | D6 + canonical chart of accounts | AI Engineer | P2 |
| D8 | Eval harness + golden sets for every AI surface | all AI | Labelled fixtures | ML Engineer | P1 (must lead) |
| D9 | AI audit archive + explainability store | all AI | Prompt/output/decision logs | Data Engineer | P1 |
| D10 | Client-book feature store (curated, tenant-scoped) | W2 | D1–D4 outputs | Data Engineer | P2 |

**Sequencing note:** D8 (evaluation) is first, not last. Nothing in P2 ships before D8 exists.

## 6. Evaluation & quality bar

Every AI feature ships against a golden set with a **stated precision floor** agreed with the Backend Lead and documented in the feature's acceptance criteria. Proposed floors (to be ratified):

| Feature | Metric | Floor (P1) | Floor (P2) |
|---|---|---|---|
| D2 categorisation | top-1 accuracy on tenant chart of accounts | ≥ 85% | ≥ 92% |
| D3 journal suggestions | precision on suggested lines | ≥ 90% | ≥ 95% |
| D4 anomaly flags | precision on known-anomalous fixtures (recall may be low) | ≥ 80% | ≥ 85% |
| D5 compliance Q&A | citation-grounded answer rate + no-fabrication rate | 100% citation, ≥ 95% no-fabrication | same |
| D7 import mapping | field-mapping accuracy | ≥ 90% | ≥ 97% |

**Hard rules:**
- **Below-floor behaviour degrades to human-only.** The UI must show "no suggestion" rather than a low-confidence guess. A confident wrong journal is worse than no journal.
- **Every eval set is versioned and tenant-safe.** Golden sets are built from synthetic/fixture data or from explicitly consented, de-identified client data under a DUA — never from raw client books by default.
- **Regression gate in CI.** D8 runs on every prompt/template/model change; a drop below floor blocks the merge. Model and prompt versions are pinned in the audit archive, so any posted entry can be tied to the exact version that produced it.

## 7. Data/ML work plan for my department

**Phase 1 (foundations, parallel with backend scaffolding):**
- Data Engineer: D1 ingestion + raw zone layout + D6 importer framework for the two highest-volume formats (AutoCount, SQL Account) + D9 audit archive schema.
- ML Engineer: D8 eval harness + golden-set framework + baseline benchmark for D2 on synthetic Malaysian SME transaction shapes.
- AI Engineer: D5 compliance RAG over the public LHDN/SST/SSM corpus, with citation provenance; prompt library + version control conventions for the D9 archive.

**Phase 2 (copilot core, gated on CTO's substrate decision):**
- D2/D3 model + service behind the chosen inference substrate; tenant-scoped fine-tuning only where consent and volume allow.
- D10 feature store; D7 importer mapping suggestions.

**Phase 3 (depth):**
- D4 anomaly detection with per-tenant baselining; F1 monthly close analytics; F2 practice-level (firm) portfolio analytics across client books.

**Cross-cutting, owned by me:** evaluation floors, data residency enforcement, tenant isolation review of every curated table, and the model/prompt version registry.

## 8. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Hosted LLM used with client data → PDPA breach | Severe | Substrate decision (Sec. 4); provider-side no-training/no-retention contract terms; D9 audit archive |
| Model hallucinated SST rate → wrong tax on a filed invoice | Severe | SST/tax computation stays deterministic code, never model-generated; models classify and explain only |
| Prompt injection via ingested bank statement or importer file | High | Treat all ingested text as untrusted; strip/sandbox; injection-specific eval cases in D8 |
| Cross-client leakage in firm edition through AI context | Severe | `tenant_id` + `client_id` on every AI context assembly; RLS + eval cases asserting isolation |
| Cold start — no training data | Medium | Phase 1 = rules + retrieval; synthetic goldens; migration data (D6) as future fuel |
| Evaluation sets built from live client data without DUA | High | Fixture/synthetic by default; consent + de-identification required |
| Scope creep into payroll/SST engine | Medium | Explicit out-of-scope (Sec. 1); those routes to Backend Lead |

## 9. Decisions I need from the CTO

1. **Inference substrate** (Sec. 4) — blocks W2. Options: in-region Bedrock vs self-hosted open-weights vs hybrid. Needs Legal + Security + Infrastructure input.
2. **Mission/slice structure for the data & AI track** — I propose one mission, `M-DATA`, with slices: `S1 Foundations` (D6/D8/D9 + raw zone), `S2 Importer & Migration` (W3), `S3 Copilot Core` (D1–D3, W2), `S4 Assurance & Depth` (D4, eval gates, analytics). Features = the D-items above. Approve, or tell me to restructure before I create it — I have **not** created a mission unilaterally.
3. **W3 sequencing** — I argue importers (W3) land **before** copilot depth (W2), because they are the moat *and* the future data source. Confirm or overrule.
4. **Precision floors** (Sec. 6) — agree, or nominate owners to ratify per feature.

## 10. Open questions for the next validation pass

- Which importer formats matter most? (Assumption: AutoCount + SQL Account, by incumbent share. §4 of competitive analysis.)
- Do firms, not just SMEs, hold the books they migrate? If yes, D6 needs firm-level multi-book format support from day one.
- Is the compliance corpus for D5 licensed/permissible to embed and cite publicly? (Assumption: yes for LHDN/SST/SSM public guidance; must verify SSM/MBRS terms.)
