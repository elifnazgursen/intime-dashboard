# InTime Activity Dashboard

A Streamlit dashboard for the provided daily, weekly, and overall activity
summary CSV files. Pandas prepares the data, and Altair renders the charts.

## Data files

- `daily_dashboard_summary.csv`
- `weekly_dashboard_summary.csv`
- `overall_dashboard_summary.csv`
- `daily_goals_satisfaction.csv` (optional)

Upload the three activity summaries in the **Upload CSV summaries** section in
the left sidebar to view a dataset. Each file must contain the required columns
for its daily, weekly, or overall summary. The optional daily goals and
satisfaction summary can also be uploaded; it must use the same columns as
`public_data/daily_goals_satisfaction.csv`. If no summary files are uploaded,
the dashboard reads the matching files from local `data/` when all three are
available; otherwise it uses the published summaries in `public_data/`. Partial
summary uploads are not combined with default files; all three are required as
a set. Each upload is limited to 10 MB.

Daily goals and satisfaction are based only on unique manual survey responses.
Automatic survey records (including the automatic `99` satisfaction value) are
not counted. Days without a manual entry display **No data** and satisfaction as **Not
entered**. Sleep actual and target hours are shown side by side with a progress
indicator; the actual value is the one Aleks entered in the survey, not the
sensor-derived average sleep-session duration.

The daily activity trend uses Aleks-entered hobby hours and goal instead of the
separate recorded hobby estimate, alongside other recorded activity,
survey-entered activity and goal series, and satisfaction points. Hours use the
left axis and satisfaction points use a separate right axis.

The local CSV files are excluded by `.gitignore` because they may contain user
identifiers. Do not commit them or deploy them with the application source.
The application does not write uploaded CSV files to the repository or local
disk. They are processed by the hosting provider while the dashboard runs, so
review the provider's privacy terms before uploading personal data.

The Render deployment opens with the sanitized summary data in `public_data/`.
Those activity summaries are included in the public GitHub repository and are
visible to anyone who can access the dashboard. The source CSVs in `data/` stay
local and ignored; identifiers, timestamps, and GPS diagnostic fields are not
included in the published copies. The sanitized goal/satisfaction summaries
are also public so the hosted dashboard can display them.

## What the dashboard shows

- A selected day's commute duration, estimated distance, and average recorded
  sleep-session duration
- Daily study and eating durations, plus Aleks-entered hobby hours and goal
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
three CSV files in the sidebar or view the sanitized preloaded summary dataset.
The original CSV files in `data/` are not part of the repository or deployment.
