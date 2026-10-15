CREATE TABLE daily_summaries (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recorded_on DATE NOT NULL UNIQUE,
    total_free_time_minutes INTEGER NOT NULL CHECK (total_free_time_minutes >= 0),
    distance_travelled_meters INTEGER NOT NULL CHECK (distance_travelled_meters >= 0),
    score SMALLINT NOT NULL CHECK (score BETWEEN 0 AND 100)
);

CREATE TABLE activity_types (
    id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE activity_durations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    daily_summary_id BIGINT NOT NULL
        REFERENCES daily_summaries (id) ON DELETE CASCADE,
    activity_type_id SMALLINT NOT NULL
        REFERENCES activity_types (id),
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes >= 0),
    UNIQUE (daily_summary_id, activity_type_id)
);

INSERT INTO activity_types (name)
VALUES ('sleep'), ('social'), ('work'), ('gym')
ON CONFLICT (name) DO NOTHING;
