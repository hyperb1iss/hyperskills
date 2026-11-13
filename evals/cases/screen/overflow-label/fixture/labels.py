"""Short human-readable labels for the dashboard."""


def tag_label(tags, limit=3):
    """Join tags for display, collapsing the overflow."""
    if not tags:
        return "no tags"
    shown = ", ".join(tags[:limit])
    extra = len(tags) - limit
    if extra <= 0:
        return shown
    return f"{shown} and {extra} more"


def recipient_label(names, limit=2):
    """Join recipient names for display, collapsing the overflow."""
    raise NotImplementedError
