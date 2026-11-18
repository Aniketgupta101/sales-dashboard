# Test Cases

Approach: pandas computes the expected value independently from the Excel files. SQL and API results must match it.

## Database

| ID | Test | Expected |
|---|---|---|
| DB-1 | Row counts after load | 60 customers, 240 orders |
| DB-2 | Run loader twice | Still 60 and 240 |
| DB-3 | Insert order with unknown `Customer_ID` | FK violation |
| DB-4 | Duplicate PK; status "Shipped"; discount 1.5; quantity 0 | Each rejected |
| DB-5 | Column types | Dates are `DATE`, amounts numeric, quantity int |

## SQL view

| ID | Test | Expected |
|---|---|---|
| SQL-1 | `COUNT(*)` of `vw_sales` | 240 (no join fan-out) |
| SQL-2 | Revenue sum, view vs orders table | 1,159,206 on both |
| SQL-3 | Cancelled rows | All have net amount 0 |

## Metrics (no filters)

| ID | Test | Expected |
|---|---|---|
| M-1 | Total orders | 240 |
| M-2 | Unique customers | 59 |
| M-3 | AOV | 5,682.38 |
| M-4 | Revenue by category | Electronics 532,772; Accessories 248,730; Lifestyle 192,597; Office 185,107 |
| M-5 | Monthly series | 6 months; Jan 231,812; Feb 157,676; Mar 225,820; Apr 160,162; May 139,176; Jun 244,560 |
| M-6 | Revenue by segment | Consumer 473,590; Corporate 446,560; Small Business 239,056 |
| M-7 | Orders by status | Completed 164; Returned 40; Cancelled 36 |
| M-8 | Top 5 products | Smart Watch 274,674; Bluetooth Speaker 182,337; USB-C Hub 116,754; Mechanical Keyboard 106,580; Laptop Stand 86,717 |
| M-9 | Repeat customers | 48 of 54 |

## Filters

| ID | Test | Expected |
|---|---|---|
| F-1 | Status = Returned | Revenue 198,890; orders 40; AOV 4,972.25 |
| F-2 | Status = Cancelled | Revenue 0; orders 36; AOV shows "-" (no crash) |
| F-3 | Category = Electronics | Revenue 532,772 |
| F-4 | Date 2026-01-01 to 2026-01-31 | Revenue 231,812; orders 44 |
| F-5 | Segment + city + category combined | Matches pandas |
| F-6 | Combination with zero rows | Empty-state message; KPIs show 0 |
| F-7 | Date boundaries | Start and end dates inclusive |
| F-8 | Monthly trend under a filter | Still shows all 6 months (zeros included) |

## API

| ID | Test | Expected |
|---|---|---|
| A-1 | Invalid date or unknown param | 422 error |
| A-2 | `category=' OR 1=1 --` | No effect, zero rows or 422 |
| A-3 | `GET /api/filters` | Lists all categories, segments, cities, statuses |

## UI

| ID | Test | Expected |
|---|---|---|
| UI-1 | Page load | KPIs populated; no console errors |
| UI-2 | Change any filter | All cards and charts update together |
| UI-3 | Reset filters | Back to baseline totals |
| UI-4 | Mobile width (about 380px) | No horizontal scroll |
| UI-5 | Slow or failed API | Loading and error state shown |
