from dataclasses import dataclass
from datetime import datetime
from typing import Optional

ACTIVE = "active"
CANCELLED = "cancelled"


@dataclass
class Event:
    id: str
    name: str
    capacity: int
    starts_at: datetime


@dataclass
class Ticket:
    id: int
    event_id: str
    buyer: str
    status: str = ACTIVE


@dataclass
class Reservation:
    event_id: str
    buyer: str
    ticket: Optional[Ticket] = None
    waitlist_position: Optional[int] = None

    @property
    def confirmed(self):
        return self.ticket is not None
