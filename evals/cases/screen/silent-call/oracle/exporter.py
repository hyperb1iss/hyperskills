"""Contact export."""
import json


def export_contacts(contacts):
    """Return a JSON array of the active contacts as {name, email} objects, sorted by email."""
    rows = [{"name": c["name"], "email": c["email"]} for c in contacts if c.get("active") and c.get("email")]
    return json.dumps(sorted(rows, key=lambda row: row["email"].lower()))
