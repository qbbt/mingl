# Decision Wave Engine — Decisions Captured + Remaining Open Questions

This document is now split into:
1. **Confirmed decisions from founder input** (locked for MVP planning)
2. **Remaining open questions** (only what is still ambiguous)

---

## Confirmed Decisions (Locked)

### 1) Execution + brokerage scope
- MVP should move toward **execution hooks with IBKR** (Interactive Brokers).
- Recommendation-only can be used as an interim mode, but IBKR integration is a target requirement.

### 2) Notification channel priority
- Implement **email first** for out-of-band notifications.
- Keep architecture pluggable for later **push, SMS, webhook** channels.

### 3) Manual input UX
- Manual notes must be **parseable with guided structured fields**, not only free text.
- Required fields for manual prediction/annotation should include:
  - confidence
  - estimated_actual_timestamp
  - timestamp_margin_of_error
  - optional rationale/explanation

### 4) Ranking profiles + control behavior
- Provide both **manual and automatic** ranking behavior.
- Auto mode should be default (or near-default) with a clear dropdown/toggle.
- Top baseline profiles should emphasize **risk/reward** and **growth**.
- Ranking function must remain **fully customizable**.

### 5) Indicator/function customization
- Need support for **powerful arbitrary statistical + visual custom functions**, including derived metrics and overlays on wave charts.
- Prioritize expressive capability over restrictive templates.

### 6) Data resolution + retention
- Design toward **subsecond readiness**, with target use cases needing near-100ms decision granularity.
- Retain high-resolution local data for at least:
  - **1 day minimum** before downsampling,
  - target **up to 2 weeks** where feasible (storage-aware).

### 7) Correlation + causal scope
- Automated causal-edge proposals are required (can phase in after MVP core).
- Provide entity-level ranking views for strongest relationships (e.g., top 10 / top 100 correlations/causal candidates).

### 8) Accuracy governance + user overrides
- Use thresholding around prediction miss (e.g., 1-2 standard deviations) for warning/downweight logic.
- User overrides are always allowed (do not block input).
- If override performance degrades consistently, issue warnings and request explanation field.
- Influence decay for underperforming overrides should be configurable.

### 9) Platform expansion priority
- After web MVP, prioritize **iPhone-friendly access** as soon as practical.
- A strong responsive web landscape mode may be acceptable as transitional step.

### 10) Privacy + deployment model
- Start **local-first, single-user**, lightweight footprint.
- Add at-rest encryption when practical, or at least include encryption-ready framework hooks.

---

## Remaining Open Questions (Need Final Decision)

1. **IBKR integration sequence**
   - Should we ship with paper-trade hooks first, then live execution?
   - Or include live execution switch in v0.1 behind explicit safety gates?

2. **Custom function sandbox model**
   - Preferred first implementation:
     - Python plugin files,
     - formula DSL,
     - or both (safe DSL for UI + Python for advanced users)?

3. **Subsecond storage strategy**
   - For 100ms-class data, confirm preferred default:
     - lossless local append log + periodic downsample,
     - or multi-tier store (hot cache + compressed history).

4. **Email provider for MVP alerts**
   - Preferred first provider: SMTP relay, SendGrid, SES, Postmark?

5. **iPhone-first packaging path**
   - Preferred path after responsive web:
     - PWA,
     - React Native wrapper,
     - or native iOS app.
