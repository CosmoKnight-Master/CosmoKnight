# Business Contact Setup Runbook

Purpose: A one-day, manual-execution runbook to set up Gambling Excellence business contact channels (email inboxes, phone, published contact points) with automation-ready checklists and decision guidance.

Context & assumptions
- Domain: gamblingexcellence.com
- Do NOT create accounts or modify live DNS in this runbook — follow steps and prepare records, then apply when ready.
- Time zone: US/Pacific (PST/PDT). Date used for references: 2026-03-02 (accessed resources).

Estimated total time: 4–6 hours (depends on provider familiarity)

High-level sequence (ordered)
1. Plan & choose providers — 15–30 minutes
2. Create business accounts and inboxes (Google Workspace or Microsoft 365 recommended) — 30–60 minutes
3. Prepare DNS records for email auth (SPF/DKIM/DMARC) — 30 minutes
4. Provision business phone (Google Voice or alternate) and configure call flow — 30–60 minutes
5. Publish contact details (website/footer/receipts) — 15–30 minutes
6. QA end-to-end tests and track issues — 30–60 minutes

Decision gate: Google Voice Starter vs Standard
- Reference: Google Workspace: Voice product page — https://workspace.google.com/products/voice/ (accessed 2026-03-02).
- Guidance: choose Starter if you need a single basic business number for a small team (<5 people) with basic calling and voicemail. Choose Standard if you require advanced features used by growing teams: ring groups, call transfer between users, desk phone support, and more detailed reporting. If you need enterprise-level features (advanced reporting, large seat counts, international trunking), consider higher tiers or a dedicated telephony provider.
- When to pick Starter: sole founder or micro-team that needs a phone number for outbound/inbound calls, low monthly spend, no complex routing.
- When to pick Standard: multiple agents, need for ring groups, shared voicemails, basic IVR, and central admin control.

Provider decision checklist (pick one before proceeding)
- Email host: Google Workspace (recommended), Microsoft 365, or other hosted mail provider.
- Phone: Google Voice for Google Workspace (recommended if using Google Workspace), or Twilio/Grasshopper/Nextiva for richer PBX features.

Detailed manual steps

1) Create inboxes: `support@`, `billing@`, `legal@`
- Choose implementation model (pick one):
  - Separate paid user accounts (e.g., support@example.com as a separate Workspace user). Pros: full mailbox, independent sign-in. Cons: costs per seat.
  - Email aliases on a shared user (e.g., shared@gamblingexcellence.com with aliases support@, billing@). Pros: lower cost. Cons: harder to track ownership and send as address without alias delegate.
  - Google Groups / distribution lists forwarding to a team inbox: create group `support@gamblingexcellence.com` and add users as members.
- Google Workspace (recommended) quick steps:
  1. Sign in to Google Admin console (admin.google.com) as admin.
  2. To create a mailbox as a user: Users > Add user > set Primary email `support@gamblingexcellence.com` (or create `support` as alias). Note cost implications.
  3. To create a group (alias): Groups > Create group > Group email `support@gamblingexcellence.com` > Access type: Collaborative Inbox (if using Gmail's group features) > Add members (agent accounts) > Save.
  4. Set group posting permissions and enable Reply as the group (if using Collaborative Inbox) so replies come from `support@`.
  5. Configure sender permissions if you need agents to `Send as` the shared address.
- Microsoft 365 quick steps: create a shared mailbox or distribution list, add members, grant send-as/send-on-behalf permissions.

2) Setting support hours and response SLA
- Decide default support hours (example): Mon–Fri 08:00–18:00 PST, Closed weekends.
- SLA template (pick one):
  - Priority: Critical (service down) — Response within 2 hours, escalate to phone.
  - Priority: High (payment issues) — Response within 4 business hours.
  - Priority: Normal (general inquiries) — Response within 24 business hours.
- Steps to apply:
  1. Document hours & SLA in an internal policy file and on public-facing pages.
  2. Configure autoresponder (see auto-reply template in `docs/customer_contact_copy_pack.md`).
  3. Add business hours to phone call handling (see call flow below).

3) Creating business phone and call flow
- Decision: Google Voice (Starter/Standard) is suitable for quick setup if you already use Google Workspace. Compare plan features at https://workspace.google.com/products/voice/ (accessed 2026-03-02).
- Manual provisioning steps (Google Voice, admin-driven):
  1. In Google Admin console, enable Google Voice for the domain and allocate licenses to user accounts (requires Google Workspace admin access).
  2. Buy or port a number via Voice > Numbers > Buy number (choose country/area code). Keep emergency address accurate.
  3. Configure call handoff: set the number to ring a user or a group. For shared support numbers, create a Google Group or ring group and forward calls to multiple members.
  4. Set business hours: Voice settings > Calls > Business hours — define hours and set routing for after-hours to voicemail or to a SIP trunk/number.
  5. Configure voicemail greeting and transcription, and set email notifications to `support@` for voicemail copies.
  6. Set up call screening, transfer policy and E911/emergency settings.
- Minimal call flow example (recommended):
  - During business hours: Ring `support_queue` (simultaneous ring to 3 agents) -> if no answer, forward to on-call user -> if still no answer after 45s, go to voicemail and send voicemail copy to `support@`.
  - Outside hours: Play business-hours voicemail message and send to `support@` with subject "After-hours voicemail".

4) Publishing contact details
- Where to publish: website Contact page, site footer, receipts, transactional emails, and internal docs.
- Minimum public block (short form):
  - Support: support@gamblingexcellence.com
  - Billing: billing@gamblingexcellence.com
  - Phone: +1-XXX-XXX-XXXX (business hours Mon–Fri 08:00–18:00 PST)
  - Response SLA: Replies within 24 business hours (billing issues within 4 business hours).
- Steps to publish:
  1. Update site contact page content (copy in `docs/customer_contact_copy_pack.md`).
  2. Update site footer template and transactional email footers.
  3. Add contact details to the receipt generation template and support center.

Appendix: Helpful checks & artifacts
- Save these artifacts in `docs/` and `reports/` before making DNS changes:
  - `docs/dns_email_auth_worksheet.md` (SPF/DKIM/DMARC record templates)
  - `docs/customer_contact_copy_pack.md` (copy for site, email, voicemail)
  - `reports/business_contact_qa_checklist.md` (QA script)
  - `reports/business_contact_tracker.csv` (task tracker)

If you want, I can now create the worksheet, copy pack, QA checklist and tracker files in the repo (I will not change DNS or create accounts). 
