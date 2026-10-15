import pandas as pd
import psycopg


DAILY_RECORDS_QUERY = """
SELECT
    summary.recorded_on AS date,
    summary.total_free_time_minutes AS free_time_minutes,
    summary.distance_travelled_meters AS distance_meters,
    summary.score,
    COALESCE(MAX(duration.duration_minutes) FILTER (WHERE kind.name = 'sleep'), 0)
        AS sleep_minutes,
    COALESCE(MAX(duration.duration_minutes) FILTER (WHERE kind.name = 'social'), 0)
        AS social_minutes,
    COALESCE(MAX(duration.duration_minutes) FILTER (WHERE kind.name = 'work'), 0)
        AS work_minutes,
    COALESCE(MAX(duration.duration_minutes) FILTER (WHERE kind.name = 'gym'), 0)
        AS gym_minutes
FROM daily_summaries AS summary
LEFT JOIN activity_durations AS duration
    ON duration.daily_summary_id = summary.id
LEFT JOIN activity_types AS kind
    ON kind.id = duration.activity_type_id
GROUP BY summary.id
ORDER BY summary.recorded_on DESC;
"""


def load_records_from_postgres(database_url: str) -> pd.DataFrame:
    """Load daily metric records from PostgreSQL."""
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(DAILY_RECORDS_QUERY)
            rows = cursor.fetchall()
            columns = [column.name for column in cursor.description]

    return pd.DataFrame(rows, columns=columns)
