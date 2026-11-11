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
    "total_eating_hours",
}
GOAL_SATISFACTION_REQUIRED_COLUMNS = {
    "date",
    "goal_entered",
    "satisfaction_points",
    "sleep_actual_hours",
    "sleep_target_hours",
    "study_actual_hours",
    "study_target_hours",
    "sports_actual_hours",
    "sports_target_hours",
    "hobby_actual_hours",
    "hobby_target_hours",
}

CSV_ACTIVITY_COLUMNS = {
    "Commuting": "commuting_hours",
    "Average sleep session": "average_recorded_sleep_session_hours",
    "Study": "study_hours",
    "Eating": "eating_hours",
}
GOAL_ACTIVITY_COLUMNS = {
    "Sleep": ("sleep_actual_hours", "sleep_target_hours"),
    "Study": ("study_actual_hours", "study_target_hours"),
    "Sports": ("sports_actual_hours", "sports_target_hours"),
    "Hobby entered": ("hobby_actual_hours", "hobby_target_hours"),
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


def read_goal_satisfaction_csv(
    file_path: Path | None = None,
    uploaded_file: IO[bytes] | None = None,
) -> pd.DataFrame:
    if uploaded_file is not None:
        goal_data = read_uploaded_csv_file(
            uploaded_file,
            "Daily goals and satisfaction",
            GOAL_SATISFACTION_REQUIRED_COLUMNS,
            ("date",),
        )
    elif file_path is not None:
        goal_data = read_csv_file(
            file_path,
            "Daily goals and satisfaction",
            GOAL_SATISFACTION_REQUIRED_COLUMNS,
            ("date",),
        )
    else:
        return pd.DataFrame(
            {
                column: pd.Series(dtype="object")
                for column in GOAL_SATISFACTION_REQUIRED_COLUMNS
            }
        ).assign(
            date=pd.Series(dtype="datetime64[ns]"),
            goal_entered=pd.Series(dtype="bool"),
        )

    goal_status = (
        goal_data["goal_entered"]
        .astype("string")
        .str.strip()
        .str.casefold()
        .map({"true": True, "false": False})
    )
    if goal_status.isna().any():
        st.error("Daily goals and satisfaction contains an invalid goal_entered value.")
        st.stop()
    goal_data["goal_entered"] = goal_status

    numeric_columns = GOAL_SATISFACTION_REQUIRED_COLUMNS - {
        "date",
        "goal_entered",
    }
    for column in numeric_columns:
        original_values = goal_data[column]
        numeric_values = pd.to_numeric(original_values, errors="coerce")
        if (original_values.notna() & numeric_values.isna()).any():
            st.error(
                f"Daily goals and satisfaction contains a non-numeric value "
                f"in '{column}'."
            )
            st.stop()
        goal_data[column] = numeric_values

    return goal_data


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


def make_daily_activity_trend_chart(data: pd.DataFrame) -> alt.LayerChart:
    series_names = sorted(data["Series"].dropna().unique().tolist())
    legend_selection = alt.selection_point(
        fields=["Series"],
        bind="legend",
        toggle="true",
    )
    base = alt.Chart(data).encode(
        x=alt.X(
            "date:T",
            title="Date",
            axis=alt.Axis(format="%b %d", labelAngle=0),
        ),
        color=alt.Color(
            "Series:N",
            title="Click legend items to highlight",
            scale=alt.Scale(domain=series_names),
            legend=alt.Legend(orient="right"),
        ),
        opacity=alt.condition(
            legend_selection,
            alt.value(1),
            alt.value(0.12),
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("Series:N", title="Measure"),
            alt.Tooltip("Value:Q", format=".2f"),
            alt.Tooltip("Unit:N", title="Unit"),
        ],
    )
    hours_chart = base.transform_filter(
        alt.datum.Unit == "hours"
    ).mark_line(point=True).encode(
        y=alt.Y("Value:Q", title="Hours", axis=alt.Axis(orient="left"))
    )
    points_chart = base.transform_filter(
        alt.datum.Unit == "points"
    ).mark_line(point=True).encode(
        y=alt.Y(
            "Value:Q",
            title="Satisfaction points",
            axis=alt.Axis(orient="right"),
            scale=alt.Scale(zero=False),
        )
    )
    return (
        alt.layer(hours_chart, points_chart)
        .resolve_scale(y="independent")
        .add_params(legend_selection)
    )


def show_csv_dashboard(
    daily: pd.DataFrame,
    weekly: pd.DataFrame,
    overall: pd.DataFrame,
    goal_satisfaction: pd.DataFrame,
) -> None:
    overall_row = overall.iloc[0]

    st.subheader("Daily summary")
    available_dates = set(daily["date"].dt.date)
    if not goal_satisfaction.empty:
        available_dates.update(goal_satisfaction["date"].dt.date)
    selected_date = st.selectbox(
        "Select a day",
        options=sorted(available_dates, reverse=True),
        format_func=lambda value: value.strftime("%A, %B %d, %Y"),
    )
    selected_day = daily.loc[daily["date"].dt.date == selected_date]
    day = (
        selected_day.iloc[0]
        if not selected_day.empty
        else pd.Series(dtype="object")
    )
    selected_goal = goal_satisfaction.loc[
        goal_satisfaction["date"].dt.date == selected_date
    ]
    goal = (
        selected_goal.iloc[0]
        if not selected_goal.empty and bool(selected_goal.iloc[0]["goal_entered"])
        else pd.Series(dtype="object")
    )

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
        column.metric(label, format_value(day.get(field, pd.NA), unit, precision))

    st.caption(
        "Sleep is shown as the average recorded session, not a daily total."
    )

    other_metrics = st.columns(3)
    for column, (label, field) in zip(
        other_metrics,
        [
            ("Study", "study_hours"),
            ("Hobby entered", "hobby_actual_hours"),
            ("Eating", "eating_hours"),
        ],
    ):
        value = (
            goal.get(field, pd.NA)
            if label == "Hobby entered"
            else day.get(field, pd.NA)
        )
        column.metric(label, format_value(value, "hours"))

    st.subheader("Daily goals and satisfaction")
    if goal.empty:
        st.write("No data")
        st.metric("Satisfaction points", "Not entered")
    else:
        sleep_actual = goal["sleep_actual_hours"]
        sleep_target = goal["sleep_target_hours"]

        sleep_metrics = st.columns(3)
        sleep_metrics[0].metric(
            "Sleep entered for the day",
            format_value(sleep_actual, "hours"),
        )
        sleep_metrics[1].metric(
            "Sleep goal",
            format_value(sleep_target, "hours"),
        )
        sleep_metrics[2].metric(
            "Satisfaction points",
            (
                f"{format_value(goal['satisfaction_points'], precision=0)} pts"
                if pd.notna(goal["satisfaction_points"])
                else "Not entered"
            ),
        )

        if pd.notna(sleep_actual) and pd.notna(sleep_target) and sleep_target > 0:
            progress = min(max(float(sleep_actual) / float(sleep_target), 0.0), 1.0)
            st.progress(progress, text="Sleep goal progress")
            if sleep_actual >= sleep_target:
                st.success(
                    f"Sleep goal reached ({format_value(sleep_actual, 'hours')} "
                    f"of {format_value(sleep_target, 'hours')})."
                )
            else:
                st.info(
                    f"{format_value(sleep_target - sleep_actual, 'hours')} "
                    "below the sleep goal."
                )
        else:
            st.info("No sleep goal was entered for this day.")

        comparison_rows = []
        for activity, (actual_field, target_field) in GOAL_ACTIVITY_COLUMNS.items():
            actual = goal[actual_field]
            target = goal[target_field]
            if pd.isna(target) or target <= 0:
                status = "No goal"
            elif pd.isna(actual):
                status = "No actual value"
            else:
                status = (
                    "Goal reached"
                    if actual >= target
                    else "Below goal"
                )
            comparison_rows.append(
                {
                    "Activity": activity,
                    "Actual (hours)": actual,
                    "Goal (hours)": target,
                    "Status": status,
                }
            )
        st.dataframe(
            pd.DataFrame(comparison_rows),
            hide_index=True,
            width="stretch",
        )

    st.subheader("Selected day's activity durations")
    st.caption(
        "Hobby entered is from Aleks's manual survey response. Sleep is an "
        "average session; other recorded activity bars show daily totals."
    )
    selected_activity_values = [
        (label, day.get(field, pd.NA))
        for label, field in CSV_ACTIVITY_COLUMNS.items()
    ]
    selected_activity_values.append(
        ("Hobby entered", goal.get("hobby_actual_hours", pd.NA))
    )
    activity_chart_data = pd.DataFrame(
        selected_activity_values,
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
            f"{format_value(day.get('completed_commute_sessions', pd.NA))}"
        )
        st.write(
            f"Recorded sleep sessions: "
            f"{format_value(day.get('completed_sleep_sessions', pd.NA))}"
        )

    st.divider()
    st.subheader("Activity trends")
    daily_tab, weekly_tab = st.tabs(["Daily trend", "Weekly overview"])
    with daily_tab:
        activity_trend = daily[["date", *CSV_ACTIVITY_COLUMNS.values()]].rename(
            columns={field: label for label, field in CSV_ACTIVITY_COLUMNS.items()}
        ).melt(
            id_vars="date",
            var_name="Series",
            value_name="Value",
        ).dropna()
        activity_trend["Unit"] = "hours"
        trend_parts = [activity_trend]

        entered_goals = goal_satisfaction.loc[goal_satisfaction["goal_entered"]]
        if not entered_goals.empty:
            goal_series = []
            for activity, (actual_field, target_field) in GOAL_ACTIVITY_COLUMNS.items():
                activity_name = activity.removesuffix(" entered")
                goal_series.append(
                    entered_goals[["date", actual_field, target_field]].rename(
                        columns={
                            actual_field: (
                                activity
                                if activity.endswith(" entered")
                                else f"{activity} entered"
                            ),
                            target_field: f"{activity_name} goal",
                        }
                    ).melt(
                        id_vars="date",
                        var_name="Series",
                        value_name="Value",
                    )
                )
            goals_trend = pd.concat(goal_series, ignore_index=True).dropna()
            goals_trend["Unit"] = "hours"
            trend_parts.append(goals_trend)

            satisfaction_trend = entered_goals[
                ["date", "satisfaction_points"]
            ].rename(
                columns={"satisfaction_points": "Value"}
            )
            satisfaction_trend["Series"] = "Satisfaction points"
            satisfaction_trend["Unit"] = "points"
            trend_parts.append(satisfaction_trend.dropna(subset=["Value"]))

        trend_data = pd.concat(trend_parts, ignore_index=True)
        if trend_data.empty:
            st.info("There is not enough data to show a daily trend.")
        else:
            st.caption(
                "Click one or more legend items to highlight a series. "
                "Hours use the left axis; satisfaction points use the right axis."
            )
            trend_chart = make_daily_activity_trend_chart(trend_data)
            st.altair_chart(trend_chart, width="stretch", theme="streamlit")

        daily_table = daily[
            [
                "date",
                "commuting_hours",
                "estimated_distance_km",
                "average_recorded_sleep_session_hours",
                "study_hours",
                "eating_hours",
            ]
        ].rename(
            columns={
                "date": "Date",
                "commuting_hours": "Commute (hours)",
                "estimated_distance_km": "Estimated distance (km)",
                "average_recorded_sleep_session_hours": "Avg. sleep session (hours)",
                "study_hours": "Study (hours)",
                "eating_hours": "Eating (hours)",
            }
        )
        hobby_by_date = goal_satisfaction.loc[
            goal_satisfaction["goal_entered"]
        ].set_index(goal_satisfaction.loc[goal_satisfaction["goal_entered"], "date"].dt.date)[
            "hobby_actual_hours"
        ]
        daily_table["Hobby entered (hours)"] = daily["date"].dt.date.map(
            hobby_by_date
        ).to_numpy()
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
        manual_hobby = goal_satisfaction.loc[
            goal_satisfaction["goal_entered"]
            & goal_satisfaction["hobby_actual_hours"].notna()
        ]
        weekly_hobby_rows = []
        for _, week in weekly.iterrows():
            week_start = week["week_start"].date()
            week_end = week["week_end"].date()
            week_values = manual_hobby.loc[
                manual_hobby["date"].dt.date.between(week_start, week_end),
                "hobby_actual_hours",
            ]
            weekly_hobby_rows.append(
                {
                    "Week": week["week_start"],
                    "Measure": "Avg. daily hobby entered",
                    "Hours": week_values.mean() if not week_values.empty else pd.NA,
                }
            )
        weekly_hobby_trend = pd.DataFrame(weekly_hobby_rows).dropna()
        if not weekly_hobby_trend.empty:
            weekly_trend = pd.concat(
                [weekly_trend, weekly_hobby_trend],
                ignore_index=True,
            )
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
                "average_daily_eating_hours": "Avg. daily eating (hours)",
            }
        )
        weekly_table["Avg. daily hobby entered (hours)"] = [
            row["Hours"] for row in weekly_hobby_rows
        ]
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
        tracking_start = pd.to_datetime(overall_row["tracking_start_date"])
        tracking_end = pd.to_datetime(overall_row["tracking_end_date"])
        period_hobby = goal_satisfaction.loc[
            goal_satisfaction["goal_entered"]
            & goal_satisfaction["date"].between(tracking_start, tracking_end),
            "hobby_actual_hours",
        ].dropna()
        total_hobby_entered = (
            period_hobby.sum() if not period_hobby.empty else pd.NA
        )
        overall_metrics = st.columns(5)
        for column, (label, value, unit) in zip(
            overall_metrics,
            [
                ("Days with data", overall_row["days_with_any_data"], "days"),
                ("Total commute", overall_row["total_commuting_hours"], "hours"),
                ("Estimated distance", overall_row["total_estimated_distance_km"], "km"),
                (
                    "Recorded sleep",
                    overall_row["total_reconstructed_recorded_sleep_hours"],
                    "hours",
                ),
                ("Total hobby entered", total_hobby_entered, "hours"),
            ],
        ):
            precision = 0 if unit == "days" else 1
            column.metric(
                label,
                (
                    f"{int(value)} days"
                    if unit == "days"
                    else format_value(value, unit, precision)
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
    local_goal_satisfaction_file = DATA_DIR / "daily_goals_satisfaction.csv"
    published_goal_satisfaction_file = (
        PUBLISHED_DATA_DIR / "daily_goals_satisfaction.csv"
    )
    with st.sidebar.expander("Upload CSV summaries", expanded=True):
        st.caption(
            "Upload all three summary CSV files to use your own data. "
            "Daily goals and satisfaction are optional."
        )
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
        goal_satisfaction_upload = st.file_uploader(
            "Daily goals and satisfaction CSV (optional)",
            type="csv",
            key="goal_satisfaction_upload",
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
        goal_satisfaction = read_goal_satisfaction_csv(
            uploaded_file=goal_satisfaction_upload,
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
        if goal_satisfaction_upload is not None:
            goal_satisfaction = read_goal_satisfaction_csv(
                uploaded_file=goal_satisfaction_upload,
            )
        else:
            default_goal_file = (
                local_goal_satisfaction_file
                if local_goal_satisfaction_file.is_file()
                else published_goal_satisfaction_file
            )
            goal_satisfaction = read_goal_satisfaction_csv(
                file_path=default_goal_file
                if default_goal_file.is_file()
                else None
            )

    if len(overall) != 1:
        st.error("The overall summary file must contain exactly one row.")
        st.stop()

    show_csv_dashboard(
        daily.sort_values("date"),
        weekly,
        overall,
        goal_satisfaction,
    )


if __name__ == "__main__":
    main()
