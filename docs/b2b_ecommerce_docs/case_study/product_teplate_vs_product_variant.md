Here is the **clear explanation** in **technical Odoo terms**, with **examples**, **IDs**, and **how an external portal shop should handle products and sale orders**.

---

# ✅ **1. Main Difference: `product.product` vs `product.template`**

### **`product.template`**

* Represents the **generic product**.
* Holds **general product info**:

  * Name
  * Description
  * Category
  * UoM
  * Sales price
  * Images
  * Tracking
  * Variant attributes
* Has **one record per product template**, regardless of variants.

### **`product.product`**

* Represents a **product variant**.
* Stores **variant-specific data**:

  * Attribute combinations (color, size, etc.)
  * Barcode
  * SKU/internal reference
  * Volume/weight
  * Variant image
* There can be **multiple product.product records per product.template**.

### **Relation**

```text
product.product.product_tmpl_id → points to product.template
product.template has many product.product variants
```

---

# ✅ **2. Example With Data: Product Tables & IDs**

## **Example**

Product: *T-Shirt*
Variants:

* Red / M
* Red / L
* Blue / M

### **Table: product.template**

| id | name    | list_price |
| -- | ------- | ---------- |
| 10 | T-Shirt | 500        |

This is the **template**.

### **Table: product.product**

| id  | product_tmpl_id | name           | barcode |
| --- | --------------- | -------------- | ------- |
| 101 | 10              | T-Shirt Red M  | TS-R-M  |
| 102 | 10              | T-Shirt Red L  | TS-R-L  |
| 103 | 10              | T-Shirt Blue M | TS-B-M  |

All variants link to **template 10**.

---

# ✅ **3. When Do You Read Template vs Variant?**

| Use Case                                           | Read From          | Why                                                             |
| -------------------------------------------------- | ------------------ | --------------------------------------------------------------- |
| Product list on website                            | `product.template` | Templates are the main products. Usually one page per template. |
| Selecting variant attributes                       | `product.product`  | Each variant has its own ID.                                    |
| Stock availability                                 | `product.product`  | Stock is maintained per variant.                                |
| Adding to cart                                     | `product.product`  | Sale order lines require product.product.                       |
| Displaying product details (description, pictures) | `product.template` | Template carries general info.                                  |

---

# ✅ **4. **External Portal Shop Architecture**

### **(Custom B2B portal, Next.js, mobile app, etc.)**

Your external portal should **never work with product.template only**.

### **Portal needs to:**

### **1. Read templates for catalog**

```
GET /product.template?fields=["name","image","website_price"]
```

### **2. Read variants for real transactions**

```
GET /product.product?fields=["id","product_tmpl_id","barcode","combination_indices"]
```

### **3. Add to cart → MUST use product.product**

Sale order lines require:

```python
order_line.product_id  = product.product(id)
order_line.product_uom_qty
order_line.price_unit
```

Even if the product has no variants, Odoo still creates **one product.product**.

---

# ✅ **5. When creating sale orders: which table? which ID?**

From the reference:
🔗 `sale/models/sale_order.py`

### **Sale Order Line (`sale.order.line`)**

These fields exist:

```python
product_id = fields.Many2one('product.product')
order_id = fields.Many2one('sale.order')
```

### ❗ Important:

* `product_id` **always points to product.product**
* **Never** pass product.template ID

### Example Request

External shop sends order:

```json
{
  "partner_id": 45,
  "order_line": [
    {
      "product_id": 101,
      "product_uom_qty": 2
    }
  ]
}
```

If you send `product_id = 10` (template ID) → **error**.

---

# ✅ **6. Full Example: External Portal Workflow**

### **Step 1: Load Products**

```python
GET /product.template
```

Portal displays product list.

### **Step 2: User selects attributes**

Portal calls:

```python
GET /product.product?domain=[("product_tmpl_id","=",10)]
```

Returns variants (101, 102, 103).

### **Step 3: Add to Cart**

Portal POSTs:

```json
{
  "product_id": 102, 
  "quantity": 3
}
```

### **Step 4: Create Sale Order**

Odoo:

* uses `sale.order`
* lines point to product.product only

---

# ✅ **7. Summary**

### **Difference**

* `product.template` = product master
* `product.product` = variant

### **External Shop Depends On**

| Feature                   | Use              |
| ------------------------- | ---------------- |
| Product list              | product.template |
| Product variant selection | product.product  |
| Stock                     | product.product  |
| Create sale order         | product.product  |

---


