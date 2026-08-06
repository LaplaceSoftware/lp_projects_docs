# Pricelist Management — Time Plan

**Audience:** Product Owner · Business Team · Stakeholders
**Portal:** Account Manager Portal (AMP)
**Duration:** 7 working days — 2 preparation · 4 build · 1 testing on `staging-b2b`
**Companions:** `040_pricelist_management_technical_plan.md` (technical) · `042_pricelist_management_backlog.md` (stories)

---

## 1. What We Are Building

Today, pricing is maintained in the back-office system. Anyone who needs to change a customer price,
set up a promotion, or offer a volume discount has to go through the internal Odoo interface.

This feature brings pricing into the **Account Manager Portal**, where the commercial team already
works. They will be able to see every pricelist, create and retire pricelists, and manage the
individual price rules inside them — without leaving the portal and without asking IT.

### The business outcome

| Today                                                    | After this feature                                                               |
| -------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Pricing lives in the back-office system                  | Pricing is managed in the Account Manager Portal                                 |
| Promotions are set up manually and switched off manually | Promotions carry start and end dates and expire on their own                     |
| Volume discounts are applied ad hoc per quotation        | "Buy 10+, pay less" is an explicit, visible rule                                 |
| Everyone with pricing access can change pricing          | Account Managers can*see* a client's price without being able to *change* it |

---

## 2. Screens Needed

Four surfaces, all inside the Account Manager Portal, grouped under the existing
**Products Management** section of the sidebar.

| # | Screen                              | What the user does there                                                                                                                                                                   |
| - | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1 | **Pricelists — List**        | See all pricelists with their name and currency. Search by name or currency. Create a new pricelist. Edit or retire an existing one. Click a name to open it.                              |
| 2 | **Pricelist — Detail**       | View and edit the pricelist's name and currency. Retire it from here too.                                                                                                                  |
| 3 | **Items / Rules — Sub-list** | Sits inside the detail screen. Shows every price rule in that pricelist: the product (and variant), the price, the minimum quantity, and the dates the price is valid between. Searchable. |
| 4 | **Add / Edit Price Rule**     | A pop-up form to create or change one rule: pick the product, optionally narrow it to a specific variant, then set price, minimum quantity, and the start/end dates.                       |

### What each rule captures

| Field             | Meaning in business terms                                                                              |
| ----------------- | ------------------------------------------------------------------------------------------------------ |
| Product / Variant | Which product this price applies to. Leave the variant blank to cover*all* variants of that product. |
| Price             | The price the customer pays.                                                                           |
| Min Qty           | The smallest quantity that unlocks this price — how volume discounts are expressed.                   |
| Start date        | When the price becomes active. Leave blank for "immediately".                                          |
| End date          | When the price stops applying. Leave blank for "no expiry".                                            |

---

## 3. System Capabilities Required

The portal talks to the backend through a set of service calls. Nine in total — **two already exist**
and seven are new. No deep technical detail; this is the functional inventory.

### Pricelists

| Capability                                          | Status                             |
| --------------------------------------------------- | ---------------------------------- |
| Get the list of pricelists (with search and paging) | ✅ Already available, need update  |
| Get one pricelist's details                         | ✅ Already available , need update |
| Create a new pricelist                              | 🆕 To build                        |
| Update a pricelist's name or currency               | 🆕 To build                        |
| Retire a pricelist                                  | 🆕 To build                        |

### Price rules inside a pricelist

| Capability                                                   | Status      |
| ------------------------------------------------------------ | ----------- |
| Get the price rules for a pricelist (with search and paging) | 🆕 To build |
| Add a price rule                                             | 🆕 To build |
| Edit a price rule                                            | 🆕 To build |
| Remove a price rule                                          | 🆕 To build |

### Reused — nothing to build

| Capability                | Note                                                |
| ------------------------- | --------------------------------------------------- |
| Search products           | Powers the product picker in the rule form          |
| List product variants     | Powers the variant picker                           |
| Read a user's permissions | Decides which menu items and buttons that user sees |

> **On retiring a pricelist:** a retired pricelist is **archived, not erased**. Past orders and
> pricing history stay intact and auditable. This is a deliberate choice.

---

## 4. Access Management — Data to Be Defined

Access in this platform is organised as a hierarchy: a **portal** contains **categories**, a category
contains **screens**, a screen has **permissions**, and permissions are bundled into **roles** that
get assigned to users.

Below is exactly what gets added, in that hierarchy. **No new portal, no new category, and no new
role** — everything attaches to structures that already exist.

```text
Account Manager Portal                                    [EXISTS — reuse]
│
└── Products Management  (category)                       [EXISTS — reuse]
    │
    ├── Product Categories                                [exists]
    ├── Products                                          [exists]
    ├── Brands                                            [exists]
    │
    └── Pricelists                                        ★ NEW SCREEN
        │   route: /admin/pricelists
        │
        ├── Permissions                                   ★ 5 NEW
        │   ├── View          — see the pricelist list
        │   ├── View Detail   — open a single pricelist
        │   ├── Create        — add a new pricelist
        │   ├── Edit          — change name or currency
        │   └── Delete        — retire a pricelist
        │
        └── Pricelist Items  (sub-screen)                 ★ NEW SCREEN
            │
            └── Permissions                               ★ 4 NEW
                ├── View      — see the price rules
                ├── Create    — add a price rule
                ├── Edit      — change a price rule
                └── Delete    — remove a price rule
```

### Why two screens instead of one

Pricelists and their price rules each need their own Create / Edit / Delete permissions. Splitting
them into a screen and a sub-screen is what makes a grant like *"can see prices, cannot change
rules"* possible — which is precisely the control the business asked for.

### Which roles get what

| Role                        | Pricelists | Price Rules | In plain terms                                    |
| --------------------------- | ---------- | ----------- | ------------------------------------------------- |
| **Super Admin**       | Full       | Full        | Everything                                        |
| **Pricing Manager**   | Full       | Full        | Owns pricing end to end                           |
| **Account Manager**   | View only  | View only   | Can see the price a client gets; cannot change it |
| **Read Only Manager** | View only  | View only   | Look, never touch                                 |

> ⚠️ **Decision needed:** the **Pricing Manager** role is *read-only* in the system today. This
> feature is what turns it into a genuine editing role. Please confirm that is the intent before
> Day 5.

### Summary of records

| What        | How many | New or reused                              |
| ----------- | -------- | ------------------------------------------ |
| Portal      | 1        | Reused                                     |
| Category    | 1        | Reused (Products Management)               |
| Screens     | 2        | **New**                              |
| Permissions | 9        | **New**                              |
| Roles       | 4        | Reused — updated with the new permissions |

---

## 5. Delivery Timetable — 7 Days

Three phases: **2 days preparation**, **4 days build**, **1 day testing on staging**.

| Day         | Phase       | Milestone                              | What is delivered                                                                                                                                                                                                                                  | Demo-able?                          |
| ----------- | ----------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| **1** | Preparation | **Technical plan**               | The technical approach is written and agreed, and three open questions are closed: how retiring a pricelist behaves, where the service calls live, and how far permission enforcement goes. No code — this is the day that prevents rework later. | —                                  |
| **2** | Preparation | **Backlog ready**                | Every piece of work is written up as a numbered story (`AMP-PL >> 01.1` onward) with acceptance criteria and a test script for QA, sequenced so the team knows what blocks what. Stories are loaded into Azure and ready to pick up.             | —                                  |
| **3** | Build       | **Foundations built**            | The backend can create, rename and retire pricelists. The portal screen is scaffolded. Nothing visible to a business user yet.                                                                                                                     | —                                  |
| **4** | Build       | **Pricelists are manageable** ✅ | The team can see every pricelist in one screen, search it, and create, rename or retire one — no IT involvement. Retiring is safe: the pricelist is archived, never erased.                                                                       | ✅ Pricing Manager                  |
| **5** | Build       | **Prices are visible** ✅        | Opening a pricelist shows the products and prices inside it, with quantity breaks and validity dates. Read-only at this point.**Best day for a stakeholder walkthrough.**                                                                    | ✅ Pricing Manager, Account Manager |
| **6** | Build       | **Prices are editable** ✅       | Rules can be added, changed and removed: pick a product (optionally a specific variant), set price, minimum quantity and start/end dates. Seasonal and promotional pricing becomes self-service. Access rules go live.                             | ✅ Pricing Manager                  |
| **7** | Testing     | **Verified on staging** ✅       | Deployed to the**`staging-b2b`** environment on Odoo.sh and tested there against real data — every screen, every role, and the full 130-case QA script. Documentation updated. Ready for release.                                         | ✅ All roles                        |

### Why a dedicated staging day

Days 3–6 are verified on developer machines with test data. Day 7 is the first time the feature runs
on **`staging-b2b`** against a database that already exists — which is where two specific risks
surface and nowhere else:

- **Permissions on an existing database.** Role permissions can load correctly on a fresh setup and
  silently skip a database that was created before this release. Only a real staging environment
  proves the team actually gets the access they were granted.
- **Real catalogue volume.** Searching and paging behave differently against thousands of real
  products than against a handful of test records.

### Checkpoints for the business

| When            | What we need from you                                                                                         |
| --------------- | ------------------------------------------------------------------------------------------------------------- |
| **Day 1** | Confirm the three decisions listed above, and confirm the Pricing Manager role should become an editing role. |
| **Day 2** | Review the backlog — this is the last cheap moment to add or drop scope.                                     |
| **Day 5** | Attend the walkthrough — the screens are real but still inexpensive to change.                               |
| **Day 7** | Sign off on staging for release.                                                                              |

### If the week slips

The order is deliberate, so a delay costs the least at the end. Days 3–6 build the feature in the
order the business would use it — manage pricelists, then read prices, then edit them. If a day is
lost, the last build day (editing rules) is the one to move, leaving a usable read-only feature on
staging rather than a half-finished editor. **Day 7 should not be the day that gets cut** — it is
the only day the feature is proven anywhere other than a developer's machine.

---

## 6. Two Things to Be Aware Of

**1. The Pricing Manager role changes character.**
It is a view-only role today. This feature makes it the owner of pricing. Anyone currently holding
that role will gain the ability to change prices the moment this ships. Worth reviewing who holds it.

**2. Permissions control what the screen shows, not what the server refuses.**
Every admin screen in the portal works this way today — this feature is no different, and no less
safe than what is already live. If the business needs enforcement at the server level as well, that
is a separate platform-wide initiative and should be scheduled on its own merits rather than folded
into this week.
