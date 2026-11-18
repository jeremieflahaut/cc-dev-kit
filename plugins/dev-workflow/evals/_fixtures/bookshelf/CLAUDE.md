# Bookshelf

Small order-pricing service.

## Conventions

- Money amounts are integers in cents. Never produce a fractional amount: round explicitly.
- Date range parameters are named `date_start` and `date_end`, everywhere.
- Errors from the HTTP client must propagate to the caller. Never swallow them in a `catch`.
