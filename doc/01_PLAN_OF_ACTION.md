# Sales Dashboard Assignment: Plan of Action

## 1. Understanding the task

Load two Excel files (`customers.xlsx`, `orders.xlsx`) into a database, join them on `Customer_ID`, and build a filterable sales dashboard on top.

| Area | Weight | What it means for us |
|---|---:|---|
| Data loading and table relationships | 25% | PK, FK, correct data types, idempotent loader |
| SQL join and metric accuracy | 25% | Join view and KPIs that match independent calculations |
| Dashboard clarity and required visuals | 25% | 4 KPIs and 4 charts |
| Filters and usability | 15% | At least 2 filters; we build 5 |
| Code organization and README | 10% | Clean repo and documented assumptions |

Bonus items: top-5 products, repeat-customer metric, Docker.

## 2. Data findings

- **Size:** 60 customers, 240 orders, Jan to Jun 2026.
- **Integrity:** no duplicate IDs, no orphan orders, no nulls. Non-cancelled `Net_Amount_INR` always equals qty x price x (1 - discount).
- **Cancelled orders:** all have net amount 0.
- **Statuses:** Completed 164, Returned 40, Cancelled 36.

### Traps

1. One customer has no orders. "Unique customers" is 59 or 60 depending on the join.
2. Returned orders count toward revenue (Rs 198,890). Show them separately by status.
3. AOV divides by non-cancelled orders (204), but "Total orders" counts all (240). These are different counts.

### Ground-truth KPIs

| Metric | Expected |
|---|---|
| Net revenue | 1,159,206 |
| Total orders | 240 (204 non-cancelled) |
| Unique customers | 59 |
| AOV | 5,682.38 |
| Top product | Smart Watch (274,674) |
| Repeat customers (2+ non-cancelled orders) | 48 of 54 |

## 3. Timeline (about 3.5 hours)

| Phase | Work | Time |
|---|---|---|
| 1 | Profile data, fix metric definitions | 15 min |
| 2 | `schema.sql`, view, loader script | 40 min |
| 3 | Write tests first (pandas as the oracle) | 30 min |
| 4 | FastAPI endpoint with filters | 40 min |
| 5 | Frontend: 4 KPIs, 4 charts, 5 filters, responsive | 60 min |
| 6 | Bonus: top-5 products, repeat customers, Docker | 20 min |
| 7 | README, screenshots | 15 min |

## 4. Assumptions (copy into the README)

- Revenue includes Returned orders; Cancelled contribute 0.
- "Total orders" counts all unique `Order_ID`s, any status.
- "Unique customers" counts distinct customers in the filtered orders.
- AOV = total net revenue / non-cancelled orders; shows "-" when that count is 0.
- All metrics respond to all filters.

## 5. Deliverables checklist

- [ ] Schema SQL
- [ ] Loader script and loading steps
- [ ] Join view SQL
- [ ] Working dashboard
- [ ] Tests
- [ ] `docker-compose.yml`
- [ ] README with setup, tools, assumptions
