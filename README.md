# InTime Activity Dashboard

A Streamlit dashboard for the provided daily, weekly, and overall activity
summary CSV files. Pandas prepares the data, and Altair renders the charts.

## Data files

- `daily_dashboard_summary.csv`
- `weekly_dashboard_summary.csv`
- `overall_dashboard_summary.csv`

Upload all three files in the **Upload CSV summaries** section in the left
sidebar to view a dataset. Each file must contain the required columns for its
daily, weekly, or overall summary. If no files are uploaded, the dashboard
reads the matching files from the local `data/` folder when available. Partial
uploads are not combined with local files; all three uploads are required as a
set. Each file is limited to 10 MB.

The local CSV files are excluded by `.gitignore` because they may contain user
identifiers. Do not commit them or deploy them with the application source.
The application does not write uploaded CSV files to the repository or local
disk. They are processed by the hosting provider while the dashboard runs, so
review the provider's privacy terms before uploading personal data.

## What the dashboard shows

- A selected day's commute duration, estimated distance, and average recorded
  sleep-session duration
- Daily study, hobby, and eating durations
- Daily and weekly trends with clickable chart legends
- A compact full-period summary

The selected-day activity comparison is a horizontal bar chart. Daily and
weekly trends are line charts, with dates on the horizontal axis and hours on
the vertical axis. Click a legend item to highlight that series; the other
lines fade into the background. The chart data is reshaped with Pandas before
Altair encodes the axes, colors, and tooltips.

The sleep value in these files is an average recorded session, not a daily
total. Installation identifiers and GPS diagnostic fields are hidden.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints the local URL, usually <http://localhost:8501>.

## Deploy on Render

The repository includes a Render Blueprint in `render.yaml`. Create a new
Blueprint on Render and connect the public GitHub repository
`elifnazgursen/intime-dashboard`. Render will build and start the Streamlit app
from this configuration. The deployed URL is public; visitors upload their own
three CSV files in the sidebar. The local user CSVs are not part of the
repository or deployment.
