"""How far back a request has to reach.

The rates already in Home Assistant's statistics decide it: there is no point
asking for a year every three hours to learn one new number. Each request goes
one day further back than it strictly needs, so nothing is missed at the edges.
"""

from __future__ import annotations

from datetime import date

from .const import MAX_DAYS, MIN_SPAN_DAYS, SAFETY_DAYS


def span_days(newest: date | None, today: date, seed: int) -> int:
    """
    The number of days to ask for.

    Nothing known yet means seeding the whole history the user asked for.
    Otherwise it is the distance to the newest rate that is already stored,
    which heals a gap of any length by itself: a weekend needs three days, a
    fortnight's outage needs fourteen.

    It is never shorter than MIN_SPAN_DAYS. The newest stored day can be today even
    when today's rate isn't out, because the recorder keeps hourly statistics of the
    sensor under the same id, and a request that finds no rates is refused.
    """
    if newest is None:
        needed = seed
    else:
        needed = max((today - newest).days, 0)

    return min(max(needed + SAFETY_DAYS, MIN_SPAN_DAYS), MAX_DAYS)
