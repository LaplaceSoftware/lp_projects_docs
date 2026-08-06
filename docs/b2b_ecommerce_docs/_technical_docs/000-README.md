# SAMTIA B2B E-Commerce Platform — Technical Documentation

**Audience:** Technical Manager · Solution Architect · newly onboarding developer
**Goal:** understand the whole platform — architecture, applications, integrations, business
workflows, deployment and major components — without reading source code.

**Generated from:** live source scan of `addons_lp_ecommerce/` (Odoo 19 modules) and
`next_ecommerce/` (Next.js 15 portals).

**Scope rule applied:** only features reachable from a visible menu, screen or active API route
are documented. Dead code, commented-out models and unregistered views are excluded — see
[016 — Exclusions](016-Architecture-Decisions-and-Customization-Points.md#exclusions).

---

## Index

| #   | Document                                                                                                 | Covers                                                   |
| --- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| 001 | [Project Overview](001-Project-Overview.md)                                                               | What the platform is, actors, portals, glossary          |
| 002 | [System Architecture](002-System-Architecture.md)                                                         | C4 context & container views, request lifecycle          |
| 003 | [Repositories and Structure](003-Repositories-and-Structure.md)                                           | The two repos, folder responsibilities                   |
| 004 | [Odoo Modules](004-Odoo-Modules.md)                                                                       | Module catalog, dependency graph, responsibilities       |
| 005 | [Domain Model](005-Domain-Model.md)                                                                       | Custom models, extensions, ERD, inheritance              |
| 006 | [API and Controller Architecture](006-API-and-Controller-Architecture.md)                                 | Envelope, controller inheritance, endpoint catalog       |
| 007 | [Authentication and Authorization](007-Authentication-and-Authorization.md)                               | Session login, password reset, guards, Access Management |
| 008 | [Order Lifecycle](008-Order-Lifecycle.md)                                                                 | Portal state machine, sequence diagrams                  |
| 009 | [Feature Catalog](009-Feature-Catalog.md)                                                                 | Every shipped feature with a technical description       |
| 010 | [Next.js Application Architecture](010-NextJS-Application-Architecture.md)                                | Layers, routing, state, HTTP client                      |
| 011 | [Navigation and User Journeys](011-Navigation-and-User-Journeys.md)                                       | Back-office menus, portal menus, journeys                |
| 012 | [Real-Time and Messaging](012-Realtime-and-Messaging.md)                                                  | WebSocket, chat, presence, notifications, chatter        |
| 013 | [Master Data and Configuration](013-Master-Data-and-Configuration.md)                                     | Startup config, SMTP, system parameters, crons, env vars |
| 014 | [Deployment Architecture](014-Deployment-Architecture.md)                                                 | Odoo.sh branches, portal Docker pipeline, environments   |
| 015 | [External Integrations and Dependencies](015-External-Integrations-and-Dependencies.md)                   | Third-party and platform dependencies                    |
| 016 | [Architecture Decisions and Customization Points](016-Architecture-Decisions-and-Customization-Points.md) | Why it is built this way; where to extend                |
| 017 | [Odoo.sh Environments Guide](017-Odoo.sh-Environments-Guide.md)                                           | Branch topology, environment URLs, release step sequence |

---

## Reading Paths

**New Technical Manager (1 hour)** → 001 → 002 → 004 → 008 → 011 → 014

**New Backend Developer** → 002 → 004 → 005 → 006 → 007 → 013 → 016

**New Frontend Developer** → 002 → 010 → 011 → 006 → 007 → 012 → 014

---

## Terminology (used consistently throughout)

| Term                                   | Meaning                                                                          |
| -------------------------------------- | -------------------------------------------------------------------------------- |
| **Client Portal**                | Customer-facing Next.js app served at`/`                                       |
| **AMP** / Account Manager Portal | Internal Next.js app served at`/admin/*`                                       |
| **Back-office**                  | The Odoo web client itself (ERP UI)                                              |
| **Client**                       | A B2B customer*company* (`res.partner`, `is_company = True`)               |
| **Portal user**                  | An end user belonging to a Client company                                        |
| **Account Manager**              | Internal employee owning one or more Clients                                     |
| **Portal state**                 | The B2B order status shown in both portals, distinct from Odoo's native`state` |
| **AMM**                          | Access Management Module — role/permission engine (`access_management`)       |
