# Skills Required and Build Checklist

## Skills

| Skill | Applied to |
|---|---|
| Data modelling and SQL | PK/FK, `CHECK` constraints, join view, `COUNT DISTINCT`, `FILTER`, `generate_series` |
| ETL | Idempotent pandas loader, type coercion, transactions |
| Backend (FastAPI) | Validated query params, parameterised SQL, JSON contract |
| Frontend | KPI cards, Chart.js charts, filter bar, INR formatting, loading/empty/error states, responsive layout |
| Visual design | Clear hierarchy, consistent palette, accessible contrast |
| Testing (pytest) | DB, SQL, API tests with a pandas oracle |
| DevOps and docs | Docker Compose, README with assumptions |

## Build order

1. `db/schema.sql` and `db/view.sql`
2. `backend/load_data.py`, then verify DB-1 to DB-5
3. `tests/` skeleton with the expected values from `03_TEST_CASES.md`
4. `backend/queries.py` and `main.py`, then verify M-* and F-* tests
5. Frontend: layout, KPIs, charts, filters
6. Bonus items and Docker
7. README, screenshots, final test run

## Definition of done

- [ ] All tests in `03_TEST_CASES.md` pass
- [ ] KPIs match the ground-truth table
- [ ] 5 filters work together and reset cleanly
- [ ] `docker-compose up` brings up everything from scratch
- [ ] README lists setup steps, tools, assumptions
