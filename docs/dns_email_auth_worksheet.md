# DNS & Email Authentication Worksheet

Purpose: Explicit, registrar- and provider-friendly templates for SPF, DKIM and DMARC for gamblingexcellence.com. Use this to paste directly into registrar DNS control panels.

Notes before you edit
- Do NOT apply changes until you have admin access to your DNS provider and can roll back if needed.
- Replace placeholders in <angle-brackets>.
- TTL: set to 3600 (1 hour) while testing; consider 86400 after stable.

1) SPF (Sender Policy Framework)
- Record type: TXT
- Host / Name: @
- TTL: 3600
- Value (examples):
  - If using Google Workspace: "v=spf1 include:_spf.google.com ~all"
  - If using Microsoft 365: "v=spf1 include:spf.protection.outlook.com -all"
  - If using external transactional email (e.g., Mailgun/SendGrid), include their include statements: e.g., "v=spf1 include:_spf.google.com include:sendgrid.net ~all"

SPF template (registrar-ready):
- Type: TXT
- Host: @
- Value: "v=spf1 <include:provider1> <include:provider2> ~all"

2) DKIM (DomainKeys Identified Mail)
- DKIM is usually provisioned from your mail provider. You will get a selector and an associated DNS record. Typical forms:
  - TXT record named: <selector>._domainkey
  - Example host: google._domainkey (for selector 'google')
  - TTL: 3600
  - Value: the long key string provided by provider, e.g. "v=DKIM1; k=rsa; p=<base64-public-key>"

DKIM checklist (provider flow):
1. In provider console (Google Workspace / Microsoft 365 / third-party), create/enable DKIM for `gamblingexcellence.com` and note the selector (e.g., `google` or `mail`).
2. Copy the DNS record name (`<selector>._domainkey`) and TXT value exactly.
3. Add TXT/CNAME record at registrar per provider instruction.
4. Wait 1–24 hours then enable DKIM signing in provider console.

3) DMARC (Domain-based Message Authentication, Reporting & Conformance)
- Purpose: collect aggregate reports and eventually enforce policy.
- Record type: TXT
- Host / Name: _dmarc
- TTL: 3600
- Monitoring (initial) template — start here:
  - Value: "v=DMARC1; p=none; pct=100; rua=mailto:dmarc-aggregate@gamblingexcellence.com; ruf=mailto:dmarc-forensic@gamblingexcellence.com; fo=1"

Enforce stage template (when comfortable):
  - Value: "v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc-aggregate@gamblingexcellence.com; ruf=mailto:dmarc-forensic@gamblingexcellence.com; fo=1"
  - Later (strict): "v=DMARC1; p=reject; rua=mailto:dmarc-aggregate@gamblingexcellence.com; pct=100; fo=1"

DMARC rollout sequence (recommended)
1. p=none for 7–14 days. Review aggregate reports for aligned sending sources.
2. Move to p=quarantine for 7–14 days (if misdirected mail remains low).
3. Move to p=reject when comfortable; continue monitoring.

4) DNS record examples (registrar copy/paste ready)
- SPF
  - Type: TXT
  - Host: @
  - TTL: 3600
  - Value: "v=spf1 include:_spf.google.com include:sendgrid.net ~all"
- DKIM (example — replace selector & key)
  - Type: TXT
  - Host: google._domainkey
  - TTL: 3600
  - Value: "v=DKIM1; k=rsa; p=<BASE64_PUBLIC_KEY_FROM_PROVIDER>"
- DMARC (monitoring)
  - Type: TXT
  - Host: _dmarc
  - TTL: 3600
  - Value: "v=DMARC1; p=none; pct=100; rua=mailto:dmarc-aggregate@gamblingexcellence.com"

5) Validation checklist (how to confirm records are working)
- After DNS change propagation (allow up to 1 hour for TTL=3600):
  1. Use `dig` or online DNS tools to confirm TXT records exist:
     - `dig TXT gamblingexcellence.com +short` (Windows: use online DNS checkers)
  2. Send a test email from the primary sending service to an external mailbox (Gmail) and view full headers.
     - Confirm SPF: "pass" or "neutral" in header (Authentication-Results).
     - Confirm DKIM: "pass" with selector indicated.
     - Confirm DMARC: alignment result in header.
  3. Use DKIM/DMARC analysis services or online tools (MXToolbox, dmarcian) to parse and validate.

6) Rollout notes & safety
- Always start DMARC in `p=none` to collect reports.
- If you see legitimate sending providers failing DKIM/SPF, add their include statements or configure their DKIM selectors.

7) Helpful placeholder records for registrar forms
- SPF (TXT):
  - Name/Host: @
  - Value: "v=spf1 include:_spf.google.com ~all"
- DKIM (TXT):
  - Name/Host: <selector>._domainkey
  - Value: "v=DKIM1; k=rsa; p=<base64-public-key>"
- DMARC (TXT):
  - Name/Host: _dmarc
  - Value: "v=DMARC1; p=none; rua=mailto:dmarc-aggregate@gamblingexcellence.com"
