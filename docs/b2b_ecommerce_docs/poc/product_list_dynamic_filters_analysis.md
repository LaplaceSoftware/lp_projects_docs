# Product List Dynamic Filters Analysis & Proposal

## 1. Overview
The goal is to implement a **Dynamic Filter System** for the product list endpoint (`/ecommerce/api/products`). 
The system must return available filter options (Brands, Categories, Attributes, Tags, Price Range) based on the **currently filtered product set**. 
This ensures that users only see relevant filters (e.g., if "Laptops" category is selected, the "Screen Size" attribute should appear, but "Shoe Size" should not).

## 2. Current Architecture
- **Model**: `product.template`
- **Controller Endpoint**: `/ecommerce/api/products`
- **Current Logic**:
    1.  Receives params (`public_categ_ids`, `brand_ids`, `product_ids`, `search_term`, etc.).
    2.  Builds a search Domain.
    3.  Executes `search()` with pagination.
    4.  Returns product list.

## 3. Requirements
1.  **Context-Aware**: Filters must reflect the current search results.
2.  **Multi-Select**: Support selecting multiple values for the same filter (e.g., Brands: "Apple" OR "Samsung").
3.  **Performance**: Target ~1000 products. Must be sub-200ms.
4.  **Structure**: Clean JSON response for the frontend (Next.js/React).

## 4. Proposed Logic

### 4.1. The "Two-Step" Search Strategy (Optimized for ~1000 Items)
For a catalog or result set of around 1000 items, we can efficiently use the Odoo ORM without needing raw SQL. The strategy involves fetching matching IDs and then querying related models.

**Step 1: Build Base Domain & Fetch IDs**
Construct the domain and fetch all matching product IDs.
```python
product_ids = Product.search(domain).ids  # Fast for ~1000 items
```

**Step 2: Aggregate Filters**
Use `read_group` and `search_read` with the fetched `product_ids`.

### 4.2. Filter Extraction Logic

#### A. Brands
*   **Source**: `brand_id` field on `product.template`.
*   **Method**: `read_group`.
*   **Logic**:
    ```python
    brand_data = Product.read_group(domain, ['brand_id'], ['brand_id'])
    # Result: [{'brand_id': (1, 'Apple'), 'brand_id_count': 10}, ...]
    ```

#### B. Categories (Public)
*   **Source**: `public_categ_ids` (Many2many).
*   **Inverse Relation**: `product_tmpl_ids` exists on `product.public.category`.
*   **Method**: `search_read` on Category model.
*   **Logic**:
    ```python
    Category = self.env['product.public.category']
    # Fetch categories that contain ANY of the found products
    categories = Category.search_read(
        [('product_tmpl_ids', 'in', product_ids)], 
        ['id', 'name']
    )
    ```

#### C. Attributes
*   **Source**: `attribute_line_ids` (One2many).
*   **Method**: `search_read` on Attribute Line model.
*   **Logic**:
    ```python
    AttributeLine = self.env['product.template.attribute.line']
    # Fetch attribute lines linked to found products
    lines = AttributeLine.search_read(
        [('product_tmpl_id', 'in', product_ids)],
        ['attribute_id', 'value_ids']
    )
    # Post-process in Python to group by attribute_id
    ```

#### D. Product Tags
*   **Source**: `product_tag_ids` (Many2many).
*   **Inverse Relation**: `product_template_ids` exists on `product.tag`.
*   **Method**: `search_read` on Tag model.
*   **Logic**:
    ```python
    Tag = self.env['product.tag']
    tags = Tag.search_read(
        [('product_template_ids', 'in', product_ids)],
        ['id', 'name', 'color']
    )
    ```

#### E. Price Range
*   **Source**: `list_price`.
*   **Method**: `read_group`.
*   **Logic**:
    ```python
    price_data = Product.read_group(domain, ['list_price:min', 'list_price:max'], [])
    ```

### 4.3. Proposed JSON Response Structure

```json
{
  "count": 45,
  "filters": {
   "tags": [
      { "id": 101, "name": "New", "color": "#FF0000", "count": null },
      { "id": 102, "name": "Sale", "color": "#00FF00", "count": null }
    ],
    "brands": [
      { "id": 1, "name": "Apple", "count": 10 },
      { "id": 2, "name": "Samsung", "count": 8 }
    ],
    "categories": [
      { "id": 10, "name": "Electronics", "count": null },
      { "id": 12, "name": "Computers", "count": null }
    ],
   
    "attributes": [
      {
        "id": 100,
        "name": "Color",
        "display_type": "color",
        "values": [
          { "id": 501, "name": "Black", "html_color": "#000", "count": null },
          { "id": 502, "name": "White", "html_color": "#FFF", "count": null }
        ]
      }
    ],
    "price_range": {
      "min": 100.00,
      "max": 2500.00
    }
  },
  "results": [ ...products... ]
}
```
*Note: Exact counts for Categories/Tags/Attributes are expensive to calculate precisely in the same query. For <1000 items, we can calculate them in Python if strictly necessary, but often just showing availability is enough.*

## 5. Implementation Code (Draft)

```python
def _get_dynamic_filters(self, domain):
    Product = self.env['product.template']
    
    # 1. Fetch IDs (Fast for ~1000 items)
    # We use the same domain used for the search results
    product_ids = Product.search(domain).ids
    
    if not product_ids:
        return {'brands': [], 'categories': [], 'tags': [], 'attributes': [], 'price_range': {}}

    # 2. Brands & Price (Aggregation)
    # read_group is highly optimized
    stats = Product.read_group(domain, ['brand_id', 'list_price:min', 'list_price:max'], ['brand_id'])
    
    brands = []
    min_price = 0
    max_price = 0
    
    if stats:
        # Extract min/max from the first group (or global group if no brand grouping)
        # Note: When grouping by brand, min/max might be per brand. 
        # Better to do a separate query for global min/max or parse carefully.
        # Let's do separate for clarity and safety.
        price_stats = Product.read_group(domain, ['list_price:min', 'list_price:max'], [])
        if price_stats:
            min_price = price_stats[0]['list_price_min']
            max_price = price_stats[0]['list_price_max']

        for stat in stats:
            if stat['brand_id']:
                brands.append({
                    'id': stat['brand_id'][0],
                    'name': stat['brand_id'][1],
                    'count': stat['brand_id_count']
                })

    # 3. Tags (Inverse Search)
    Tag = self.env['product.tag']
    tags_data = Tag.search_read(
        [('product_template_ids', 'in', product_ids)],
        ['id', 'name', 'color']
    )
    
    # 4. Categories (Inverse Search)
    Category = self.env['product.public.category']
    categs_data = Category.search_read(
        [('product_tmpl_ids', 'in', product_ids)],
        ['id', 'name']
    )

    # 5. Attributes (Inverse Search & Python Grouping)
    AttributeLine = self.env['product.template.attribute.line']
    # Optimize: Read attribute_id and value_ids
    lines = AttributeLine.search_read(
        [('product_tmpl_id', 'in', product_ids)],
        ['attribute_id', 'value_ids']
    )
    
    # Grouping logic
    attrs_map = {}
    for line in lines:
        attr = line['attribute_id'] # (id, name)
        attr_id = attr[0]
        if attr_id not in attrs_map:
            attrs_map[attr_id] = {
                'id': attr_id,
                'name': attr[1],
                'values': {}
            }
        
        for val_id in line['value_ids']:
            # We only have IDs here. If we need names/colors, we might need 
            # to fetch 'product.attribute.value' details separately or join.
            # Ideally, search_read on 'product.attribute.value' filtering by attribute_line relations
            # is cleaner but more complex.
            # Simplified: Just collect IDs for now, or fetch details in a batch.
            attrs_map[attr_id]['values'][val_id] = True

    # To get Value Details (Name, Color), we need one more query
    all_value_ids = []
    for attr in attrs_map.values():
        all_value_ids.extend(attr['values'].keys())
    
    if all_value_ids:
        Value = self.env['product.attribute.value']
        # Fetch details
        values_data = Value.search_read(
            [('id', 'in', all_value_ids)],
            ['id', 'name', 'attribute_id', 'html_color', 'is_custom']
        )
        
        # Remap details back to structure
        for val in values_data:
            attr_id = val['attribute_id'][0]
            if attr_id in attrs_map and val['id'] in attrs_map[attr_id]['values']:
                attrs_map[attr_id]['values'][val['id']] = {
                    'id': val['id'],
                    'name': val['name'],
                    'html_color': val['html_color']
                }

    # Format Attributes List
    attributes = []
    for attr in attrs_map.values():
        values_list = [v for k, v in attr['values'].items() if isinstance(v, dict)]
        if values_list:
            attributes.append({
                'id': attr['id'],
                'name': attr['name'],
                'values': values_list
            })

    return {
        'brands': brands,
        'categories': categs_data,
        'tags': tags_data,
        'attributes': attributes,
        'price_range': {'min': min_price, 'max': max_price}
    }
```

## 6. Client-Side Integration (Frontend)

1.  **Initial Load**: Call API with no filters -> Get full product list + Global filters.
2.  **User Selects Filter (e.g., Brand=Apple)**:
    -   Update State: `selectedBrands = [1]`
    -   Call API: `POST /products { brand_ids: [1] }`
    -   **Update UI**:
        -   Replace Product Grid with new results.
        -   **Update Sidebar**:
            -   Keep "Brands" selected.
            -   Update "Categories" (maybe only show categories containing Apple products).
            -   Update "Attributes" (only show attributes relevant to Apple products).

### User Experience Tip
*   **Sticky Selection**: If a user selects a filter that eliminates all other options, show "0 results" but keep the filter selected so they can uncheck it.
*   **Debounce**: Wait 300-500ms after user clicks a checkbox before triggering the API to avoid spamming requests.
