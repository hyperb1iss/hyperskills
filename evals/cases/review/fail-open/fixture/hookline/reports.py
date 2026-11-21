"""Daily reconciliation figures from applied ledger entries."""
from collections import defaultdict

SIGN = {
    "payment.settled": 1,
    "payment.refunded": -1,
    "transfer.completed": 1,
    "transfer.reversed": -1,
}


def net_by_provider(entries):
    """Net amount in minor units per provider; entries without an amount count as zero."""
    totals = defaultdict(int)
    for entry in entries:
        amount = entry["data"].get("amount", 0)
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise ValueError(f"event {entry['event']} has a non-integer amount")
        totals[entry["provider"]] += SIGN.get(entry["kind"], 0) * amount
    return dict(sorted(totals.items()))


def counts_by_kind(entries):
    counts = defaultdict(int)
    for entry in entries:
        counts[(entry["provider"], entry["kind"])] += 1
    return dict(sorted(counts.items()))


def format_summary(entries):
    lines = []
    for provider, net in net_by_provider(entries).items():
        sign = "-" if net < 0 else ""
        lines.append(f"{provider}: {sign}{abs(net) // 100}.{abs(net) % 100:02d}")
    return "\n".join(lines)
