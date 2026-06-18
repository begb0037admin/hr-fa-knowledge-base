# HOW TO — SQL Fundamentals for HR Reporting

**Category:** Reporting
**Applies to:** SQL Developer (Oracle PL/SQL), Visual Studio Report Datasets (TSQL)
**Audience:** HR Systems analysts new to SQL

---

## Overview

SQL (Structured Query Language) is used in two main places in HR Reporting:

- **SQL Developer** — for directly querying the PeopleXD Oracle database (read-only). Uses Oracle PL/SQL syntax.
- **Visual Studio .RDL files** — for writing report dataset queries. Uses TSQL (Transact-SQL, Microsoft syntax).

The two dialects are broadly similar. Once you know one, you can read the other. Key difference: if you Google an SQL problem, include "Oracle SQL" or "TSQL" in your search so you get the right syntax back.

**Important:** SQL Developer access to PeopleXD is read-only. You cannot break or change anything in the database by running queries.

---

## 1. Views, Tables, and Functions

In SQL Developer, when connected to PeopleXD, you will see:

- **Views** — pre-built query results. Always use these in preference to tables. The Access Group agreement is to pull data from views, not tables.
- **Tables** — the raw underlying data. Avoid unless you have a specific reason.
- **Functions** — used for pulling UDF information and salary data. You will encounter these in existing SQL queries.

To find a view, right-click and apply a filter. Use wildcards (e.g. `%pay%calendar%`) to search by keyword.

To see what SQL a view is built from, click the view and select the SQL button at the top.

---

## 2. The Basic SELECT Statement

The simplest SQL query has two parts:

```sql
SELECT column1, column2
FROM view_or_table_name
```

**Example — pull everyone's forename and surname:**
```sql
SELECT forename, surname
FROM PRBI_HR_PERSON_MASTER
```

Rules:
- List the columns you want, separated by commas
- `FROM` tells the query where to pull the data from
- SQL is not case-sensitive, but convention is to write keywords (SELECT, FROM, WHERE) in uppercase

---

## 3. Filtering with WHERE

Add a `WHERE` clause to restrict results:

```sql
SELECT column1, column2
FROM table_name
WHERE column1 = 'value'
```

**Example — active staff only:**
```sql
SELECT forename, surname
FROM PRBI_HR_PERSON_MASTER
WHERE employment_status = 'S'
```

### Common operators

| Operator | Meaning | Example |
|---|---|---|
| `=` | Equals | `WHERE status = 'S'` |
| `<>` or `!=` | Not equal | `WHERE status <> 'L'` |
| `>` / `<` | Greater / less than | `WHERE salary > 30000` |
| `IS NULL` | No value present | `WHERE end_date IS NULL` |
| `IS NOT NULL` | Value is present | `WHERE start_date IS NOT NULL` |
| `IN (...)` | Matches any value in a list | `WHERE pay_code IN (100, 121, 125)` |
| `NOT IN (...)` | Excludes values in a list | `WHERE pay_code NOT IN (999)` |
| `BETWEEN x AND y` | Within a range | `WHERE start_date BETWEEN '01-JAN-2024' AND '31-DEC-2024'` |
| `LIKE '%value%'` | Contains text (wildcard) | `WHERE surname LIKE '%ton'` |
| `NOT LIKE` | Does not contain text | `WHERE dept NOT LIKE '%test%'` |

### Wildcards (used with LIKE)
- `%` — replaces any number of characters
- `%ton` — anything ending in "ton"
- `ton%` — anything starting with "ton"
- `%ton%` — anything containing "ton" anywhere

### Combining conditions
Use `AND`, `OR`, `NOT` to combine multiple filters:

```sql
WHERE employment_status = 'S'
AND surname LIKE '%ton'
```

---

## 4. The IN List — Adding a Pay Code

The `IN` operator checks whether a column's value matches any value in a list. This is how pay code filters work in HR reports.

**Numeric values — no quotes needed:**
```sql
WHERE pay_code IN (100, 105, 110, 115, 120, 125)
```

**String values — single quotes required:**
```sql
WHERE department IN ('Finance', 'HR', 'IT')
```

**To add a new pay code to an existing filter**, find the `IN` list and insert the number in sequential order:

```sql
-- Before:
WHERE pay_code IN (100, 105, 110, 115, 120, 125)

-- After adding pay code 121:
WHERE pay_code IN (100, 105, 110, 115, 120, 121, 125)
```

Keeping the list sequential is not required by SQL, but is best practice so future maintainers can find and modify values easily.

---

## 5. Sorting Results with ORDER BY

Add `ORDER BY` at the end of your query to sort results:

```sql
SELECT forename, surname
FROM PRBI_HR_PERSON_MASTER
WHERE employment_status = 'S'
ORDER BY surname
```

- `ORDER BY surname` — ascending (A to Z) by default
- `ORDER BY surname DESC` — descending (Z to A)
- `ORDER BY salary DESC` — highest salary first

---

## 6. Aggregation and GROUP BY

Use aggregation functions to produce summary data:

| Function | What it does |
|---|---|
| `COUNT(column)` | Counts the number of rows |
| `SUM(column)` | Adds up numeric values |
| `MAX(column)` | Returns the highest value |
| `MIN(column)` | Returns the lowest value |

When using aggregation, all non-aggregated columns must appear in a `GROUP BY` clause:

```sql
SELECT pay_group, surname, COUNT(person_reference) AS number_of_staff
FROM PRBI_HR_PERSON_MASTER
WHERE employment_status = 'S'
GROUP BY pay_group, surname
ORDER BY COUNT(person_reference) DESC
```

### Aliasing columns
Use `AS` to give a column or function a readable name:
```sql
COUNT(person_reference) AS number_of_staff
```

### HAVING
`HAVING` filters results after aggregation has been applied (unlike `WHERE`, which filters before):

```sql
GROUP BY pay_group, surname
HAVING surname = 'Morton'
```

---

## 7. Joining Tables

Joins combine data from two or more tables or views. The three most common types are:

### INNER JOIN
Returns only rows where there is a match in both tables.

```sql
SELECT pm.forename, pm.surname, ah.appointment_id
FROM PRBI_HR_PERSON_MASTER pm
INNER JOIN APPOINTMENT_HISTORY ah ON pm.person_reference = ah.person_reference
WHERE pm.employment_status = 'S'
```

### LEFT JOIN
Returns all rows from the first (left) table, with matched data from the second table where available. Non-matching rows show NULL for the second table's columns.

Use this when you know not everyone will have a record in the second table — for example, joining to diversity data (not everyone has diversity information recorded).

```sql
SELECT pm.forename, pm.surname, div.ethnicity
FROM PRBI_HR_PERSON_MASTER pm
LEFT JOIN DIVERSITY_DATA div ON pm.person_reference = div.person_reference
WHERE pm.employment_status = 'S'
```

### FULL OUTER JOIN
Returns all rows from both tables, matching where possible and showing NULLs where there is no match.

### Key points on joins
- When joining tables, prefix column names with the table name to avoid ambiguity: `pm.forename`, `ah.appointment_id`
- You can chain multiple joins, but be careful — each join can multiply or reduce your result set
- You can add extra conditions to a join using `AND`: `ON pm.person_reference = ah.person_reference AND ah.status = 'C'`

---

## 8. Commenting Out Code

Use two dashes (`--`) to comment out a line. SQL will ignore anything after `--` on that line.

```sql
SELECT forename, surname
FROM PRBI_HR_PERSON_MASTER
WHERE employment_status = 'S'
-- AND surname LIKE '%ton'   <-- this line is ignored
```

This is useful for:
- Temporarily removing a condition without deleting it
- Adding notes to explain what a line of code does

---

## 9. Diagnosing Errors

- A **pink wiggly underline** in SQL Developer indicates a syntax error
- A **pink bar on the right side** of the screen marks where the error is — click it to jump to the problem line
- Enable **line numbers** by right-clicking the editor and selecting "Toggle Line Numbers" — essential for navigating long queries
- Common causes: missing comma, missing closing bracket, missing operator between WHERE conditions

---

## 10. Exporting Results

In SQL Developer, right-click the query results and select **Export**. Use **CSV** format — Excel export can behave unpredictably (e.g. only exporting the highlighted row).

---

## Quick Reference

```sql
SELECT column1, column2           -- columns to return
FROM view_name                    -- where to pull from
WHERE column1 = 'value'           -- filter conditions
AND column2 IN (100, 121, 125)    -- list filter
ORDER BY column1 ASC              -- sort (ASC = A-Z, DESC = Z-A)
```

```sql
SELECT column1, COUNT(column2) AS total
FROM view_name
WHERE column1 IS NOT NULL
GROUP BY column1
HAVING COUNT(column2) > 5
ORDER BY total DESC
```

---

*Source: SQL Training session, HR Systems team. Delivered by Simon and Athena.*
*Added to KB: 18 June 2026*
