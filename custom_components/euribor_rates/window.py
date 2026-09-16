"""How far back a request has to reach.

The rates already in Home Assistant's statistics decide it: there is no point
asking for a year every three hours to learn one new number. Each request goes
one day further back than it strictly needs, so nothing is missed at the edges.
"""

from __future__ import annotations

from datetime import date

from .const import MAX_DAYS, SAFETY_DAYS


def span_days(newest: date | None, today: date, seed: int) -> int:
    """
    The number of days to ask for.

    Nothing known yet means seeding the whole history the user asked for.
    Otherwise it is the distance to the newest rate that is already stored,
    which heals a gap of any length by itself: a weekend needs three days, a
    fortnight's outage needs fourteen.
    """
    if newest is None:
        needed = seed
    else:
        needed = max((today - newest).days, 0)

    return min(needed + SAFETY_DAYS, MAX_DAYS)
