# Odoo Ecommerce Components & Workflows

## Scope & Audience
- Focuses on visual, professional diagrams for the ecommerce stack to support a Next.js B2B portal.
- Covers components, models, session objects, catalog loading by partner pricelist, and user workflow to submit an order as a backend quotation.

## Component Map (Modules)
```mermaid
flowchart LR
  subgraph Website_Layer_website_sale
    WC[HTTP Controllers]
    WM[Website Models]
  end

  subgraph Sales_sale
    SO[sale.order]
    SOL[sale.order.line]
  end

  subgraph Products_product
    PT[product.template]
    PP[product.product]
    PLI[product.pricelist]
    PLItem[product.pricelist.item]
  end

  subgraph Accounting
    FP[account.fiscal.position]
    TAX[account.tax]
  end

  subgraph Portal_Users
    RP[res.partner]
    UZ[res.users]
  end

  subgraph Payment
    PM[payment controllers]
  end

  WC -->|JSON-RPC/HTTP| SO
  WC -->|Session| WM
  WM -->|request.pricelist| PLI
  WM -->|request.fiscal_position| FP
  SO --> SOL
  SOL --> PP
  PP --> PT
  SOL --> PLItem
  PLItem --> PLI
  FP --> TAX
  RP --> UZ
  WC --> PM
```

## Model Relationships (ERD)
```mermaid
erDiagram
  product_template ||--o{ product_product : has
  product_template }o--o{ product_public_category : categorized_in

  product_pricelist ||--o{ product_pricelist_item : contains
  res_partner }o--|| product_pricelist : default_pricelist

  sale_order ||--o{ sale_order_line : includes
  sale_order }o--|| res_partner : for_partner
  sale_order }o--|| product_pricelist : uses_pricelist
  sale_order }o--|| website : scoped_to

  sale_order_line }o--|| product_product : references
  sale_order_line }o--|| uom_uom : uses_uom
  sale_order_line }o--o{ account_tax : applies

  account_fiscal_position }o--o{ account_tax : maps
```

## Session & Context Objects
- `request.cart`: current `sale.order` in session; created with website defaults.
- `request.pricelist`: resolved and cached per session; drives pricing.
- `request.fiscal_position`: used to map taxes for display/calculation.
- Product price context includes attribute extras for variants.

## Catalog Loading by Partner Pricelist
```mermaid
flowchart TD
  Auth[User/Partner Auth] --> PLSel[Resolve Pricelist]
  PLSel --> Dom[Build Website Product Domain]
  Dom --> SRCH[Search product.template]
  SRCH --> VARS[Prefetch first variant / variants]
  VARS --> Ctx[Set price context (qty,uom,date,attributes)]
  Ctx --> Price[Compute contextual price]
  Price --> TaxMap[Optional UI tax mapping via fiscal position]
  TaxMap --> JSON[Return catalog JSON]

  subgraph Inputs
    Qty[quantity]
    Uom[uom]
    Date[date]
  end
  Inputs --> Ctx
```

Notes:
- Pricelist selection: cart’s `pricelist_id` or partner’s `property_product_pricelist` (website-available).
- Domain: website sale domain + partner catalog restrictions (record rules).
- Prices: `product.template._get_contextual_price(product=variant)`; optionally align display with tax-included UI using fiscal position tax mapping.

## Pricing Computation Flow (Line-Level)
```mermaid
flowchart TD
  L[Sale Order Line] --> DP[_get_display_price]
  DP --> B[_get_pricelist_price_before_discount]
  DP --> R[_get_pricelist_price]
  B --> Max[Handle surcharge/discount visibility]
  R --> Max
  Max --> TI[Tax inclusion mapping via fiscal position]
  TI --> PU[Set price_unit & technical_price_unit]
  PU --> DC[_compute_discount]
```

## User Workflow: Submit Order as Quotation
```mermaid
sequenceDiagram
  participant U as User (Next.js UI)
  participant N as Next.js Server
  participant API as Custom Odoo REST
  participant O as Odoo Models/Controllers

  U->>N: Submit cart (items, partner)
  N->>API: POST /api/quotation {partner, items}
  API->>O: Create sale.order (draft) with partner/pricelist/fpos
  O-->>API: sale.order id
  API->>O: For each item, prepare order line values (variant resolution)
  O-->>API: sale.order.line created
  API->>O: Recompute prices & totals
  O-->>API: quotation ready (state=draft)
  API-->>N: {order_id, totals, state:draft}
  N-->>U: Show quotation summary/number
```

Implementation notes:
- Order creation mirrors website `_prepare_sale_order_values` defaults.
- Variant correctness ensured via `_prepare_order_line_values` using closest possible combination.
- Keep `state='draft'` to represent quotation; use `action_send` optionally.

## Component Interactions for Quotation
```mermaid
flowchart LR
  RP[res.partner] --> SO[sale.order]
  PLI[product.pricelist] --> SO
  FP[account.fiscal.position] --> SO
  SO --> SOL[sale.order.line]
  PP[product.product] --> SOL
  PLItem[product.pricelist.item] --> SOL
  TAX[account.tax] --> SOL
```

## Data Flow: Catalog for Logged-In Partner
```mermaid
sequenceDiagram
  participant N as Next.js
  participant API as Custom REST
  participant W as Website Layer
  participant M as Models

  N->>API: GET /api/catalog?partner_id
  API->>W: Resolve request.pricelist & fiscal_position
  W->>M: Domain = website.sale_product_domain + partner filters
  M-->>API: product templates + variants
  API->>M: Compute contextual prices (qty,uom,date)
  M-->>API: prices
  API-->>N: JSON {products, prices, taxes}
```

## Next.js Integration Blueprint
- Authentication: JWT/OAuth; map identity to Odoo portal user/partner.
- Pricing: always compute server-side via Odoo; cache per session.
- Catalog: filter on website domain + partner record rules; paginate on server.
- Quotation: create `sale.order` (draft), add lines, return id and totals.

## Visual Index
- Components: “Component Map (Modules)”
- Models: “Model Relationships (ERD)”
- Catalog: “Catalog Loading by Partner Pricelist” + “Data Flow”
- Pricing: “Pricing Computation Flow”
- Quotation: “User Workflow” + “Component Interactions for Quotation”