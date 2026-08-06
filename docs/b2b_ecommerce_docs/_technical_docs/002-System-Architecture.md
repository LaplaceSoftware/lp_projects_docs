# 002 — System Architecture

## C4 Level 1 — System Context

```mermaid
flowchart TB
    CU(["Client Portal User<br/>/ Company Admin"])
    AM(["Account Manager<br/>Pricing / Read-only"])
    ADM(["ERP / System Admin"])

    SYS["<b>SAMTIA B2B E-Commerce Platform</b><br/>Quote-driven B2B trade on Odoo 19"]

    MAIL[["SMTP relay<br/>outgoing mail"]]
    ODOOSH[["Odoo.sh<br/>backend hosting + CI"]]
    CFW[["Cloudflare Workers<br/>production portal hosting + CI/CD"]]
    REG[["Private Docker registry<br/>+ internal server"]]

    CU -->|"HTTPS storefront"| SYS
    AM -->|"HTTPS admin portal<br/>+ Odoo back-office"| SYS
    ADM -->|"Odoo back-office"| SYS

    SYS -->|"quotation PDF, password-reset code,<br/>invitation QR, state alerts"| MAIL
    SYS -.->|"backend deployed to"| ODOOSH
    SYS -.->|"production portal deployed to"| CFW
    SYS -.->|"non-production portal images to"| REG
```

The platform has **no inbound third-party integrations**. The only outbound dependency in the
runtime path is SMTP.

---

## C4 Level 2 — Containers

```mermaid
flowchart TB
    subgraph Browser["User browser"]
        NEXT["<b>Next.js 15 portal app</b><br/>React 19 · TypeScript · Tailwind 4<br/>Client Portal + AMP in one build"]
    end

    subgraph OdooSh["Odoo.sh runtime"]
        WEB["<b>Odoo 19 HTTP workers</b><br/>REST controllers + ORM + back-office UI"]
        BUS["<b>Odoo bus / WebSocket</b><br/>/websocket"]
        CRON["<b>ir.cron scheduler</b>"]
        DB[("PostgreSQL")]
        FS[("Filestore<br/>attachments, images")]
    end

    NEXT -->|"REST · JSON · session cookie<br/>CORS with credentials"| WEB
    NEXT <-->|"WebSocket frames<br/>chat · presence · notifications"| BUS
    WEB --> DB
    WEB --> FS
    BUS --> DB
    CRON --> DB
    WEB --> SMTP[["SMTP"]]
```

| Container         | Technology                               | Responsibility                                                             |
| ----------------- | ---------------------------------------- | -------------------------------------------------------------------------- |
| Portal app        | Next.js 15 App Router — Cloudflare Worker (OpenNext) in production, standalone container elsewhere | All customer and account-manager screens; no business rules                |
| Odoo HTTP workers | Python / Odoo 19                         | REST API, business logic, ORM, back-office UI, PDF rendering               |
| Odoo bus          | Odoo`bus.bus` + `/websocket`         | Push channel for chat messages, presence, notifications, grid auto-refresh |
| Scheduler         | `ir.cron`                              | Presence hygiene (stale sessions → offline)                               |
| PostgreSQL        | —                                       | Single database; all tenants share it, isolated by data scoping            |
| Filestore         | Odoo filestore                           | Product media, chatter attachments, generated PDFs                         |

---

## C4 Level 3 — Components inside Odoo

```mermaid
flowchart TB
    subgraph HTTP["HTTP layer"]
        CC["controllers/<br/>Client Portal routes"]
        AC["controllers_admin/<br/>AMP routes"]
        MC["access_management/controllers<br/>permission lookup"]
        BC["<b>lp_base.BaseController</b><br/>envelope · CORS · auth decorators"]
    end

    subgraph DOMAIN["Domain layer (models)"]
        ORD["sale.order + line<br/>portal state machine"]
        PRD["product.template / product.product<br/>catalog + pricing projection"]
        USR["res.users / res.partner<br/>identity + tenancy"]
        MSG["mail.message · discuss.channel<br/>ir.attachment · mail.presence"]
        CFG["brand · banner · merchant<br/>notification · alert · user tag<br/>product request line"]
    end

    subgraph MIX["Cross-cutting mixins"]
        SEC["ecommerce.base.secure_model<br/>reversible ID obfuscation"]
        REF["ecommerce.base_auto_refresh_model<br/>bus push on write"]
    end

    CC --> BC
    AC --> BC
    MC --> BC
    BC --> DOMAIN
    DOMAIN --> MIX
    DOMAIN --> ORM[("Odoo ORM / PostgreSQL")]
```

### Layering rule

Controllers are **thin**. They parse the request, call a single `api_*` / `*_payload` method on
a model, and wrap the returned dictionary in the response envelope. All business logic,
validation, tenancy scoping and serialisation live in the models. This is the single most
important convention in the backend — see [006](006-API-and-Controller-Architecture.md).

---

## Request Lifecycle — a typical authenticated call

```mermaid
sequenceDiagram
    participant B as Browser (Next.js)
    participant C as Odoo controller
    participant D as Decorator (lp_base)
    participant M as Model (api_* method)
    participant DB as PostgreSQL

    B->>C: OPTIONS /ecommerce/api/orders
    C->>D: preflight
    D-->>B: 204 + CORS headers

    B->>C: POST /ecommerce/api/orders (cookie)
    C->>D: http_auth_validated
    alt session is public
        D-->>B: 401 · response_code "401"
    else authenticated
        D->>M: api_get_orders(user_identity, filters)
        M->>M: resolve user → company partner
        M->>M: build tenant-scoped domain
        M->>DB: search + read
        DB-->>M: records
        M-->>C: {response_code, orders, pagination}
        C-->>B: 200 · JSON envelope + CORS
    end
```

Notes:

- Every route is declared `auth='public'` at the Odoo level and gated by the decorator
  instead. This exists so the controller can return the JSON envelope with a business code
  rather than Odoo's HTML login redirect.
- Business failures return **HTTP 200** with a non-zero `response_code`. Only session expiry
  returns HTTP 401.

---

## Real-Time Path

```mermaid
sequenceDiagram
    participant P as Portal (browser)
    participant WS as Odoo /websocket
    participant BUS as bus.bus
    participant M as Model write

    P->>WS: connect
    P->>WS: subscribe [channels]  %% MUST be the first frame
    Note over P,WS: Odoo.sh's gateway rejects any frame before subscribe (close 4001)
    P->>WS: update_presence (after subscribe)

    M->>BUS: _sendone(channel, type, payload)
    BUS-->>WS: relay
    WS-->>P: frame → store update → UI re-render
```

Presence is additionally maintained over plain HTTP (`/ecommerce/api/presence/ping` and
`/offline`) because the Odoo.sh gateway does not reliably deliver socket-close events. A
one-minute cron sweeps presences whose heartbeat went stale. See
[012](012-Realtime-and-Messaging.md).

---

## Integration Contract Between the Two Applications

| Concern     | Contract                                                                                                                                      |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Transport   | HTTPS,`Content-Type: application/json` (multipart for uploads)                                                                              |
| Base paths  | `/ecommerce/api/*` (client), `/ecommerce/api/admin/*` + `/api/admin/*` + `/ecommerce/admin/api/*` (AMP), `/amm/api/*` (permissions) |
| Auth        | Odoo session cookie, sent with`withCredentials: true`                                                                                       |
| Envelope    | `{ "response_code": "0", "response_message": "...", ...payload }`                                                                           |
| Success     | `response_code === "0"`                                                                                                                     |
| Errors      | 5xxx–6xxx business codes, HTTP 200;`"401"` with HTTP 401 = session expired                                                                 |
| Pagination  | `page` (default 1), `limit` (default 20); response carries a pagination block                                                             |
| Language    | `en_US` only — the portals send and render a single language                                                                                |
| Identifiers | Optionally obfuscated — see[016](016-Architecture-Decisions-and-Customization-Points.md#id-obfuscation)                                       |
| Real-time   | `wss://<api-host>/websocket`, derived automatically from the API base URL                                                                   |

The frontend enforces one global rule: a `response_code` of `"401"` clears local storage and
redirects to `/login`.
