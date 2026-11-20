"""Authorization helpers for API handlers."""


def can_access_warehouse(principal, warehouse_id):
    """Whether the principal may read or move stock in ``warehouse_id``."""
    return principal.is_admin or warehouse_id in principal.warehouses


def visible_warehouses(principal, warehouse_ids):
    """The subset of ``warehouse_ids`` the principal may access, order kept."""
    return [warehouse_id for warehouse_id in warehouse_ids if can_access_warehouse(principal, warehouse_id)]
