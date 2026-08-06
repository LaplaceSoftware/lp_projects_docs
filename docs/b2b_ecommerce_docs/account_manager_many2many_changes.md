# Account Manager Field: Hybrid Approach (Keep Old + Add New Many2many)

## Overview

This document outlines the changes required to add a new Many2many field for additional account managers while keeping the existing Many2one field for the primary account manager (used in chat).

**Approach:**
- **Keep:** `account_manager_user_id` (Many2one) - Primary account manager, used for chat
- **Add:** `account_manager_user_ids` (Many2many) - Additional account managers

This hybrid approach allows:
- Multiple account managers per company
- The same user to be an account manager for multiple companies
- Primary account manager designated for chat functionality
- Permission management handled by a separate module

---

## Change Summary

**Fields:**
- **Existing Field (Keep):** `account_manager_user_id` (Many2one) - Primary account manager for chat
- **New Field (Add):** `account_manager_user_ids` (Many2many) - Additional account managers

**Total Files Affected:** 6 files
**Total Endpoints Modified:** 13 endpoints

---

## File: `ecommerce/models/res_partner.py`

### 1. Add New Field Definition (After Line 20)

**Add after existing `account_manager_user_id`:**
```python
account_manager_user_ids = fields.Many2many(
    'res.users',
    'res_partner_account_manager_rel',
    'partner_id',
    'user_id',
    string='Additional Account Managers',
    domain="[('is_account_manager', '=', True)]",
    help='Additional account managers besides the primary one',
)
```

---

### 2. `create` Method (Line 40-41)

**No Change** - Keep existing logic for primary account manager

```python
if not partner.account_manager_user_id and current_user_id:
    partner.account_manager_user_id = current_user_id
# Note: account_manager_user_ids remains empty by default
```

---

### 3. `_get_or_create_portal_channel` Method (Line 71-72)

**Before:**
```python
if company_partner.account_manager_user_id:
    channel.add_members(partner_ids=[company_partner.account_manager_user_id.partner_id.id])
```

**After:**
```python
# Add primary account manager
if company_partner.account_manager_user_id:
    channel.add_members(partner_ids=[company_partner.account_manager_user_id.partner_id.id])
# Add additional account managers
for manager in company_partner.account_manager_user_ids:
    channel.add_members(partner_ids=[manager.partner_id.id])
```

---

### 4. `api_get_clients` Filter (Line 134)

**Before:**
```python
domain.append(('account_manager_user_id', '=', current_user_id))
```

**After:**
```python
# Check if user is primary account manager OR additional account manager
domain.append('|')
domain.append(('account_manager_user_id', '=', current_user_id))
domain.append(('account_manager_user_ids', 'in', current_user_id))
```

---

### 5. `api_get_client` Permission Check (Line 215)

**Before:**
```python
if partner.account_manager_user_id.id != current_user_id:
    return {
        'response_code': ClientApiErrors.CLIENT_NOT_FOUND
    }
```

**After:**
```python
is_primary_manager = partner.account_manager_user_id.id == current_user_id if partner.account_manager_user_id else False
is_additional_manager = current_user_id in partner.account_manager_user_ids.ids
if not (is_primary_manager or is_additional_manager):
    return {
        'response_code': ClientApiErrors.CLIENT_NOT_FOUND
    }
```

---

### 6. `_prepare_partner_values_from_api` (Line 393)

**Before:**
```python
if 'account_manager_user_id' in data:
    partner_vals['account_manager_user_id'] = data['account_manager_user_id']
```

**After:**
```python
if 'account_manager_user_id' in data:
    partner_vals['account_manager_user_id'] = data['account_manager_user_id']
if 'account_manager_user_ids' in data:
    partner_vals['account_manager_user_ids'] = data['account_manager_user_ids']
```

---

### 7. `_prepare_partner_values_from_api` Default Value (Line 433-436)

**No Change** - Keep existing logic for primary account manager

```python
# No change - keep existing logic for primary account manager
# Additional managers are set explicitly via API
```

---

### 8. `get_client_details` Serialization (Line 484-487)

**Before:**
```python
'account_manager': {
    'id': self.account_manager_user_id.id if self.account_manager_user_id else None,
    'name': self.account_manager_user_id.name if self.account_manager_user_id else ''
} if self.account_manager_user_id else None,
```

**After:**
```python
'account_manager': {
    'id': self.account_manager_user_id.id if self.account_manager_user_id else None,
    'name': self.account_manager_user_id.name if self.account_manager_user_id else ''
} if self.account_manager_user_id else None,
'additional_account_managers': [
    {
        'id': manager.id,
        'name': manager.name
    }
    for manager in self.account_manager_user_ids
],
```

---

## File: `ecommerce/models/sale_order.py`

### 9. `api_get_orders` Filter (Line 745)

**Before:**
```python
managed_companies = self.env['res.partner'].sudo().search([
    ('account_manager_user_id', '=', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True)
])
```

**After:**
```python
managed_companies = self.env['res.partner'].sudo().search([
    '|',
    ('account_manager_user_id', '=', user.id),
    ('account_manager_user_ids', 'in', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True)
])
```

---

## File: `ecommerce/models/ir_attachment.py`

### 10. `_check_record_access` Filter for sale.order (Line 107)

**Before:**
```python
managed_companies = self.env['res.partner'].sudo().search([
    ('account_manager_user_id', '=', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True)
])
```

**After:**
```python
managed_companies = self.env['res.partner'].sudo().search([
    '|',
    ('account_manager_user_id', '=', user.id),
    ('account_manager_user_ids', 'in', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True)
])
```

---

### 11. `_check_record_access` Permission Check for res.partner (Line 114)

**Before:**
```python
return record.account_manager_user_id == user
```

**After:**
```python
is_primary_manager = record.account_manager_user_id == user if record.account_manager_user_id else False
is_additional_manager = user in record.account_manager_user_ids
return is_primary_manager or is_additional_manager
```

---

## File: `ecommerce/controllers/notification_api.py`

### 12. `list_notifications` Filter (Line 47)

**Before:**
```python
managed_companies = request.env['res.partner'].sudo().search([
    ('account_manager_user_id', '=', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True)
])
```

**After:**
```python
managed_companies = request.env['res.partner'].sudo().search([
    '|',
    ('account_manager_user_id', '=', user.id),
    ('account_manager_user_ids', 'in', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True)
])
```

---

### 13. `mark_notification_seen` Filter (Line 146)

**Before:**
```python
managed_companies = request.env['res.partner'].sudo().search([
    ('account_manager_user_id', '=', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True)
])
```

**After:**
```python
managed_companies = request.env['res.partner'].sudo().search([
    '|',
    ('account_manager_user_id', '=', user.id),
    ('account_manager_user_ids', 'in', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True)
])
```

---

### 14. `mark_all_notifications_seen` Filter (Line 183)

**Before:**
```python
managed_companies = request.env['res.partner'].sudo().search([
    ('account_manager_user_id', '=', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True),
])
```

**After:**
```python
managed_companies = request.env['res.partner'].sudo().search([
    '|',
    ('account_manager_user_id', '=', user.id),
    ('account_manager_user_ids', 'in', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True),
])
```

---

## File: `ecommerce/controllers/portal_chat_api.py`

### 15. `init_chat` DM Mode (Line 90)

**No Change Required**

**Keep as is:**
```python
am_user = company.account_manager_user_id
if not am_user:
    return self.api_response(response_code='100', response_message='No Account Manager available')
```

**Reason:** Chat continues to use the primary account manager (`account_manager_user_id`)

---

## File: `ecommerce/controllers_admin/chat_api.py`

### 16. `_get_managed_companies` Filter (Line 46)

**Before:**
```python
managed_companies = request.env['res.partner'].sudo().search([
    ('account_manager_user_id', '=', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True)
])
```

**After:**
```python
managed_companies = request.env['res.partner'].sudo().search([
    '|',
    ('account_manager_user_id', '=', user.id),
    ('account_manager_user_ids', 'in', user.id),
    ('is_company', '=', True),
    ('is_ecommerce_portal', '=', True)
])
```

---

## Endpoints Affected Summary

| File | Method/Endpoint | Line | Change Type |
|------|----------------|------|-------------|
| res_partner.py | Add New Field | After 20 | Add Many2many field |
| res_partner.py | create | 40-41 | No change |
| res_partner.py | _get_or_create_portal_channel | 71-72 | Add loop |
| res_partner.py | api_get_clients | 134 | Add OR condition |
| res_partner.py | api_get_client | 215 | Add OR check |
| res_partner.py | _prepare_partner_values_from_api | 393 | Add new field |
| res_partner.py | get_client_details | 484-487 | Add serialization |
| sale_order.py | api_get_orders | 745 | Add OR condition |
| ir_attachment.py | _check_record_access | 107 | Add OR condition |
| ir_attachment.py | _check_record_access | 114 | Add OR check |
| notification_api.py | list_notifications | 47 | Add OR condition |
| notification_api.py | mark_notification_seen | 146 | Add OR condition |
| notification_api.py | mark_all_notifications_seen | 183 | Add OR condition |
| portal_chat_api.py | init_chat | 90 | No change |
| chat_api.py | _get_managed_companies | 46 | Add OR condition |

---

## Change Patterns

### Filter Changes (OR Condition)

**Pattern:**
```python
# Before
('account_manager_user_id', '=', user_id)

# After
'|',
('account_manager_user_id', '=', user_id),
('account_manager_user_ids', 'in', user_id)
```

---

### Permission Check Changes (OR Logic)

**Pattern:**
```python
# Before
partner.account_manager_user_id == user

# After
is_primary_manager = partner.account_manager_user_id == user if partner.account_manager_user_id else False
is_additional_manager = user in partner.account_manager_user_ids
return is_primary_manager or is_additional_manager
```

---

### Serialization Changes (Add Additional Field)

**Pattern:**
```python
# Before
'account_manager': {
    'id': self.account_manager_user_id.id,
    'name': self.account_manager_user_id.name
}

# After
'account_manager': {
    'id': self.account_manager_user_id.id,
    'name': self.account_manager_user_id.name
},
'additional_account_managers': [
    {
        'id': manager.id,
        'name': manager.name
    }
    for manager in self.account_manager_user_ids
]
```

---

## Migration Notes

1. **Database Migration Required:** A migration script will be needed to:
   - Create the new many2many relation table `res_partner_account_manager_rel`
   - No data migration needed for existing `account_manager_user_id` (field is kept)
   - The new field `account_manager_user_ids` will be empty by default

2. **API Contract Changes:** 
   - API responses will now return both `account_manager` (object) and `additional_account_managers` (array)
   - API requests can send both `account_manager_user_id` (single) and `account_manager_user_ids` (array)

3. **UI Changes:**
   - Views need to be updated to show both primary and additional account managers
   - Primary manager: many2one widget (existing)
   - Additional managers: many2many widget (new)

4. **Testing:**
   - Test all 16 affected endpoints
   - Verify permission checks work correctly with both primary and additional managers
   - Test channel creation with all managers (primary + additional)
   - Verify notification distribution to all managers
   - Verify chat still uses primary account manager only

5. **Backward Compatibility:**
   - Existing `account_manager_user_id` remains unchanged
   - Chat functionality continues to work without modification
   - Existing API calls using `account_manager_user_id` continue to work

---

## Implementation Checklist

- [ ] Add new field definition in res_partner.py
- [ ] Update _get_or_create_portal_channel in res_partner.py
- [ ] Update api_get_clients in res_partner.py
- [ ] Update api_get_client in res_partner.py
- [ ] Update _prepare_partner_values_from_api in res_partner.py
- [ ] Update get_client_details in res_partner.py
- [ ] Update api_get_orders in sale_order.py
- [ ] Update _check_record_access in ir_attachment.py
- [ ] Update list_notifications in notification_api.py
- [ ] Update mark_notification_seen in notification_api.py
- [ ] Update mark_all_notifications_seen in notification_api.py
- [ ] No change needed for portal_chat_api.py init_chat
- [ ] Update _get_managed_companies in chat_api.py
- [ ] Create database migration script (new table only)
- [ ] Update XML views (add additional managers widget)
- [ ] Test all endpoints
- [ ] Update API documentation

---

## Field Usage Summary

| Field | Type | Purpose | Used In |
|-------|------|---------|---------|
| `account_manager_user_id` | Many2one | Primary account manager | Chat, All filters/checks |
| `account_manager_user_ids` | Many2many | Additional account managers | All filters/checks, Channel members |

**Note:** Both fields are used together in filters and permission checks using OR logic.

