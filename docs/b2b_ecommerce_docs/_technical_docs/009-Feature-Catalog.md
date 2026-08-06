# 009 — Feature Catalog

Every feature reachable from a visible menu, screen or active API route, with a short technical
description. Grouped by surface.

**Legend — surfaces:** **C** = Client Portal · **A** = Account Manager Portal · **B** = Odoo
back-office.

---

## Catalog & Merchandising

| Feature                | Surfaces    | Technical description                                                                                                                                                               |
| ---------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Product browsing       | C           | Paginated catalog endpoint with filtering by public category, brand, product tag and attribute values; prices resolved against the requesting company's pricelist                   |
| Product search         | C           | Server-side text search folded into the same catalog domain builder                                                                                                                 |
| Product detail         | C           | Returns the template, its variants, attribute exclusion rules, effective price / list price / discount, terms, alert message and media                                              |
| Variant selection      | C           | Attribute-value matrix with exclusion data so impossible combinations are disabled client-side                                                                                      |
| Brands                 | C · A · B | Brand catalog with ordering and an active flag; brand menu in the storefront header; full CRUD in AMP with duplicate-name protection                                                |
| Public categories      | C · A · B | Hierarchical merchandising tree with images and descriptions; drives the storefront mega-menu; CRUD in AMP                                                                          |
| Featured products      | C · B      | `is_featured_product` flag surfaced on the home page                                                                                                                              |
| Product alert messages | C · A · B | Short catalog notice attached to a product; managed from a back-office menu and selectable in AMP                                                                                   |
| Product ribbons        | A           | Odoo website-sale ribbons exposed as a lookup for the AMP product form                                                                                                              |
| "Need call" products   | C · A · B | Products that must be quoted by phone; the flag propagates onto order lines                                                                                                         |
| Product terms          | C · B      | Per-product HTML terms and conditions rendered on the detail page                                                                                                                   |
| Merchants / suppliers  | B           | Merchant master data and per-product merchant prices, maintained from the Configuration menu                                                                                        |
| Banners                | C · A · B | Scheduled marketing banners with activation windows, optional promotion URL, optional targeting to one client, and linked products/categories; carousel on the storefront home page |

## Product Management (AMP & Back-office)

| Feature                       | Surfaces | Technical description                                                                                                                                                                                                                                           |
| ----------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Product CRUD                  | A · B   | Create, read, update, delete product templates over REST, including multipart media upload and media retention control                                                                                                                                          |
| Attribute management          | A        | List attributes and values; link an attribute to a template; unlink an attribute; remove a single attribute value                                                                                                                                               |
| Variant management            | A        | Generate the full variant matrix from linked attributes, create specific variants, list, update and delete variants                                                                                                                                             |
| Bulk product import           | A · B   | JSON import pipeline: tolerant parsing of loosely formatted JSON, find-or-create of brands, categories and attributes, variant assignment, price assignment per pricelist, optional image download. Exposed both as a REST endpoint and as a back-office wizard |
| Product categories (internal) | B        | Standard Odoo product category tree, surfaced in the module's Configuration menu                                                                                                                                                                                |
| Combo choices                 | B        | Standard Odoo product combos, surfaced in Configuration                                                                                                                                                                                                         |

## Pricing

| Feature                                  | Surfaces | Technical description                                                                                                                                             |
| ---------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pricelist CRUD                           | A · B   | Create, update, delete and inspect pricelists; currency lookup endpoint                                                                                           |
| Price rule (item) CRUD                   | A        | Full CRUD over`product.pricelist.item` with search, filtering, counting and paging; rules resolve to product or variant with display names                      |
| Client-category default pricing          | A · B   | Each client category (`res.partner.grade`) carries a default pricelist; assigning a category to a client applies it                                             |
| Pricelist / category conflict resolution | B        | When a client is given both a category and a different pricelist, the module resolves the conflict deterministically and logs the outcome in the client's chatter |
| Per-company price resolution             | C        | All catalog and order prices are computed against the requesting company's effective pricelist at request time                                                    |
| Customer target price                    | C · A   | Order lines carry the price the customer is asking for, visible to the account manager during pricing                                                             |

## Orders

| Feature                           | Surfaces    | Technical description                                                                                                                  |
| --------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Basket / wishlist creation        | C           | Creates a draft`sale.order`; optionally copies an existing order as the starting point                                               |
| Multiple named baskets            | C           | `portal_label` plus a per-client sequence lets a user keep several parallel baskets and switch between them from the header          |
| Order line management             | C · A      | Create, update and delete lines; quantity, product and target price on the client side, price and discount on the account-manager side |
| RFQ submission                    | C           | State transition to`rfq_submitted`, blocked when the order has no real lines                                                         |
| Quotation issuance                | A           | Transition to`quotation_submitted` renders the quotation PDF and sends the portal quotation mail template                            |
| PO submission                     | C           | Customer converts a received quotation into`po_submitted`                                                                            |
| Order confirmation                | A           | Transition to`in_progress` runs Odoo's standard confirmation (`state = sale`)                                                      |
| Delivery & cancellation           | A           | Terminal transitions to`delivered` / `cancel` / `rejected`                                                                       |
| Order queues                      | C · A · B | Server-side filtered lists per portal state — Wishlists, RFQs, Quotations, Orders, Archived, Shared Wishlist                          |
| Order detail                      | C · A      | Full order payload: lines, totals, attachments, chatter counts, planning state, requests, account-manager comment                      |
| Draft orders shortcut             | C           | Lightweight endpoint returning the user's most recent drafts for the header basket selector                                            |
| Planning state                    | C · A · B | Late / On Time / Upcoming computed from the planned order date and the current portal state                                            |
| Needs attention flag              | A · B      | `portal_visible` drives the shared-wishlist queue, a back-office filter and a dashboard counter                                      |
| Reviewed / printed tracking       | C · A      | Timestamps recorded when the customer reviews or prints a quotation                                                                    |
| Pending-submit detection          | C · A      | Editing an already-quoted order flags it as changed but not re-submitted                                                               |
| Account-manager notes vs. comment | A · B      | Internal note (never shown to the client) and a client-visible comment on the same order                                               |
| Order deletion                    | C           | Only the creating user may delete their basket                                                                                         |

## Catalog Requests

| Feature                   | Surfaces | Technical description                                                                                           |
| ------------------------- | -------- | --------------------------------------------------------------------------------------------------------------- |
| Request a missing product | C        | Free-text product request with quantity and reference URL, attached to an order                                 |
| Request triage            | A · B   | State machine submitted → in progress → product added / not found, with a date stamp per transition           |
| Auto-created order line   | C · A   | Linking a sourced product to a request creates the corresponding order line automatically; unlinking removes it |
| Open-request counter      | B        | Live count of unresolved requests on the back-office order form with a drill-down                               |

## Clients & Users

| Feature                    | Surfaces    | Technical description                                                                                                                                          |
| -------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Password login             | C · A      | The only sign-in method. Accepts a login**or** an identification number; establishes an Odoo session cookie                                              |
| Forgotten-password reset   | C · A      | Three-step self-service flow at`/reset-password`: e-mail a one-time code, verify it for a secret token, set a new password. The code never signs the user in |
| Password change            | C · A      | An authenticated user changes their own password                                                                                                               |
| Client company CRUD        | A · B      | Create, read, update, archive and restore B2B client companies, including address, category, pricelist and account manager                                     |
| Client categories          | A · B      | CRUD over`res.partner.grade`, used as the segmentation and default-pricing dimension                                                                         |
| Account-manager assignment | A · B      | Primary account manager plus an additional many-to-many set; drives notification routing and chat thread scoping                                               |
| Portal user management     | C · A · B | Company admins create, update, activate, deactivate and delete their own company's users; internal staff manage the same from the back-office                  |
| Dual activation control    | C · A · B | Vendor-side`activate` and client-side `portal_activate` must both be true                                                                                  |
| User tags                  | C · A · B | Per-company tags for organising portal users, with full CRUD from the client portal                                                                            |
| Invitation by QR code      | A · B      | Generates an invitation URL and QR image, sends the invitation mail template, and offers a printable PDF report                                                |
| Online users view          | B           | Back-office list of currently connected portal users, driven by presence                                                                                       |
| Account managers view      | B           | Configuration list of internal users flagged as account managers                                                                                               |
| Address lookups            | A           | Country and state endpoints for client address forms                                                                                                           |

## Collaboration

| Feature                            | Surfaces    | Technical description                                                                                                                                    |
| ---------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Order chatter                      | C · A · B | Read, post and update comments on an order; access validated against the order's company                                                                 |
| Chatter attachments                | C · A · B | Upload and delete files on an order thread; deletion restricted to the uploader; portal provenance recorded on every attachment                          |
| Attachment listing                 | A           | Generic endpoint listing documents attached to a record with access checks                                                                               |
| Live chat — client side           | C           | Initialises or joins the company's discuss channel, sends messages, marks as read; messages arrive over WebSocket                                        |
| Live chat — account manager inbox | A           | Thread list across all managed client companies with last message, unread count and presence; init, send and mark-read per thread                        |
| Back-office chat widget            | B           | An internal user can converse with portal users directly from the Odoo web client                                                                        |
| Presence / online status           | C · A · B | Heartbeat-driven online / away / offline status shown in the chat UIs and the back-office Online Users list                                              |
| In-app notifications               | C · A      | Typed activity feed (user login, order update, message, user activation) with unread badge, mark-one-seen and mark-all-seen; delivered live over the bus |
| E-mail notifications               | —          | Account manager receives an e-mail on RFQ submitted, RFQ updated, PO submitted and shared wishlist; globally switchable in settings                      |

## Back-Office Only

| Feature                      | Technical description                                                                                                |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| B2B Dashboard                | OWL client action with counters (Needs Attention, New RFQs, Total RFQs, …) that drill into pre-filtered order lists |
| Portal-state search filters  | Saved filters on the order search view for every portal state plus Needs Attention and Quotation Submitted           |
| Live list refresh            | Orders broadcast a bus event on every change so open lists update without a manual reload                            |
| Notifications administration | Configuration menu listing all generated notifications                                                               |
| Module settings              | Shop portal URL and the e-mail notification master switch, under Settings → B2B Ecommerce                           |

## Platform / Cross-Cutting

| Feature             | Technical description                                                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Media proxy         | CORS-enabled image and binary endpoints so the portal can render Odoo-hosted media directly                                                 |
| Build info endpoint | Reports the deployed build so an environment can be identified from the outside                                                             |
|                     |                                                                                                                                             |
| Permission lookup   | AMM endpoint returning a user's roles, permission codes and visible screen tree per portal                                                  |
| Release notes page  | Public`/release-notes` timeline in the portal, generated at build time from per-release JSON; only business-facing highlights are exposed |
| Help page           | Public`/help` page in the client portal                                                                                                   |
| Theming             | Light / dark mode toggle persisted per user in both portals                                                                                 |
