"""Digest emails."""

from .mailer import Message

PERIOD_WORDS = {"daily": "today", "weekly": "this week"}


def render_digest(user, digest, cadence, settings):
    """The digest email for ``user``. ``cadence`` is "daily" or "weekly"."""
    lines = [f"Hi {user.name or 'there'},", "", f"Here is what happened {PERIOD_WORDS[cadence]}."]
    for section in digest.sections:
        lines += ["", f"{section.title} ({section.total})"]
        for event in section.events:
            lines.append(f"- {event.subject}")
            if event.url:
                lines.append(f"  {event.url}")
        if section.more:
            lines.append(f"- and {section.more} more")
    lines += [
        "",
        "--",
        f"You get this {cadence} digest because of your notification settings.",
        f"Change them at {settings.preferences_url}",
    ]
    return Message(
        to=user.email,
        subject=f"{digest.total} {'update' if digest.total == 1 else 'updates'} {PERIOD_WORDS[cadence]}",
        body="\n".join(lines) + "\n",
        sender=settings.digest_sender,
        category=f"digest-{cadence}",
    )
