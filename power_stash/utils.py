from datetime import datetime
from typing import List, Tuple

from dateutil.relativedelta import relativedelta


def generate_monthly_datetime_chunks(
    start: datetime,
    end: datetime,
    n_months: int,
) -> List[Tuple[datetime, datetime]]:
    """Create chunks of dates of a given monthly candence."""
    chunks = []
    current_start = start
    while current_start < end:
        current_end = current_start + relativedelta(months=n_months)
        # Ensure that the end date is not beyond the overall end date
        current_end = min(current_end, end)
        chunks.append((current_start, current_end))
        current_start = current_end
    return chunks
