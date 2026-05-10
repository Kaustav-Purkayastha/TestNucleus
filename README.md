# TestNucleus

**Metadata-driven data quality validation framework for data engineering.**

Define your quality rules once in YAML. Run them against any database. Get structured reports. Fail your pipeline when data is bad.

---

## A Note on AI-Assisted Development

This project was built with GitHub Copilot / Claude used as a coding accelerator. The distinction matters — here is exactly where human expertise drove the work and where AI was used as a tool.

**Entirely mine (no AI involvement):**

- **The core concept.** The idea of separating *what to test* (metadata/config) from *how to test it* (the engine) came from seeing how brittle hardcoded data checks are in real pipelines. That architectural decision — making tests config-driven rather than code-driven — is the reason this project exists.
- **The real-world problem framing.** Every scenario in this README (ingestion validation, pre-dbt gates, migration reconciliation, data contracts, audit reporting) is drawn from actual pain points I have encountered or observed in data engineering workflows. AI does not know your pipelines broke silently — you do.
- **The choice of failure modes to cover.** Deciding which checks matter — NULL propagation, referential integrity after schema changes, format drift from third-party sources, value range violations in financial data — came from domain knowledge, not a prompt.
- **Technology selection decisions.** Choosing SQLAlchemy for multi-database support, YAML for human-readable config, and a CLI-first design so it integrates cleanly into Airflow/CI pipelines — these were deliberate engineering choices.

**Where AI was used:**

- Writing the Python implementation once the architecture was decided (validator functions, engine runner, CLI wiring, Pydantic models)
- Boilerplate that is mechanical to write but tedious — `__init__.py` exports, pytest fixtures, pyproject.toml packaging config
- The HTML report template (CSS layout)
- First draft of this README, edited for accuracy and framing

**The honest summary:** AI wrote code faster than I could type it. The thinking that determines whether that code is useful — what problem it solves, how it fits into real data engineering workflows, what the failure modes are — that came from experience. Code is the easy part.

---

## The Problem

Data pipelines break silently. A source system starts sending malformed emails, a nightly ETL loads negative revenue figures, a foreign key reference goes stale after a schema change — and none of it surfaces until a dashboard is wrong or a downstream model produces nonsense.

Traditional approaches are fragile: ad-hoc SQL scripts scattered across repos, one-off checks hardcoded into transformation logic, or nothing at all until a stakeholder notices. TestNucleus gives you a single, repeatable layer to validate data quality — before it moves downstream.

---

## Real-World Scenarios

### 1. Validating raw data on ingestion

Your pipeline ingests customer records from a third-party CRM via API every night. The source system has no enforced schema — fields arrive as strings, nulls appear without warning, and email formats are inconsistent.

**Without TestNucleus:** Bad records flow into your warehouse, silently corrupting downstream aggregations and marketing segments.

**With TestNucleus:**
```yaml
suite_name: "CRM Ingestion — Raw Layer"
connection: "postgresql://${PG_USER}:${PG_PASS}@${PG_HOST}/warehouse"

tests:
  - table: raw_customers
    field: customer_id
    checks:
      - type: not_null
      - type: unique

  - table: raw_customers
    field: email
    checks:
      - type: email_format
        nullable: true
      - type: completeness_rate
        params:
          threshold: 90.0

  - table: raw_customers
    field: created_at
    checks:
      - type: not_null
      - type: date_format
        params:
          format: "%Y-%m-%dT%H:%M:%S"
```

Run this after ingestion, before any transformation. If pass rate drops below threshold, the pipeline stops.

---

### 2. Pre-transformation checks in a dbt pipeline

You run dbt to transform staging data into fact and dimension tables. A bad source record can propagate through 5 layers of models before anyone notices.

**With TestNucleus** as a pre-dbt gate:
```yaml
suite_name: "Staging Layer — Pre-Transform Gate"
connection: "snowflake://${SF_USER}:${SF_PASS}@${SF_ACCOUNT}/ANALYTICS/STAGING"

tests:
  - table: stg_orders
    field: order_id
    checks:
      - type: not_null
      - type: unique

  - table: stg_orders
    field: total_amount
    checks:
      - type: not_null
      - type: min_value
        params:
          min: 0

  - table: stg_orders
    field: customer_id
    checks:
      - type: referential_integrity
        params:
          ref_table: stg_customers
          ref_field: customer_id
```

Wire it into your CI/CD or Airflow DAG:
```bash
testnucleus run configs/staging_gate.yaml --fail-under 100
# exits with code 1 if any check fails — stops the dbt run
```

---

### 3. Post-load reconciliation for data migrations

Your team is migrating a legacy Oracle system to PostgreSQL. After each batch load you need to verify the data arrived intact — row counts, nullability, referential integrity, value ranges.

```yaml
suite_name: "Migration Reconciliation — Batch 3"
connection: "postgresql://${PG_USER}:${PG_PASS}@${PG_HOST}/migrated_db"

tests:
  - table: accounts
    field: account_id
    checks:
      - type: not_null
      - type: unique

  - table: accounts
    field: status
    checks:
      - type: in_set
        params:
          values: ["ACTIVE", "CLOSED", "SUSPENDED", "PENDING"]

  - table: transactions
    field: amount
    checks:
      - type: not_null
      - type: between
        params:
          min: -1000000
          max: 1000000

  - table: transactions
    field: account_id
    checks:
      - type: referential_integrity
        params:
          ref_table: accounts
          ref_field: account_id
```

Run after every batch. The HTML report becomes your migration sign-off artifact.

---

### 4. Ongoing data contract enforcement

Your data team publishes tables consumed by analysts and ML engineers. You have a data contract — a promise about what those tables will contain. TestNucleus enforces it on a schedule.

```yaml
suite_name: "Data Contract — users_v2"
connection: "bigquery://${GCP_PROJECT}/analytics"

tests:
  - table: users_v2
    field: user_id
    checks:
      - type: not_null
      - type: unique

  - table: users_v2
    field: subscription_tier
    checks:
      - type: in_set
        params:
          values: ["free", "pro", "enterprise"]

  - table: users_v2
    field: signup_date
    checks:
      - type: not_null
      - type: date_format
        params:
          format: "%Y-%m-%d"

  - table: users_v2
    field: email
    checks:
      - type: not_null
      - type: email_format
      - type: completeness_rate
        params:
          threshold: 99.5
```

Schedule this in Airflow, Prefect, or a cron job. If the contract is violated, downstream consumers are notified before they pull bad data.

---

### 5. Regulatory and audit reporting

Your organisation handles financial or health data with compliance requirements. You need documented evidence that data meets quality standards at a point in time.

Run with `--format all` to produce both a machine-readable JSON result and a human-readable HTML report:

```bash
testnucleus run configs/compliance_suite.yaml --format all --output reports/audit_2026_Q1.html
```

The HTML report is self-contained — no server needed, open it in any browser. The JSON output feeds into your compliance dashboards or gets archived alongside your pipeline run logs.

---

## Supported Checks

| Category | Check | What it validates |
|---|---|---|
| **Completeness** | `not_null` | No NULL values in the column |
| | `not_empty` | No NULL or blank string values |
| | `completeness_rate` | Non-null % meets a minimum threshold |
| **Uniqueness** | `unique` | All values in the column are distinct |
| | `duplicate_count` | Duplicate count within an allowed threshold |
| **Conformity** | `email_format` | Values match a valid email pattern |
| | `phone_format` | Values match a valid phone number pattern |
| | `url_format` | Values match a valid URL pattern |
| | `regex_match` | Values match a custom regular expression |
| | `max_length` | String length does not exceed a maximum |
| | `min_length` | String length meets a minimum |
| | `no_trailing_spaces` | No leading or trailing whitespace |
| **Validity** | `min_value` | Numeric values are above a minimum |
| | `max_value` | Numeric values are below a maximum |
| | `between` | Numeric values fall within a range |
| | `not_negative` | Numeric values are >= 0 |
| | `date_format` | Dates match the expected format string |
| | `in_set` | Values belong to an allowed set |
| **Consistency** | `referential_integrity` | All foreign key values exist in the referenced table |
| | `no_cross_table_duplicates` | No overlapping values between two tables |

---

## Supported Databases

TestNucleus uses SQLAlchemy — any database SQLAlchemy supports works out of the box.

| Database | Connection string format | Extra install |
|---|---|---|
| SQLite | `sqlite:///./path/to/file.db` | — |
| PostgreSQL | `postgresql://user:pass@host/db` | `pip install -e ".[postgres]"` |
| MySQL | `mysql+pymysql://user:pass@host/db` | `pip install -e ".[mysql]"` |
| Snowflake | `snowflake://user:pass@account/db/schema?warehouse=wh` | `pip install snowflake-sqlalchemy` |
| BigQuery | `bigquery://project/dataset` | `pip install sqlalchemy-bigquery` |
| MS SQL Server | `mssql+pyodbc://user:pass@dsn` | `pip install pyodbc` |

Store credentials in `.env` and reference them in your YAML with `${VAR_NAME}` — they are never hardcoded in config files.

---

## Installation

```bash
git clone https://github.com/Kaustav-Purkayastha/TestNucleus.git
cd TestNucleus

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -e .
# or without building the package:
# pip install -r requirements.txt
```

Verify:
```bash
testnucleus --version
testnucleus list-checks
```

---

## Quick Start

```bash
# 1. Seed the sample database
python data/seed.py

# 2. Run the example suite (console output)
testnucleus run configs/example_suite.yaml

# 3. Generate HTML + JSON reports
testnucleus run configs/example_suite.yaml --format all

# 4. Open the report
# Windows
Start-Process reports\E-commerce_Data_Quality_Suite.html
# macOS / Linux
open reports/E-commerce_Data_Quality_Suite.html
```

---

## CLI Reference

```
testnucleus run <config>              Run all checks in a suite
  --format  console|json|html|all    Output format (default: console)
  --output  <path>                   Custom output file path
  --fail-under <float>               Exit code 1 if pass rate < threshold

testnucleus validate <config>        Validate config syntax without running
testnucleus list-checks              Show all available check types
testnucleus --version                Print version
```

**Exit codes:** `0` success · `1` pass rate below `--fail-under` · `2` config or connection error

---

## Writing a Suite Config

```yaml
suite_name: "My Suite"
description: "Optional description"
connection: "postgresql://${DB_USER}:${DB_PASS}@localhost/mydb"

tests:
  - table: orders
    field: status
    checks:
      - type: not_null
      - type: in_set
        params:
          values: ["pending", "shipped", "delivered", "cancelled"]

  - table: orders
    field: customer_email
    checks:
      - type: email_format
        nullable: true    # skip NULL rows for this specific check
      - type: completeness_rate
        params:
          threshold: 95.0
```

Set `nullable: true` on any check to skip rows where that field is NULL, rather than counting them as failures. This is useful for optional fields where you still want to validate the non-null values.

---

## Pipeline Integration

**Airflow:**
```python
from airflow.operators.bash import BashOperator

quality_gate = BashOperator(
    task_id="data_quality_check",
    bash_command="testnucleus run /opt/configs/suite.yaml --format json --fail-under 95",
)

ingest >> quality_gate >> transform
```

**GitHub Actions:**
```yaml
- name: Data quality gate
  run: |
    pip install -e .
    testnucleus run configs/suite.yaml --fail-under 100
```

---

## Project Structure

```
TestNucleus/
├── src/testnucleus/
│   ├── cli.py                   # Click CLI entry point
│   ├── connectors/sql.py        # SQLAlchemy engine + env var resolution
│   ├── engine/runner.py         # Suite execution engine
│   ├── models/
│   │   ├── config.py            # Pydantic models for YAML config
│   │   └── results.py           # Pydantic models for check results
│   ├── reporting/
│   │   ├── console.py           # Rich terminal output
│   │   └── exporters.py         # JSON and HTML report generation
│   └── validators/
│       ├── completeness.py
│       ├── conformity.py
│       ├── consistency.py
│       ├── uniqueness.py
│       └── validity.py
├── configs/                     # Your YAML test suites
├── data/seed.py                 # Sample database seeder
├── reports/                     # Generated reports (git-ignored)
└── tests/                       # pytest suite — 14 tests
```

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

---

## License

This project is licensed under the [MIT License](LICENSE).
