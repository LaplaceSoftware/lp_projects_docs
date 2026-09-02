# 016 — Account Manager Portal: Reports

A dedicated Reports area for reviewing activity across the platform. Today it contains one
report — more may be added here over time.

---

## Persistence Report

**Screen name:** Persistence Report
**Business purpose:** See who has been active on the platform, and when — a login/activity
record you can filter and export.
**Who uses it:** Account Managers, Business Administrators.
**Navigation path:** Sidebar → **Reports** → **Persistence Report**.

📷 **Screenshot Placeholder**
File: `images/amp-persistence-report.png`
Description: The Persistence Report screen — mode toggle, search/filter bar, results table and
the Export to Excel button.

### Choosing who to report on

| Mode | Shows |
|------|-------|
| **Client users** | Sign-ins by your customers' portal users |
| **Internal users** | Sign-ins by SAMTIA employees |
| **All users** | Both, combined |

### Narrowing the results

| Tool | What it does |
|------|--------------|
| **Search** | Finds by name |
| **Users** | Restricts to one or more specific people |
| **Date range** | Restricts to sign-ins between two dates |

### Exporting

Click **Export to Excel** to download the currently filtered results as a spreadsheet — useful
for sharing activity with someone who does not have access to the portal, or for record-keeping.

### Business rules

- The report reflects the same login activity that drives the "first sign-in" notification
  described in [013](013-Messages-and-Notifications.md) — this is where you go to see the full
  history rather than just the latest event.
- The export always matches whatever filters are currently applied on screen.

---

## Tips

- **Use Client users mode when a customer disputes who signed in and when** — it is the
  authoritative record.
- **Export before changing filters further** if you need a snapshot of a specific view; the
  export is not saved anywhere in the portal afterwards.
