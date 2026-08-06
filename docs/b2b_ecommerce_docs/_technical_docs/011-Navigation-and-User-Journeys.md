# 011 — Navigation and User Journeys

Navigation is the fastest way to read a system's business shape. This document reconstructs the
business flow from the menus that are actually rendered.

---

## Odoo Back-Office — "B2B Ecommerce" Application

```mermaid
flowchart LR
    R["B2B Ecommerce"] --> D["Dashboard"]
    R --> O["Orders Management"]
    R --> P["Products Management"]
    R --> C["Clients Management"]
    R --> CF["Configuration 🔒 admin"]

    O --> O1["RFQ Quotations"]
    O --> O2["Quotations"]
    O --> O3["Orders"]

    P --> P1["Brands"]
    P --> P2["Public Categories"]
    P --> P3["Product Tags"]
    P --> P4["Alert Messages"]
    P --> P5["Products"]
    P --> P6["Variants 🔒 variant group"]
    P --> P7["Pricelists 🔒 pricing team"]

    C --> C1["Clients Categories"]
    C --> C2["Clients"]
    C --> C3["Client Users"]
    C --> C4["Online Users"]
    C --> C5["Users Tags"]

    CF --> F1["Account Managers"]
    CF --> F2["Notifications"]
    CF --> F3["Merchants"]
    CF --> F4["Product Merchants"]
    CF --> F5["Combo Choices"]
    CF --> F6["Categories"]
```

Root menu visibility: system administrators and the Ecommerce Account Manager group.

| Menu | Group restriction | What it does |
|------|-------------------|--------------|
| Dashboard | — | OWL client action with counters that drill into filtered order lists (Needs Attention, New RFQs, Total RFQs) |
| Orders Management → RFQ Quotations | — | Orders in the RFQ portal states |
| Orders Management → Quotations | — | Orders in the quotation / PO states |
| Orders Management → Orders | — | Confirmed orders (`state = sale`) |
| Products Management → Pricelists | Pricing Team or admin | Pricelist maintenance |
| Products Management → Variants | Product-variant group | Variant list |
| Clients Management → Clients | Account Manager / admin | Two variants of the same menu: an attachment-scoped view for Account Managers, a full-chatter view for admins |
| Configuration | System admin only | Master data and reference lists |
| Import Products | Technical group only | JSON import wizard, deliberately hidden from normal users |

## Odoo Back-Office — "Access Management" Application

```mermaid
flowchart LR
    AR["Access Management"] --> AC["Configuration"]
    AR --> UR["User Access Right (report)"]
    AC --> A1["Applications"]
    AC --> A2["Screen Categories"]
    AC --> A3["Screens"]
    AC --> A4["Roles"]
```

Permissions and role assignments are managed **inside** the Screen and Role forms rather than
through their own top-level menus. The *User Access Right* wizard produces an effective-permission
report for a chosen user.

---

## Account Manager Portal (`/admin/*`)

```mermaid
flowchart LR
    S["AMP sidebar"] --> D["Dashboard<br/>/admin/dashboard"]
    S --> OM["Orders management"]
    S --> PM["Products management"]
    S --> CM["Clients management"]
    S --> M["Messages<br/>/admin/messages"]
    S --> CF["Configuration<br/>/admin/configuration"]

    OM --> O1["Shared wishlist"]
    OM --> O2["RFQ Quotations"]
    OM --> O3["Quotations"]
    OM --> O4["Orders"]
    OM --> O5["Archived Orders"]

    PM --> P1["Product Categories"]
    PM --> P2["Products"]
    PM --> P3["Brands"]
    PM --> P4["Pricelists"]

    CM --> C1["Clients Categories"]
    CM --> C2["Clients"]
```

The sidebar is a **static, typed tree** in the frontend. Each leaf carries an AMM screen
reference (`amp.dashboard`, `amp.rfq_quotations`, …). When AMM returns data the tree is filtered
to the permitted screens; a group node disappears when all its children do. When AMM is absent
the full tree renders.

The orders section is ordered to mirror the workflow: unqualified interest (Shared wishlist) →
incoming requests (RFQ Quotations) → issued quotations → confirmed orders → archive.

---

## Client Portal (`/`)

```mermaid
flowchart LR
    H["Header"] --> PR["Products mega-menu<br/>public category tree"]
    H --> BR["Brands menu"]
    H --> SE["Product search"]
    H --> NO["Notifications"]
    H --> BA["Basket selector<br/>switch between wishlists"]
    H --> UM["User menu"]

    UM --> TH["Help + light/dark theme"]
    UM --> CP["Company Profile"]
    UM --> LO["Sign out"]

    CP --> T1["Users 🔒 company admin"]
    CP --> T2["User Tags 🔒 company admin"]
    CP --> T3["Wishlists"]
    CP --> T4["RFQs"]
    CP --> T5["Orders"]
    CP --> T6["Archived"]
```

Company Profile is a single route with a `?page=` parameter driving a left navigation. The
**Users** and **User Tags** tabs are visible only to company admins; a standard user landing on
them is redirected to Orders. Unguarded auxiliary pages: `/help` and `/release-notes`.

The header basket selector is the key storefront affordance — a customer keeps several named
baskets in parallel and switches the active one without leaving the catalog.

---

## Screen ↔ Navigation Mapping

| AMM application | Screens in the catalogue | Rendered by |
|-----------------|--------------------------|-------------|
| `amp` | dashboard, shared_wishlist, rfq_quotations, quotations, orders, archived_orders, product_categories, products, brands, pricelists, pricelist_items, client_categories, clients, client_users, user_tags, messages | AMP sidebar tree |
| `client` | home, products, orders, company_profile, company_users, user_tags, help | Client header + company-profile tabs |

`pricelist_items`, `client_users` and `user_tags` (amp) exist in the catalogue for permission
purposes but have no dedicated sidebar entry — they are reached from within their parent screen
or from the Client Portal.

---

## User Journeys

### Journey 1 — Client user places an order

```mermaid
journey
    title From catalog to confirmed order
    section Discover
      Log in with login and password: 4: Client user
      Browse categories / brands / search: 5: Client user
      Open product detail, pick a variant: 5: Client user
    section Compose
      Add to a named basket: 5: Client user
      Request a product not in the catalog: 3: Client user
      Set target prices: 4: Client user
    section Negotiate
      Submit as RFQ: 5: Client user
      Chat with the account manager: 4: Client user, Account Manager
      Receive quotation e-mail + in-app notice: 5: Client user
    section Close
      Review quotation, submit PO: 5: Client user
      Track In Progress → Delivered: 4: Client user
```

### Journey 2 — Account Manager works the queue

```mermaid
flowchart LR
    A["Dashboard<br/>Needs Attention · New RFQs"] --> B["Shared wishlist<br/>proactive outreach"]
    A --> C["RFQ Quotations queue"]
    C --> D["Open order · price lines<br/>resolve product requests"]
    D --> E["Comment for the client<br/>+ internal note"]
    E --> F["Submit quotation<br/>PDF + e-mail sent"]
    F --> G["Quotations queue<br/>await PO"]
    G --> H["Confirm order → In Progress"]
    H --> I["Delivered"]
    C -.->|"clarify"| J["Messages inbox<br/>live chat"]
```

### Journey 3 — Onboarding a new client company

```mermaid
sequenceDiagram
    actor AM as Account Manager
    participant AMP as AMP
    participant B as Back-office
    actor CA as Client Company Admin
    actor CU as Client user

    AM->>AMP: create client company<br/>category, pricelist, address, account manager
    Note over AMP: client gets its own order sequence
    AM->>AMP: create the company admin user
    AM->>B: send invitation (QR code e-mail / printable PDF)
    CA->>CA: activate account via invitation
    CA->>CU: create sub-users, assign tags
    CA->>CU: control access with portal_activate
    CU->>CU: log in and start ordering
```

### Journey 4 — Product goes live in the catalog

```mermaid
flowchart LR
    A["Create product in AMP<br/>or bulk JSON import"] --> B["Assign brand,<br/>public categories, media"]
    B --> C["Link attributes<br/>generate variants"]
    C --> D["Set prices on pricelists<br/>or via price rules"]
    D --> E["Optional: featured flag,<br/>ribbon, alert message, terms"]
    E --> F["Visible to clients whose<br/>pricelist prices the product"]
```

Product visibility is a **pricing consequence**, not a separate publish switch: the catalog is
filtered by what the requesting company's pricelist can price.
