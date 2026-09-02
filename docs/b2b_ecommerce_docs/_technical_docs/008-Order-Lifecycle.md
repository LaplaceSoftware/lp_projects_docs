# 008 — Order Lifecycle

The order lifecycle is the heart of the platform. A single `sale.order` record carries **two
status fields**: Odoo's native `state` (the ERP truth) and `portal_state` (the B2B business
truth shown in both portals).

---

## Portal State Machine

```mermaid
stateDiagram-v2
    [*] --> draft: customer creates a basket/wishlist

    draft --> rfq_submitted: customer submits for quotation

    rfq_submitted --> rfq_updated: customer revises before pricing
    rfq_updated --> rfq_submitted

    rfq_submitted --> quotation_submitted: account manager prices & sends
    rfq_updated --> quotation_submitted
    rfq_submitted --> rejected
    rfq_updated --> rejected

    quotation_submitted --> po_submitted: customer accepts, sends PO
    quotation_submitted --> rfq_updated: customer edits → re-submits
    quotation_submitted --> cancel

    po_submitted --> in_progress: account manager confirms the order
    po_submitted --> cancel

    in_progress --> delivered
    in_progress --> cancel

    rejected --> [*]
    cancel --> [*]
    delivered --> [*]
```

### State reference

| `portal_state`        | Business meaning                             | Mapped Odoo`state` | Owner of the next move  |
| ----------------------- | -------------------------------------------- | -------------------- | ----------------------- |
| `draft`               | Basket / wishlist being built                | `draft`            | Customer                |
| `rfq_submitted`       | Request for quotation lodged                 | `draft`            | Account Manager         |
| `rfq_updated`         | Customer revised the request                 | `draft`            | Account Manager         |
| `rejected`            | Request refused                              | `cancel`           | —                      |
| `quotation_submitted` | Priced quotation issued (PDF e-mailed)       | `sent`             | Customer                |
| `po_submitted`        | Customer sent their purchase order           | `sent`             | Account Manager         |
| `in_progress`         | Order confirmed and being fulfilled          | `sale`             | Account Manager         |
| `delivered`           | Fulfilment complete                          | `sale`             | —                      |
| `cancel`              | Cancelled                                    | `cancel`           | —                      |

State changes arrive through a single update endpoint. Two transitions are **not** plain field
writes — they delegate to real Odoo actions:

| Transition                | Delegates to              | Side effects                                                                                             |
| ------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------- |
| →`quotation_submitted` | the quotation-send action | Renders the quotation PDF, sends the*Ecommerce: Portal Quotation* mail template, sets `state = sent` |
| →`in_progress`         | the order-confirm action  | Runs Odoo's standard confirmation, sets`state = sale`                                                  |

### Guard rails

- A transition to any state other than `draft`, `rejected` or `cancel` is refused if the order
  has no real (non-display) lines.
- An unknown `portal_state` value is rejected outright.
- Only the creator may delete a basket.
- Editing an already-quoted order sets `portal_pending_submit`, marking it as changed but not
  yet re-submitted.
- A B2B portal order stays out of the standard Odoo Sales module views
  (Quotations / Orders) until it reaches `state='sale'` — i.e. until it hits `in_progress`. This
  keeps in-flight RFQs and quotations from cluttering the internal sales pipeline; the order is
  always visible in the AMP/back-office portal-state queues regardless.

---

## End-to-End Business Workflow

```mermaid
sequenceDiagram
    autonumber
    actor C as Client Portal User
    participant P as Client Portal
    participant API as Odoo REST API
    participant O as sale.order
    participant N as Notifications + e-mail
    actor AM as Account Manager (AMP)

    C->>P: browse catalog, add products
    P->>API: order create / order_lines create
    API->>O: draft order, per-client sequence number
    Note over O: portal_state = draft

    C->>P: submit request
    P->>API: orders/update state = rfq_submitted
    O->>N: notify account manager (in-app + e-mail)
    N-->>AM: "New RFQ submitted"

    AM->>API: open RFQ queue, edit line prices
    API->>O: order_lines/update

    AM->>API: orders/update state = quotation_submitted
    O->>O: render quotation PDF
    O->>N: send quotation mail template
    N-->>C: quotation e-mail
    Note over O: portal_state = quotation_submitted · state = sent

    alt customer accepts
        C->>P: submit PO
        P->>API: orders/update state = po_submitted
        O->>N: notify account manager
        AM->>API: orders/update state = in_progress
        O->>O: confirm order → state = sale
        AM->>API: orders/update state = delivered
    else customer revises
        C->>P: edit lines
        P->>API: orders/update state = rfq_updated
        O->>N: notify account manager
    else cancelled
        C->>P: cancel
        P->>API: orders/update state = cancel
    end
```

**Notification trigger points.** The account manager is notified on exactly three customer-side
transitions: `rfq_submitted`, `rfq_updated`, `po_submitted` — plus when a wishlist is shared, and
whenever the client opens or downloads the quotation PDF. Notifications are only sent when the
actor is a portal user, so account-manager-side edits do not notify the account manager. E-mail
delivery is globally switchable via a system setting; the in-app notification is always created.

---

## The Shared-Wishlist Flow

A parallel, lighter-weight flow that does not enter the RFQ pipeline.

```mermaid
sequenceDiagram
    actor C as Client user
    participant O as sale.order (draft)
    participant N as Notification
    actor AM as Account Manager

    C->>O: mark basket as "needs attention" (portal_visible = true)
    O->>N: create notification + notify account manager
    N-->>AM: "<user> shared wishlist <name>"
    AM->>O: review in AMP "Shared wishlist" queue
    AM->>O: mark handled (portal_visible = false)
```

`portal_visible` is the "needs attention" flag; it also drives the **Needs Attention** filter
and dashboard counter in the Odoo back-office.

---

## Requesting a Product That Is Not in the Catalog

```mermaid
sequenceDiagram
    actor C as Client user
    participant R as ecommerce.product.request.line
    participant O as sale.order
    actor AM as Account Manager

    C->>R: create request (name, qty, reference URL) on an order
    Note over R: state = submitted
    AM->>R: pick up → in_progress
    alt product can be sourced
        AM->>R: link a created/matched product → product_added
        R->>O: auto-create the sale order line
    else cannot be sourced
        AM->>R: not_found
    end
```

The request line and the order line stay linked: unlinking or re-pointing the request removes
or replaces the generated order line. The order carries a live count of unresolved requests,
surfaced as a button on the back-office order form.

---

## Order Numbering and Labelling

| Field               | Origin                                                                                         | Shown to     |
| ------------------- | ---------------------------------------------------------------------------------------------- | ------------ |
| `name`            | Odoo's standard sale-order sequence                                                            | Back-office  |
| `portal_order_no` | The**client company's own sequence** (`portal_order_sequence_id`), generated on create | Both portals |
| `portal_label`    | Free text chosen by the customer ("Q3 lab restock")                                            | Both portals |

Per-client sequences mean each customer sees a continuous, private numbering series.

---

## Planning and Attention Signals

| Signal                                                  | Meaning                                                     |
| ------------------------------------------------------- | ----------------------------------------------------------- |
| `portal_planned_order_date` + computed planning state | Late / On Time / Upcoming — drives urgency indicators      |
| `portal_visible`                                      | Needs attention (unread portal activity or shared wishlist) |
| `portal_reviewed` + `portal_reviewed_date`          | The customer has reviewed the quotation — stamped only when the actor is a portal user |
| `portal_print_quotation_date`                         | The customer printed/downloaded the quotation — same portal-user-only stamping |
| `account_manager_print_po_date`                       | The account manager downloaded the purchase order — the internal-side mirror of the two rows above |
| `portal_pending_submit`                               | The customer edited a quoted order without re-submitting    |
| `portal_messages_count`                               | Volume of portal-originated chatter                         |
| `account_manager_notes` / `account_manager_comment` | Internal note vs. client-visible comment                    |

The planning state is not purely computed-on-read: a daily scheduled job
(*Ecommerce: Update Order Planning States*) recomputes it from `portal_planned_order_date` for
every order, so a Late/Upcoming indicator does not go stale between reads.

---

## Where Each State Appears

| Surface                                        | Queues                                                                                                                                                        |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **AMP** (`/admin`)                     | Shared Wishlist · RFQ Quotations · Quotations · Orders · Archived Orders                                                                                  |
| **Client Portal** (`/company-profile`) | Wishlists · RFQs · Orders · Archived                                                                                                                       |
| **Odoo back-office**                     | Orders Management → RFQ Quotations · Quotations · Orders; dashboard drill-downs for Needs Attention, New RFQs, Total RFQs; search filters per portal state |
