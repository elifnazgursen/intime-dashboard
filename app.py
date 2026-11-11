from pathlib import Path
from typing import IO

import altair as alt
import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).parent / "data"
PUBLISHED_DATA_DIR = Path(__file__).parent / "public_data"


DAILY_REQUIRED_COLUMNS = {
    "date",
    "commuting_hours",
    "completed_commute_sessions",
    "estimated_distance_km",
    "average_recorded_sleep_session_hours",
    "completed_sleep_sessions",
    "study_hours",
    "hobby_hours",
    "eating_hours",
}
WEEKLY_REQUIRED_COLUMNS = {
    "week_start",
    "week_end",
    "days_with_data",
    "average_daily_commuting_hours",
    "average_daily_estimated_distance_km",
    "average_recorded_sleep_session_hours",
    "average_daily_study_hours",
    "average_daily_hobby_hours",
    "average_daily_eating_hours",
}
OVERALL_REQUIRED_COLUMNS = {
    "tracking_start_date",
    "tracking_end_date",
    "days_with_any_data",
    "total_commuting_hours",
    "total_estimated_distance_km",
    "total_reconstructed_recorded_sleep_hours",
    "total_study_hours",
    "total_hobby_hours",
    "total_eating_hours",
}

CSV_ACTIVITY_COLUMNS = {
    "Commuting": "commuting_hours",
    "Average sleep session": "average_recorded_sleep_session_hours",
    "Study": "study_hours",
    "Hobby": "hobby_hours",
    "Eating": "eating_hours",
}


def read_csv_file(
    file_path: Path,
    label: str,
    required_columns: set[str],
    date_columns: tuple[str, ...],
) -> pd.DataFrame:
    if not file_path.is_file():
        st.error(f"Required data file not found: {file_path.name}")
        st.stop()
    try:
        data = pd.read_csv(file_path)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        st.error(f"Could not read {label}: {error}")
        st.stop()

    return validate_csv_data(data, label, required_columns, date_columns)


def read_uploaded_csv_file(
    uploaded_file: IO[bytes],
    label: str,
    required_columns: set[str],
    date_columns: tuple[str, ...],
) -> pd.DataFrame:
    try:
        data = pd.read_csv(uploaded_file)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        st.error(f"Could not read {label}: {error}")
        st.stop()

    return validate_csv_data(data, label, required_columns, date_columns)


def validate_csv_data(
    data: pd.DataFrame,
    label: str,
    required_columns: set[str],
    date_columns: tuple[str, ...],
) -> pd.DataFrame:
    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        st.error(f"{label} is missing columns: {', '.join(sorted(missing_columns))}")
        st.stop()
    if data.empty:
        st.error(f"{label} contains no data rows.")
        st.stop()

    for column in date_columns:
        parsed_dates = pd.to_datetime(data[column], errors="coerce")
        if parsed_dates.isna().any():
            st.error(f"{label} contains an invalid date in '{column}'.")
            st.stop()
        data[column] = parsed_dates

    return data


def format_value(value: object, unit: str = "", precision: int = 1) -> str:
    if pd.isna(value):
        return "—"
    return f"{float(value):,.{precision}f}{f' {unit}' if unit else ''}"


def make_interactive_trend_chart(
    data: pd.DataFrame,
    date_column: str,
    series_column: str,
    date_title: str,
    value_title: str,
    date_format: str = "%b %d",
) -> alt.Chart:
    legend_selection = alt.selection_point(
        fields=[series_column],
        bind="legend",
        toggle="true",
    )
    return (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                f"{date_column}:T",
                title=date_title,
                axis=alt.Axis(format=date_format, labelAngle=0),
            ),
            y=alt.Y("Hours:Q", title=value_title),
            color=alt.Color(
                f"{series_column}:N",
                title="Click legend items to highlight",
                legend=alt.Legend(orient="right"),
            ),
            opacity=alt.condition(
                legend_selection,
                alt.value(1),
                alt.value(0.12),
            ),
            tooltip=[
                alt.Tooltip(
                    f"{date_column}:T",
                    title=date_title,
                    format="%Y-%m-%d",
                ),
                alt.Tooltip(f"{series_column}:N", title=series_column),
                alt.Tooltip("Hours:Q", format=".2f"),
            ],
        )
        .add_params(legend_selection)
    )


def show_csv_dashboard(
    daily: pd.DataFrame,
    weekly: pd.DataFrame,
    overall: pd.DataFrame,
) -> None:
    overall_row = overall.iloc[0]

    st.subheader("Daily summary")
    selected_date = st.selectbox(
        "Select a day",
        options=sorted(daily["date"].dt.date.unique(), reverse=True),
        format_func=lambda value: value.strftime("%A, %B %d, %Y"),
    )
    day = daily.loc[daily["date"].dt.date == selected_date].iloc[0]

    primary_metrics = st.columns(3)
    for column, (label, field, unit, precision) in zip(
        primary_metrics,
        [
            ("Commute duration", "commuting_hours", "hours", 1),
            ("Estimated distance", "estimated_distance_km", "km", 3),
            (
                "Average sleep session",
                "average_recorded_sleep_session_hours",
                "hours",
                1,
            ),
        ],
    ):
        column.metric(label, format_value(day[field], unit, precision))

    st.caption(
        "Sleep is shown as the average recorded session, not a daily total."
    )

    other_metrics = st.columns(3)
    for column, (label, field) in zip(
        other_metrics,
        [
            ("Study", "study_hours"),
            ("Hobby", "hobby_hours"),
            ("Eating", "eating_hours"),
        ],
    ):
        column.metric(label, format_value(day[field], "hours"))

    st.subheader("Selected day's recorded activities")
    st.caption(
        "Sleep is an average session; the other bars show daily totals."
    )
    activity_chart_data = pd.DataFrame(
        [
            (label, day[field])
            for label, field in CSV_ACTIVITY_COLUMNS.items()
        ],
        columns=["Activity", "Hours"],
    ).dropna()
    if activity_chart_data.empty:
        st.info("No duration data is available for the selected day.")
    else:
        activity_chart = (
            alt.Chart(activity_chart_data)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                x=alt.X("Hours:Q", title="Hours"),
                y=alt.Y("Activity:N", title="", sort="-x"),
                color=alt.Color("Activity:N", legend=None),
                tooltip=[
                    alt.Tooltip("Activity:N"),
                    alt.Tooltip("Hours:Q", format=".2f"),
                ],
            )
        )
        st.altair_chart(activity_chart, width="stretch", theme="streamlit")

    with st.expander("Daily record details"):
        st.write(
            "Completed commute sessions: "
            f"{format_value(day['completed_commute_sessions'])}"
        )
        st.write(
            f"Recorded sleep sessions: {format_value(day['completed_sleep_sessions'])}"
        )

    st.divider()
    st.subheader("Activity trends")
    daily_tab, weekly_tab = st.tabs(["Daily trend", "Weekly overview"])
    with daily_tab:
        trend_data = daily[["date", *CSV_ACTIVITY_COLUMNS.values()]].rename(
            columns={field: label for label, field in CSV_ACTIVITY_COLUMNS.items()}
        ).melt(
            id_vars="date",
            var_name="Activity",
            value_name="Hours",
        ).dropna()
        if trend_data.empty:
            st.info("There is not enough data to show a daily trend.")
        else:
            st.caption("Click one or more legend items to highlight activities.")
            trend_chart = make_interactive_trend_chart(
                trend_data,
                "date",
                "Activity",
                "Date",
                "Hours",
            )
            st.altair_chart(trend_chart, width="stretch", theme="streamlit")

        daily_table = daily[
            [
                "date",
                "commuting_hours",
                "estimated_distance_km",
                "average_recorded_sleep_session_hours",
                "study_hours",
                "hobby_hours",
                "eating_hours",
            ]
        ].rename(
            columns={
                "date": "Date",
                "commuting_hours": "Commute (hours)",
                "estimated_distance_km": "Estimated distance (km)",
                "average_recorded_sleep_session_hours": "Avg. sleep session (hours)",
                "study_hours": "Study (hours)",
                "hobby_hours": "Hobby (hours)",
                "eating_hours": "Eating (hours)",
            }
        )
        daily_table["Date"] = daily_table["Date"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            daily_table.sort_values("Date", ascending=False),
            hide_index=True,
            width="stretch",
        )

    with weekly_tab:
        weekly_activity_columns = {
            "Avg. daily commute": "average_daily_commuting_hours",
            "Avg. sleep session": "average_recorded_sleep_session_hours",
        }
        weekly_trend = weekly[
            [
                "week_start",
                *weekly_activity_columns.values(),
            ]
        ].rename(
            columns={
                "week_start": "Week",
                **{
                    field: label
                    for label, field in weekly_activity_columns.items()
                },
            }
        ).melt(
            id_vars="Week",
            var_name="Measure",
            value_name="Hours",
        ).dropna()
        if not weekly_trend.empty:
            st.caption("Click one or more legend items to highlight measures.")
            weekly_chart = make_interactive_trend_chart(
                weekly_trend,
                "Week",
                "Measure",
                "Week starting",
                "Average hours",
            )
            st.altair_chart(weekly_chart, width="stretch", theme="streamlit")
        else:
            st.info("There is not enough data to show a weekly trend.")

        weekly_table = weekly[
            [
                "week_start",
                "week_end",
                "days_with_data",
                "average_daily_commuting_hours",
                "average_daily_estimated_distance_km",
                "average_recorded_sleep_session_hours",
                "average_daily_study_hours",
                "average_daily_hobby_hours",
                "average_daily_eating_hours",
            ]
        ].rename(
            columns={
                "week_start": "Week starting",
                "week_end": "Week ending",
                "days_with_data": "Days with data",
                "average_daily_commuting_hours": "Avg. daily commute (hours)",
                "average_daily_estimated_distance_km": "Avg. daily distance (km)",
                "average_recorded_sleep_session_hours": "Avg. sleep session (hours)",
                "average_daily_study_hours": "Avg. daily study (hours)",
                "average_daily_hobby_hours": "Avg. daily hobby (hours)",
                "average_daily_eating_hours": "Avg. daily eating (hours)",
            }
        )
        for column in ("Week starting", "Week ending"):
            weekly_table[column] = weekly_table[column].dt.strftime("%Y-%m-%d")
        st.dataframe(
            weekly_table.sort_values("Week starting", ascending=False),
            hide_index=True,
            width="stretch",
        )

    with st.expander("Full-period summary"):
        st.caption(
            f"{overall_row['tracking_start_date']:%Y-%m-%d} – "
            f"{overall_row['tracking_end_date']:%Y-%m-%d}"
        )
        overall_metrics = st.columns(4)
        for column, (label, field, unit) in zip(
            overall_metrics,
            [
                ("Days with data", "days_with_any_data", "days"),
                ("Total commute", "total_commuting_hours", "hours"),
                ("Estimated distance", "total_estimated_distance_km", "km"),
                (
                    "Recorded sleep",
                    "total_reconstructed_recorded_sleep_hours",
                    "hours",
                ),
            ],
        ):
            precision = 0 if unit == "days" else 1
            column.metric(
                label,
                (
                    f"{int(overall_row[field])} days"
                    if unit == "days"
                    else format_value(overall_row[field], unit, precision)
                ),
            )

    st.caption(
        "Personal identifiers and GPS diagnostic fields are hidden."
    )


def show_postgres_dashboard(records: pd.DataFrame) -> None:
    if records.empty:
        st.warning("No daily records were found in PostgreSQL.")
        return

    prepared = records.copy()
    prepared["date"] = pd.to_datetime(prepared["date"])
    prepared["free_time_hours"] = prepared["free_time_minutes"] / 60
    prepared["distance_km"] = prepared["distance_meters"] / 1000
    for field in ("sleep_minutes", "social_minutes", "work_minutes", "gym_minutes"):
        prepared[field.replace("_minutes", "_hours")] = prepared[field] / 60
    prepared["activity_duration_hours"] = (
        prepared["social_hours"] + prepared["work_hours"] + prepared["gym_hours"]
    )
    prepared = prepared.sort_values("date").reset_index(drop=True)

    st.caption("Data source: PostgreSQL")
    st.subheader("Daily summary")
    selected_date = st.selectbox(
        "Select a day",
        options=list(prepared["date"].dt.date.iloc[::-1]),
        format_func=lambda value: value.strftime("%A, %B %d, %Y"),
        key="postgres_day",
    )
    day = prepared.loc[prepared["date"].dt.date == selected_date].iloc[0]

    metrics = st.columns(4)
    for column, (label, field, unit, precision) in zip(
        metrics,
        [
            ("Free time", "free_time_hours", "hours", 1),
            ("Distance travelled", "distance_km", "km", 1),
            ("Activity duration", "activity_duration_hours", "hours", 1),
            ("Daily score", "score", "/100", 0),
        ],
    ):
        value = day[field]
        formatted = (
            f"{value:.0f}/100"
            if unit == "/100"
            else format_value(value, unit, precision)
        )
        column.metric(label, formatted)
    st.caption("The score is read from the database; it is not calculated here.")

    activity_metrics = st.columns(4)
    activities = []
    for column, (label, field) in zip(
        activity_metrics,
        [
            ("Sleep", "sleep_hours"),
            ("Social time", "social_hours"),
            ("Work", "work_hours"),
            ("Gym", "gym_hours"),
        ],
    ):
        column.metric(label, format_value(day[field], "hours"))
        activities.append((label, day[field]))

    activity_data = pd.DataFrame(activities, columns=["Activity", "Hours"])
    activity_chart = (
        alt.Chart(activity_data)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("Hours:Q", title="Hours"),
            y=alt.Y("Activity:N", title="", sort="-x"),
            color=alt.Color("Activity:N", legend=None),
            tooltip=["Activity:N", alt.Tooltip("Hours:Q", format=".1f")],
        )
    )
    st.altair_chart(activity_chart, width="stretch", theme="streamlit")

    st.subheader("Recent activity trend")
    trend_data = prepared[
        ["date", "sleep_hours", "social_hours", "work_hours", "gym_hours"]
    ].rename(
        columns={
            "sleep_hours": "Sleep",
            "social_hours": "Social time",
            "work_hours": "Work",
            "gym_hours": "Gym",
        }
        ).melt(id_vars="date", var_name="Activity", value_name="Hours")
    st.caption("Click a legend item to highlight an activity.")
    trend_chart = make_interactive_trend_chart(
        trend_data,
        "date",
        "Activity",
        "Date",
        "Hours",
    )
    if not trend_data.empty:
        st.altair_chart(trend_chart, width="stretch", theme="streamlit")

    with st.expander("Daily records"):
        st.dataframe(
            prepared[
                [
                    "date",
                    "free_time_hours",
                    "distance_km",
                    "sleep_hours",
                    "social_hours",
                    "work_hours",
                    "gym_hours",
                    "score",
                ]
            ].sort_values("date", ascending=False),
            hide_index=True,
            width="stretch",
        )


def main() -> None:
    st.set_page_config(page_title="Activity Dashboard", layout="wide")
    st.title("Activity Dashboard")

    local_files = {
        "daily": DATA_DIR / "daily_dashboard_summary.csv",
        "weekly": DATA_DIR / "weekly_dashboard_summary.csv",
        "overall": DATA_DIR / "overall_dashboard_summary.csv",
    }
    published_files = {
        "daily": PUBLISHED_DATA_DIR / "daily_dashboard_summary.csv",
        "weekly": PUBLISHED_DATA_DIR / "weekly_dashboard_summary.csv",
        "overall": PUBLISHED_DATA_DIR / "overall_dashboard_summary.csv",
    }
    with st.sidebar.expander("Upload CSV summaries", expanded=True):
        st.caption("Upload all three summary CSV files to use your own data.")
        daily_upload = st.file_uploader(
            "Daily summary CSV",
            type="csv",
            key="daily_summary_upload",
            max_upload_size=10,
        )
        weekly_upload = st.file_uploader(
            "Weekly summary CSV",
            type="csv",
            key="weekly_summary_upload",
            max_upload_size=10,
        )
        overall_upload = st.file_uploader(
            "Overall summary CSV",
            type="csv",
            key="overall_summary_upload",
            max_upload_size=10,
        )

    uploads = (daily_upload, weekly_upload, overall_upload)
    if any(upload is not None for upload in uploads):
        if not all(upload is not None for upload in uploads):
            st.warning("Upload all three summary CSV files to display the dashboard.")
            st.stop()
        assert daily_upload is not None
        assert weekly_upload is not None
        assert overall_upload is not None
        daily = read_uploaded_csv_file(
            daily_upload,
            "Daily summary",
            DAILY_REQUIRED_COLUMNS,
            ("date",),
        )
        weekly = read_uploaded_csv_file(
            weekly_upload,
            "Weekly summary",
            WEEKLY_REQUIRED_COLUMNS,
            ("week_start", "week_end"),
        )
        overall = read_uploaded_csv_file(
            overall_upload,
            "Overall summary",
            OVERALL_REQUIRED_COLUMNS,
            ("tracking_start_date", "tracking_end_date"),
        )
    else:
        default_files = (
            local_files
            if all(file_path.is_file() for file_path in local_files.values())
            else published_files
        )
        if not all(file_path.is_file() for file_path in default_files.values()):
            st.info("Upload the daily, weekly, and overall summary CSV files to begin.")
            st.stop()
        daily = read_csv_file(
            default_files["daily"],
            "Daily summary",
            DAILY_REQUIRED_COLUMNS,
            ("date",),
        )
        weekly = read_csv_file(
            default_files["weekly"],
            "Weekly summary",
            WEEKLY_REQUIRED_COLUMNS,
            ("week_start", "week_end"),
        )
        overall = read_csv_file(
            default_files["overall"],
            "Overall summary",
            OVERALL_REQUIRED_COLUMNS,
            ("tracking_start_date", "tracking_end_date"),
        )

    if len(overall) != 1:
        st.error("The overall summary file must contain exactly one row.")
        st.stop()

    show_csv_dashboard(daily.sort_values("date"), weekly, overall)


if __name__ == "__main__":
    main()
