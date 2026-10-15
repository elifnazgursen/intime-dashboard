# InTime Activity Dashboard

A beginner-friendly activity dashboard built with Python, Streamlit, pandas,
Altair, and PostgreSQL.

## Features

- Daily free time, distance travelled, activity duration, social time, and score
- Daily data table with grouping and sorting
- Sleep and social-life comparison chart
- PostgreSQL data loading, with sample data used when `DATABASE_URL` is unset

## Run locally

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies and start the dashboard:

   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

Streamlit prints the local URL, usually <http://localhost:8501>.

## PostgreSQL

1. Create a database and run [`database/schema.sql`](database/schema.sql).
2. Set the `DATABASE_URL` environment variable to your PostgreSQL connection
   string.
3. Run `streamlit run app.py` again.

Example format (replace the placeholders locally; do not commit credentials):

```text
postgresql://username:password@localhost:5432/database_name
```

Without `DATABASE_URL`, the dashboard uses the example records in
[`sample_data.py`](sample_data.py).
