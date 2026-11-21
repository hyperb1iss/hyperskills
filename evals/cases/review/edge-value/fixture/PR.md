# Waitlist for sold-out events

Sold-out events now put buyers on a waitlist instead of rejecting the order. `reserve()` returns a `Reservation` that carries either the ticket or the buyer's place in line, and the buyer gets an email saying how many people are ahead of them. Cancelling a ticket gives the seat to the first waiting buyer and emails them the new ticket.

Seats are now counted from active tickets instead of the `sold` counter on `Event`. Cancellations and promotions both change availability, and keeping a separate counter in step with both was easy to get wrong. `SoldOut` is gone, and `cancel()` returns the promoted ticket, if any.
