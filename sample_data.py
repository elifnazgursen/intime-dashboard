import pandas as pd


def load_sample_data() -> pd.DataFrame:
    """Return example daily summaries until a PostgreSQL database is connected."""
    return pd.DataFrame(
        [
            {
                "date": "2026-10-07",
                "free_time_minutes": 245,
                "distance_meters": 7800,
                "score": 68,
                "sleep_minutes": 372,
                "social_minutes": 210,
                "work_minutes": 450,
                "gym_minutes": 0,
            },
            {
                "date": "2026-10-08",
                "free_time_minutes": 280,
                "distance_meters": 10400,
                "score": 81,
                "sleep_minutes": 438,
                "social_minutes": 120,
                "work_minutes": 480,
                "gym_minutes": 72,
            },
            {
                "date": "2026-10-09",
                "free_time_minutes": 210,
                "distance_meters": 8200,
                "score": 59,
                "sleep_minutes": 336,
                "social_minutes": 288,
                "work_minutes": 390,
                "gym_minutes": 0,
            },
            {
                "date": "2026-10-10",
                "free_time_minutes": 265,
                "distance_meters": 12100,
                "score": 76,
                "sleep_minutes": 414,
                "social_minutes": 150,
                "work_minutes": 480,
                "gym_minutes": 48,
            },
            {
                "date": "2026-10-11",
                "free_time_minutes": 330,
                "distance_meters": 6500,
                "score": 52,
                "sleep_minutes": 288,
                "social_minutes": 312,
                "work_minutes": 0,
                "gym_minutes": 0,
            },
            {
                "date": "2026-10-12",
                "free_time_minutes": 300,
                "distance_meters": 9300,
                "score": 73,
                "sleep_minutes": 426,
                "social_minutes": 192,
                "work_minutes": 0,
                "gym_minutes": 90,
            },
            {
                "date": "2026-10-13",
                "free_time_minutes": 255,
                "distance_meters": 9700,
                "score": 74,
                "sleep_minutes": 378,
                "social_minutes": 204,
                "work_minutes": 480,
                "gym_minutes": 18,
            },
        ]
    )
