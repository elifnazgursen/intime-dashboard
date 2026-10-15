import os

import altair as alt
import pandas as pd
import psycopg
import streamlit as st

from database import load_records_from_postgres
from sample_data import load_sample_data


ACTIVITY_COLUMNS = {
    "Sleep": "sleep_minutes",
    "Social time": "social_minutes",
    "Work": "work_minutes",
    "Gym": "gym_minutes",
}


def hours(minutes: float) -> float:
    return minutes / 60


def prepare_data(data: pd.DataFrame) -> pd.DataFrame:
    prepared = data.copy()
    prepared["date"] = pd.to_datetime(prepared["date"])
    prepared["free_time_hours"] = prepared["free_time_minutes"].map(hours)
    prepared["distance_km"] = prepared["distance_meters"] / 1000

    for column in ACTIVITY_COLUMNS.values():
        prepared[column.replace("_minutes", "_hours")] = prepared[column].map(hours)

    prepared["activity_duration_hours"] = (
        prepared["social_hours"] + prepared["work_hours"] + prepared["gym_hours"]
    )
    return prepared.sort_values("date", ascending=False).reset_index(drop=True)


def show_summary(latest_day: pd.Series) -> None:
    st.subheader("Daily summary")
    st.caption(latest_day["date"].strftime("%A, %d %B %Y"))

    columns = st.columns(5)
    metrics = [
        ("Total free time", f"{latest_day['free_time_hours']:.1f} h"),
        ("Distance travelled", f"{latest_day['distance_km']:.1f} km"),
        ("Activity duration", f"{latest_day['activity_duration_hours']:.1f} h"),
        ("Social time", f"{latest_day['social_hours']:.1f} h"),
        ("Score", f"{int(latest_day['score'])} / 100"),
    ]
    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)


def make_activity_table(data: pd.DataFrame) -> pd.DataFrame:
    columns = {
        label: data[column.replace("_minutes", "_hours")]
        for label, column in ACTIVITY_COLUMNS.items()
    }
    activity_data = pd.DataFrame(columns, index=data.index)
    activity_data.insert(0, "Date", data["date"].dt.strftime("%Y-%m-%d"))
    return activity_data.melt(
        id_vars="Date",
        var_name="Activity",
        value_name="Duration (hours)",
    )


def show_daily_data(data: pd.DataFrame) -> None:
    st.subheader("Daily data")
    group_by = st.selectbox("Group by", ["Day", "Activity type"])

    if group_by == "Day":
        sort_by = st.selectbox(
            "Sort by",
            [
                "Newest day",
                "Oldest day",
                "Activity duration: high to low",
                "Activity duration: low to high",
                "Score: high to low",
                "Score: low to high",
            ],
        )
        sort_columns = {
            "Newest day": ("date", False),
            "Oldest day": ("date", True),
            "Activity duration: high to low": ("activity_duration_hours", False),
            "Activity duration: low to high": ("activity_duration_hours", True),
            "Score: high to low": ("score", False),
            "Score: low to high": ("score", True),
        }
        column, ascending = sort_columns[sort_by]
        sorted_data = data.sort_values(column, ascending=ascending)
        table = pd.DataFrame(
            {
                "Day": sorted_data["date"].dt.strftime("%Y-%m-%d"),
                "Free time (h)": sorted_data["free_time_hours"].round(1),
                "Distance (km)": sorted_data["distance_km"].round(1),
                "Sleep (h)": sorted_data["sleep_hours"].round(1),
                "Social time (h)": sorted_data["social_hours"].round(1),
                "Work (h)": sorted_data["work_hours"].round(1),
                "Gym (h)": sorted_data["gym_hours"].round(1),
                "Activity duration (h)": sorted_data["activity_duration_hours"].round(1),
                "Score": sorted_data["score"].astype(int),
            }
        )
    else:
        sort_by = st.selectbox(
            "Sort by",
            ["Newest day", "Oldest day", "Duration: high to low", "Duration: low to high"],
        )
        table = make_activity_table(data)
        if sort_by == "Newest day":
            table = table.sort_values(["Date", "Activity"], ascending=[False, True])
        elif sort_by == "Oldest day":
            table = table.sort_values(["Date", "Activity"], ascending=[True, True])
        elif sort_by == "Duration: high to low":
            table = table.sort_values("Duration (hours)", ascending=False)
        else:
            table = table.sort_values("Duration (hours)", ascending=True)
        table["Duration (hours)"] = table["Duration (hours)"].round(1)

    st.dataframe(table, hide_index=True, use_container_width=True)


def show_sleep_social_chart(data: pd.DataFrame) -> None:
    st.subheader("Sleep & social life")
    st.caption("Compare daily sleep duration and social time.")

    chronological_data = data.sort_values("date").copy()
    chronological_data["Day"] = chronological_data["date"].dt.strftime("%d %b")
    chart_data = chronological_data[["Day", "sleep_hours", "social_hours"]].rename(
        columns={"sleep_hours": "Sleep", "social_hours": "Social life"}
    ).melt(
        id_vars="Day",
        var_name="Activity",
        value_name="Duration (hours)",
    )

    chart = (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("Day:N", title="Date", axis=alt.Axis(labelAngle=0), sort=None),
            y=alt.Y("Duration (hours):Q", title="Duration (hours)"),
            xOffset=alt.XOffset("Activity:N"),
            color=alt.Color("Activity:N", title=""),
            tooltip=[
                alt.Tooltip("Day:N", title="Date"),
                alt.Tooltip("Activity:N", title="Activity"),
                alt.Tooltip("Duration (hours):Q", format=".1f"),
            ],
        )
    )
    st.altair_chart(
        chart,
        use_container_width=True,
        theme="streamlit",
    )


def main() -> None:
    st.set_page_config(page_title="Activity Dashboard", layout="wide")
    st.title("Activity Dashboard")

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:
            records = load_records_from_postgres(database_url)
        except psycopg.Error as error:
            st.error(f"Could not load dashboard data from PostgreSQL: {error}")
            st.stop()
        st.caption("Data source: PostgreSQL")
    else:
        records = load_sample_data()
        st.info("Showing sample data. Set DATABASE_URL to load data from PostgreSQL.")

    if records.empty:
        st.warning("No daily records found.")
        st.stop()

    data = prepare_data(records)
    show_summary(data.iloc[0])
    st.divider()
    show_daily_data(data)
    st.divider()
    show_sleep_social_chart(data)


if __name__ == "__main__":
    main()
