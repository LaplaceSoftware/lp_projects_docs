# ODOO.SH ENVIRONMENTS & RELEASE MANAGEMENT GUIDE

**B2B E-commerce × ERP Integration Platform**

*Branching Topology · Syncing Direction · Deployment Workflow*

---

## 1. Purpose of This Document

This guide is the single reference for how code moves from the two development repositories to the live production platform on Odoo.sh. It explains the repository architecture, the five Odoo.sh branches, the direction of syncing between them, and the exact step sequence each team follows when releasing changes.

Every environment URL (storefront portal and Odoo back-office) is listed in Section 3 so any team member can immediately access the environment relevant to their stage of testing.

### Golden Rule

**Code flows in ONE direction only:** `staging-b2b / staging-erp → pre-prod → training → production`

**All merges on Odoo.sh are performed exclusively by the ERP Team.** Other teams test and raise upgrade requests.

---

## 2. Repository Architecture

The platform is built from two Git repositories with a submodule relationship:

- **B2B E-commerce submodule repo** — Developed and owned by the B2B E-commerce Team. Contains the storefront and the Client / Account Manager portal features. The team works on its own cycle and delivers changes by pushing to the `main` branch.
- **ERP main repo** — Owned by the ERP Team and connected to Odoo.sh. It embeds the B2B repo as a Git submodule and holds the five deployment branches. This repo is the single source of truth for everything deployed on Odoo.sh.

### Key Principle

**The B2B team never pushes directly to Odoo.sh.** All deployments flow through the ERP main repo — the ERP team updates the submodule pointer and merges between Odoo.sh branches.

---

## 3. Odoo.sh Environments & URLs

Five branches exist on Odoo.sh. Every environment exposes an Odoo back-office; all except `staging-erp` also expose a storefront portal.

| Branch                | Purpose                                            | Storefront Portal URL                                 | Odoo Back-office URL                                   |
| --------------------- | -------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------ |
| **staging-b2b** | Validate B2B E-commerce submodule changes          | https://staging-b2b.adv-photonx.com  | https://staging-b2b-odoo.adv-photonx.com       |
| **staging-erp** | Validate ERP / back-office changes                 | — (back-office only)                | https://<staging-erp-build>.dev.odoo.com |
| **pre-prod**    | Integrate staging-b2b + staging-erp; joint testing | https://pre-prod.adv-photonx.com     | https://pre-prod-odoo.adv-photonx.com          |
| **training**    | UAT and end-user training on validated build       | https://training-b2b.adv-photonx.com | https://training-b2b-odoo.adv-photonx.com      |
| **production**  | Live environment serving real clients              | https://b2b.samtia.com               | https://www.samtia.com                         |

Every environment except `staging-erp` is reached through a custom `adv-photonx.com`
sub-domain (`samtia.com` in production); `staging-erp` is still addressed by its raw Odoo.sh
build URL.

### Syncing Direction is One-Way, Left → Right

`staging-b2b` + `staging-erp` → `pre-prod` → `training` → `production`

**All merges are performed by the ERP Team only.**

---

## 4. Release Workflow — Step Sequence

The sequence below is triggered whenever the B2B E-commerce Team pushes changes to the submodule main branch. Each promotion happens only after the responsible team confirms testing and raises an upgrade request.

### 1. B2B Team pushes changes

New commits land on the B2B submodule repo, branch `main`.

### 2. ERP Team merges submodule → staging-b2b

The submodule pointer is updated on the Odoo.sh `staging-b2b` branch and the build is deployed.

### 3. B2B Team tests staging-b2b

Storefront and portal test cases are executed; on success the team requests an upgrade to the next branch.

### 4. ERP Team merges staging-b2b → pre-prod

The validated B2B changes are promoted to the integration branch.

### 5. ERP Team merges staging-erp → pre-prod

ERP-side changes are merged into the same integration branch so both streams meet in `pre-prod`.

### 6. Joint testing on pre-prod

B2B and ERP Teams test the integrated build together; when **BOTH** teams confirm, an upgrade to training is requested.

### 7. ERP Team merges pre-prod → training

The confirmed build is deployed to the training environment for UAT.

### 8. Training Team confirms UAT

Business scenarios are validated end-to-end; on approval the production upgrade is requested.

### 9. ERP Team merges training → production

**The release goes live on `b2b.samtia.com`.**

---

## 5. Team Responsibilities

| Team                          | Responsibilities                                                                                                                                                                    | Environments Used                                           |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **B2B E-commerce Team** | Develop the B2B submodule; push to submodule main; test storefront & portals on staging-b2b; joint testing on pre-prod; raise upgrade requests.                                     | `staging-b2b`, `pre-prod`                               |
| **ERP Team**            | Own the ERP main repo and Odoo.sh; perform ALL merges between branches; update submodule pointers; test ERP changes on staging-erp; joint testing on pre-prod; execute deployments. | `staging-erp`, `pre-prod`, `training`, `production` |
| **Training Team**       | Run user acceptance testing on the training environment; validate business scenarios end-to-end; give final approval (go / no-go) for production release.                           | `training`                                                |

---

## 6. Operating Rules & Guardrails

### One-way syncing

Merges flow one way only. Never merge backwards (e.g., `pre-prod` → `staging-b2b`). If a fix is needed, it starts again from the source repo.

### Single merge authority

Only the ERP Team performs merges and submodule pointer updates on Odoo.sh. The B2B Team never pushes to Odoo.sh branches directly.

### Test-then-promote

A branch is promoted only after the responsible team explicitly confirms testing and raises an upgrade request. `pre-prod` requires confirmation from **BOTH** the B2B and ERP Teams.

### Isolation before integration

`staging-b2b` isolates B2B module changes; `staging-erp` isolates ERP changes. The two streams meet for the first time in `pre-prod` — never earlier.

### Protected production

`production` receives code only from `training`, guaranteeing that every live release has passed staging, integration, and UAT.

---

## Summary: Code Flow Topology

```
B2B Submodule repo (B2B Team)
       ↓
       └─→ ERP Main Repo (ERP Team)
                ↓
                ├─→ staging-b2b (test B2B changes)
                │       ↓
                ├─→ staging-erp (test ERP changes)
                │       ↓
                └─→ pre-prod (integrate both streams)
                        ↓
                    training (UAT)
                        ↓
                    production (LIVE)
```

---

**Document Version:** 1.0 | **Last Updated:** July 2026
**Applicable to:** Laplace Software / Advanced Photonix B2B E-commerce Platform
