# Business Contact QA Checklist

Purpose: End-to-end QA tests to confirm contact channels are ready to go live.

Preconditions
- All inboxes created and forwarding/routing configured.
- DNS email-auth records uploaded (SPF/DKIM/DMARC in monitoring mode).
- Business phone number assigned and call flow configured.

Test 1 — Inbound email: basic delivery
- Steps:
  1. From an external personal account (Gmail/Yahoo), send an email to support@gamblingexcellence.com with subject: "TEST inbound email - <timestamp>".
  2. Confirm receipt in the support mailbox or group.
  3. Check headers for SPF/DKIM/DMARC results.
- Pass criteria:
  - Email appears in the intended inbox within 5 minutes.
  - SPF and DKIM show "pass" or acceptable (if still propagating, note in results).
  - DMARC alignment not failing (monitor only at start).
- If fail: Log issue with steps to reproduce, include raw headers and DNS dig outputs.

Test 2 — Contact form (website)
- Steps:
  1. Submit test contact form with valid email and message "TEST contact form - <timestamp>".
  2. Confirm form saves to backend and triggers outbound email to support@gamblingexcellence.com.
  3. Validate auto-reply (if configured) is received by the test submitter.
- Pass criteria:
  - Form backend shows submission within 1 minute.
  - Support inbox receives the submission email.
  - Auto-reply arrives within 2 minutes (if configured).
- If fail: capture web console errors, server logs, and email headers.

Test 3 — Phone call & voicemail
- Steps:
  1. Call the published business number during business hours.
  2. Validate call rings the configured recipients (or ring group) and is answerable.
  3. If unanswered, leave voicemail; confirm voicemail message is emailed to support@gamblingexcellence.com.
- Pass criteria:
  - Call connects and audio quality is acceptable.
  - Voicemail transcription/copy delivered to `support@` within 5 minutes.
- If fail: log SIP/signal errors, time-of-day, and configuration screenshots.

Test 4 — Auto-reply & SLA enforcement
- Steps:
  1. Send support request for billing to billing@gamblingexcellence.com.
  2. Confirm auto-reply with SLA is sent to sender.
  3. Simulate agent response: agent replies and mark ticket/resolution time.
- Pass criteria:
  - Auto-reply contains correct SLA messaging.
  - Agent response is trackable against SLA time.
- If fail: record template mismatch and update `docs/customer_contact_copy_pack.md`.

Test 5 — End-to-end incident flow (critical)
- Steps:
  1. Create a high-priority simulated incident email to support with subject containing "CRITICAL TEST".
  2. Validate escalation: phone notification or immediate ping to on-call agent.
- Pass criteria:
  - On-call agent receives alert within 15 minutes and acknowledges.
- If fail: adjust escalation rules.

Pass/Fail reporting format (CSV friendly)
- Columns: test_id, test_name, datetime, environment, result(PASS/FAIL), notes, attachments
- Example: `T1,inbound email,2026-03-02T10:15:00-08:00,prod,PASS,SPF pass; DKIM pass,headers.txt`

Issue logging template
- Title: Short description
- Steps to reproduce: numbered
- Expected result:
- Actual result:
- Evidence: screenshots, raw headers, dig output, call recording timestamp
- Owner: <team member>

Sign-off
- QA owner signs off when all PASS or all FAILs are logged and assigned.
