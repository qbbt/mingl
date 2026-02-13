CREATE TABLE IF NOT EXISTS entities (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  entity_type TEXT NOT NULL,
  contributor_type TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NOT NULL,
  timestamp TEXT NOT NULL,
  value REAL NOT NULL,
  metric_name TEXT NOT NULL DEFAULT 'value',
  margin_of_error REAL NOT NULL DEFAULT 0,
  event_type TEXT NOT NULL DEFAULT 'observation',
  source_url TEXT NOT NULL DEFAULT '',
  extra_json TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY(entity_id) REFERENCES entities(id)
);

CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NOT NULL,
  timestamp TEXT NOT NULL,
  predicted_value REAL NOT NULL,
  lower_bound REAL NOT NULL,
  upper_bound REAL NOT NULL,
  confidence REAL NOT NULL,
  FOREIGN KEY(entity_id) REFERENCES entities(id)
);

CREATE TABLE IF NOT EXISTS correlations (
  id INTEGER PRIMARY KEY,
  entity_a_id INTEGER NOT NULL,
  entity_b_id INTEGER NOT NULL,
  correlation_value REAL NOT NULL,
  confidence REAL NOT NULL DEFAULT 0,
  window_seconds INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(entity_a_id) REFERENCES entities(id),
  FOREIGN KEY(entity_b_id) REFERENCES entities(id)
);

CREATE TABLE IF NOT EXISTS notification_outbox (
  id INTEGER PRIMARY KEY,
  channel TEXT NOT NULL DEFAULT 'email',
  recipient TEXT NOT NULL,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL
);
