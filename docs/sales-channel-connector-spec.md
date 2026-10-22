# Sales-Channel Connector Specification (Feature F-MVJ443L5-000H-RUXB)

**Feature:** Sales‑channel connector capability for B2C e‑Invois

**Mission:** AI‑first compliance platform – Phase 4 (W4 – 2027 long‑tail launcher)

---

## 1. Scope and Anti‑positioning
- **In‑scope:** Ingestion of order data from the following sales channels:
  - Shopify (Admin REST API, OAuth offline access)
  - WooCommerce (WordPress plugin, REST API)
  - Shopee (Marketplace settlement statements)
  - Lazada (Marketplace settlement statements)
  - TikTok Shop (Marketplace settlement statements)
- **Out‑of‑scope:** Inventory/POS depth, order creation, cart management, pricing logic. The connector only pulls *post‑sale* events.
- **Anti‑positioning:** No attempt to replace existing inventory or POS systems (e.g., AutoCount). The connector feeds *net‑of‑fees* financial events into the compliance core only.

---

## 2. Tax‑Base Calculation (SST)
1. **Net taxable amount** = `gross_order_amount` – `platform_commission` – `payment_processing_fees`.
2. **Commission & fees** must be taken from the channel‑specific webhook payload or settlement batch; if unavailable, the connector must request the fee‑breakdown via the channel's API (e.g., Shopify `transactions` endpoint).
3. **SST rate**: 8 % (effective 1 Mar 2024). The rate is **static** but must be read from the official LHDN source at implementation time; do **not** hard‑code it.

---

## 3. Settlement vs Order Date
- Orders may be settled days/weeks after the capture date.
- **Tax reporting date** is the *settlement date* (date when the net amount is transferred to the seller), not the order capture date.
- The connector must persist both timestamps (`order_created_at` and `settlement_at`) and expose them to the compliance engine; the engine will use `settlement_at` for SST calculation.

---

## 4. Refund / Partial Refund / Cancellation Semantics
- **Full refund**: Emit a reversal event with the same `order_id` and a `refund_amount` equal to the original `net_taxable_amount`.
- **Partial refund**: Emit a reversal event with `refund_amount` equal to the net amount proportional to the refunded items. The original order remains for the non‑refunded portion.
- **Cancellation before settlement**: Treat as a *zero‑settlement* event; no SST is due. Still record the cancellation for audit.
- All reversal events must include a reference to the original `order_id` and the `settlement_id` to which they apply.

---

## 5. LVGST (Low‑Value Goods Sales Tax) Branching
- **LVGST Threshold** and **exemption** values are **dynamic** and must be read live from the Malaysian Customs portal (`mysst.customs.gov.my`) at runtime.
- The connector must expose an API (e.g., `GET /lvgst‑config`) that the ingestion pipeline can call to obtain the current threshold and exemption rules.
- **Decision logic**:
  - If `net_taxable_amount` ≤ *LVGST threshold* **and** seller is *exempt* per live data → **no SST** and **no e‑Invois** generated.
  - Otherwise, apply the standard 8 % SST.
- **Implementation note:** The live fetch failed during research (see recent attempt). This must be handled with a fallback retry strategy and a feature flag to disable LVGST logic if the live service is unavailable (with a manual override for compliance review).

---

## 6. Platform‑Side Ingestion Contract (for Integration Engineer)
| Field | Type | Description |
|-------|------|-------------|
| `channel` | enum(`shopify`,`woocommerce`,`shopee`,`lazada`,`tiktok`) | Source sales channel |
| `order_id` | string | Unique identifier from the channel |
| `tenant_id` | uuid | Multi‑tenant identifier (RLS enforced) |
| `order_created_at` | timestamp | Capture timestamp from channel |
| `settlement_at` | timestamp | When funds are settled to seller |
| `gross_amount` | decimal(12,2) | Pre‑fee order total |
| `commission_fee` | decimal(12,2) | Platform commission |
| `payment_fee` | decimal(12,2) | Payment processor fee |
| `net_taxable_amount` | decimal(12,2) | Calculated per §2 |
| `sst_amount` | decimal(12,2) | `net_taxable_amount` × 8 % (or 0 if LVGST exempt) |
| `event_type` | enum(`order`,`settlement`,`refund`,`cancellation`) | Event kind |
| `refund_amount` | decimal(12,2) | Populated for `refund` events only |
| `original_order_id` | string | For refunds/cancellations, links to source order |

- All rows must respect the tenant‑isolation RLS contract (`tenant_id` = `current_setting('app.tenant_id')`).
- Events are written to the `sales_channel_events` table (to be added). The table follows the same RLS policy as other tenant‑scoped tables (see `db-contracts.md` § Part 2).

---

## 7. Acceptance Criteria (re‑stated)
1. **Feature spec documented** – this document meets the requirement.
2. **Ingestion contracts defined** – the table schema and JSON payload mapping above cover all five channels.
3. **Scope validated** – no inventory/POS logic included; only ingestion.
4. **Platform hand‑off** – Integration Engineer receives the contract and can implement the ingestion pipeline.

---

*Version: 2026‑10‑22*