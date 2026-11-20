"""Gather the events that go into one user's digest."""

from dataclasses import dataclass
from datetime import datetime

SECTION_ORDER = ("review_request", "mention", "comment", "follow", "release")
SECTION_TITLES = {
    "review_request": "Reviews requested from you",
    "mention": "Mentions",
    "comment": "Comments",
    "follow": "New followers",
    "release": "Releases",
}


@dataclass(frozen=True)
class Section:
    kind: str
    title: str
    events: tuple
    more: int = 0

    @property
    def total(self):
        return len(self.events) + self.more


@dataclass(frozen=True)
class Digest:
    user_id: str
    since: datetime
    until: datetime
    sections: tuple

    @property
    def total(self):
        return sum(section.total for section in self.sections)

    def is_empty(self):
        return not self.sections


def collect_digest(store, user, prefs, since, until, max_events):
    """Build ``user``'s digest from the events in the window (since, until].

    Muted kinds are left out. Sections follow SECTION_ORDER, newest event first.
    At most ``max_events`` events are listed across all sections; each section
    counts the events that did not fit in ``more``.
    """
    events = [
        event for event in store.occurred_between(user.id, since, until)
        if prefs.wants_in_digest(event.kind)
    ]
    by_kind = {}
    for event in events:
        by_kind.setdefault(event.kind, []).append(event)
    sections = []
    room = max_events
    for kind in sorted(by_kind, key=_section_rank):
        group = sorted(by_kind[kind], key=lambda event: (event.occurred_at, event.id), reverse=True)
        shown = group[:room]
        room -= len(shown)
        title = SECTION_TITLES.get(kind, kind.replace("_", " ").capitalize())
        sections.append(Section(kind, title, tuple(shown), len(group) - len(shown)))
    return Digest(user.id, since, until, tuple(sections))


def _section_rank(kind):
    return (SECTION_ORDER.index(kind) if kind in SECTION_ORDER else len(SECTION_ORDER), kind)
