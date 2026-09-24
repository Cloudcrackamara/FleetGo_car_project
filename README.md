```markdown
# FleetGo — Car Rental Fleet API

Backend for a car-rental fleet management platform. Customers reserve cars, agents record pickups and returns, and managers keep the fleet, pricing and workshop status under control. Team **Fire Force** (Amara & Abigail) — Backend Capstone, Project 3.

## Overview

Car-rental businesses lose track of vehicles: is a car reserved, on the road, in the workshop, or back with undocumented damage? FleetGo solves this by modeling every rental as a strict state machine — a fixed list of allowed moves between states, with anything else refused outright. Every accepted move is written to an append-only history table, so the record can't be quietly rewritten later. Pricing (late fees, damage charges) is always computed server-side; the client is never trusted with money.

## Features

- JWT authentication with three roles (customer, agent, manager) and ownership/role-based access control
- Rental lifecycle state machine: `RESERVED → ACTIVE → RETURNED`, `RESERVED → CANCELLED`, with row-level locking to guarantee exactly one winner under concurrent pickups
- Append-only `state_history` for every accepted rental state change
- Server-computed late fees and damage charges at return
- Car availability search with overlap-checking against existing reservations
- Manager-only pricing management per car class
- Workshop status tracking (`AVAILABLE` ↔ `IN_WORKSHOP`), separate from rental state
- Signed, idempotent payment webhook (HMAC-SHA256, duplicate-event protection via a unique `processed_events` table)
- Live fleet updates over Server-Sent Events (in-process pub/sub broadcaster, 15s heartbeat)
- Redis caching of the fleet board (30s TTL) with invalidation on every state-changing write
- Redis-backed rate limiting on `/auth/login` and `/auth/register` (5 attempts / 60s per IP, `429` + `Retry-After`)
- A scheduled job that auto-cancels stale `RESERVED` reservations
- Firestore mirror of the live fleet board and a dispatch event feed, with graceful degradation when Firestore isn't configured
- Centralized error handling — every error returns the same `{"error": {"code", "message", "request_id"}}` shape
- Request-id and response-timing middleware on every request

## Tech Stack

## Tech Stack

### Language
![Python](https://img.shields.io/badge/PYTHON-3776AB?style=for-the-badge&logo=python&logoColor=white)

### Backend Framework
![FastAPI](https://img.shields.io/badge/FASTAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLModel](https://img.shields.io/badge/SQLMODEL-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![Pydantic](https://img.shields.io/badge/PYDANTIC--SETTINGS-E92063?style=for-the-badge&logo=pydantic&logoColor=white)

### Database & Migrations
![PostgreSQL](https://img.shields.io/badge/POSTGRESQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Alembic](https://img.shields.io/badge/ALEMBIC-6BA81E?style=for-the-badge&logo=alembic&logoColor=white)

### Caching & Rate Limiting
![Redis](https://img.shields.io/badge/REDIS-DC382D?style=for-the-badge&logo=redis&logoColor=white)

### Secondary Store
![Firestore](https://img.shields.io/badge/FIRESTORE-FFA000?style=for-the-badge&logo=firebase&logoColor=white)

### Authentication
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![bcrypt](https://img.shields.io/badge/BCRYPT-4B8BBE?style=for-the-badge&logo=letsencrypt&logoColor=white)

### Containerization
![Docker](https://img.shields.io/badge/DOCKER-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/DOCKER%20COMPOSE-2496ED?style=for-the-badge&logo=docker&logoColor=white)

### Dependency Management
![uv](https://img.shields.io/badge/UV-DE5FE9?style=for-the-badge&logo=uv&logoColor=white)

### Testing
![Pytest](https://img.shields.io/badge/PYTEST-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

### Email
![SMTP](https://img.shields.io/badge/SMTP-004E89?style=for-the-badge&logo=maildotru&logoColor=white)
![MailHog](https://img.shields.io/badge/MAILHOG-FF6B6B?style=for-the-badge&logo=gmail&logoColor=white)

## Architecture

The codebase is organized by feature, not by layer. Each feature under `app/features/<name>/` follows the same internal shape:

```
schemas.py     → request/response models
repository.py  → all database queries for that feature — nothing else touches the session
service.py     → business rules, transactions, orchestration
router.py      → thin route functions; parse the request, call one service function
```

Route functions never contain business logic and never query the database directly. Services own transactions — one transaction per business action, committed once. Cross-cutting concerns (Redis, Firestore, email, the SSE broadcaster) live outside the feature folders in `app/core/` and `app/integrations/`, and are called from services after a successful commit, never before — so a cache invalidation, a Firestore write, or a broadcast is never sent for a change that could still roll back.

The rental lifecycle is implemented as a single state machine function (`perform_move`) that locks the target row, checks the requested move against a fixed table of allowed transitions, and refuses anything not on that list with a `409`. No route or other service function is allowed to change rental state directly.

## Project Structure

```
app/
  core/
    config.py            # Settings (pydantic-settings)
    dependencies.py       # get_session-based DbSession, get_current_user, require_role
    security.py            # JWT + bcrypt
    error.py                # centralized exception handlers, one error shape
    redis_client.py         # shared Redis client
    rate_limit.py            # rate_limit(prefix) dependency factory
  db/
    session.py
    seed.py                 # idempotent bootstrap manager seed script
  models/
    car.py, user.py, rental.py, state_history.py, payment.py,
    pricing.py, workshop_visit.py, processed_event.py
  events/
    broadcaster.py           # in-process SSE pub/sub
  integrations/
    email.py                 # SMTP adapter, stubs gracefully if unconfigured
    events.py                 # thin wrapper around the SSE broadcaster
    firestore.py               # save_document primitive + fleet board / dispatch feed writers
    notifications.py
  features/
    auth/       schemas.py, repository.py, service.py, router.py
    cars/       schemas.py, repository.py, service.py, router.py
    rentals/    schemas.py, repository.py, service.py, state_machine.py, router.py
    payments/   schemas.py, repository.py, service.py, router.py, webhook_*.py
    fleet/      schemas.py, repository.py, service.py, router.py
    workshop/   schemas.py, repository.py, service.py, router.py
  main.py
alembic/
tests/
  auth/, cars/, payments/, rentals/, webhooks/, conftest.py
mock_payment_provider.py
```

## Installation

Requires Docker and Docker Compose.

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in the required values (see **Environment Variables** below).
3. Build and start the stack:
   ```bash
   docker compose up -d --build
   ```
4. Confirm the API is up:
   ```bash
   curl http://localhost:8000/docs
   ```
5. Seed the bootstrap manager account:
   ```bash
   docker compose exec api uv run python -m app.db.seed
   ```

## Environment Variables

Defined in `app/core/config.py`, loaded from `.env`:

| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `TEST_DATABASE_URL` | no | used by the test suite |
| `REDIS_URL` | yes | used for caching and rate limiting |
| `JWT_SECRET` | yes | |
| `JWT_ALGORITHM` | no | defaults to `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | defaults to `30` |
| `BCRYPT_ROUNDS` | no | defaults to `12` |
| `WEBHOOK_SECRET` | yes | HMAC-SHA256 secret for the payment webhook |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` / `SMTP_FROM_EMAIL` | no | email is stubbed if not configured |
| `FIRESTORE_CREDENTIALS_PATH` | no | path to a service-account JSON key; Firestore writes are stubbed if not set or the file doesn't exist |
| `API_PREFIX` | no | defaults to `/api/v1` |

`docker-compose.yml` overrides `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET` and `WEBHOOK_SECRET` for the containerized environment via its own `environment:` block, which takes precedence over `.env` for those specific keys.

No real secret values are committed. Service account key files (`*-firebase-adminsdk*.json` and similarly named credential files) are gitignored.

## Database

PostgreSQL, accessed through SQLModel. The schema:

- `users` (email UNIQUE, password_hash, role)
- `cars` (plate UNIQUE, class, status), indexed on plate
- `rentals` (customer, car, start_at, end_at, state, total), indexed on (car, start_at, end_at)
- `state_history` (rental, from_state, to_state, actor, at) — append-only, one row per accepted move
- `pricing` (class, daily_rate, late_fee_per_day)
- `payments` (rental, kind, amount, recorded_by, recorded_at)
- `workshop_visits` (car, opened_at, closed_at, note)
- `processed_events` (event_id UNIQUE, reference, processed_at) — webhook idempotency

Locally, the whole stack runs against the `postgres` service defined in `docker-compose.yml` — there is no local host Postgres install involved.

## Migrations

Schema changes are managed with Alembic. `app/models/__init__.py` imports every model submodule so `SQLModel.metadata` sees every table — this import is required for `alembic revision --autogenerate` and for the test suite to work correctly.

```bash
docker compose exec api uv run alembic upgrade head
docker compose exec api uv run alembic revision --autogenerate -m "description"
```

## API

All routes are mounted under `/api/v1` (`settings.api_prefix`, defined once in `config.py`, never hardcoded per router).

| Method | Path | Who | Notes |
|---|---|---|---|
| POST | `/auth/register` | public | forces `CUSTOMER` role; rate limited |
| POST | `/auth/login` | public | rate limited |
| POST | `/auth/staff` | manager | creates agent/manager accounts |
| GET | `/cars` | customer | filter by class + date range |
| POST | `/cars` | manager | |
| POST | `/cars/{id}/workshop` | manager | |
| POST | `/cars/{id}/back-in-service` | manager | |
| PUT | `/pricing/{class}` | manager | |
| POST | `/rentals` | customer | creates a rental already `RESERVED` |
| POST | `/rentals/{id}/pickup` | agent | |
| POST | `/rentals/{id}/return` | agent | computes late fee + damage charge |
| POST | `/rentals/{id}/cancel` | customer | |
| GET | `/rentals/{id}` | owner / staff | |
| GET | `/rentals/{id}/history` | staff | |
| GET | `/rentals` | staff | paginated, filterable by state |
| POST | `/rentals/{id}/payments` | agent | |
| GET | `/fleet/board` | manager | Redis-cached, 30s TTL |
| GET | `/fleet/stream` | manager | Server-Sent Events |
| POST | `/webhooks/payment` | machine (signed) | no JWT; HMAC-SHA256 signature |

## Authentication

JWT bearer tokens, issued at login. `get_current_user` decodes and validates the token and loads the corresponding user; `require_role(*roles)` is a reusable dependency factory that returns a pre-wrapped `Depends(...)`, used as `dependencies=[require_role("manager")]` on routes. Passwords are hashed with bcrypt. Public registration always creates a `CUSTOMER`; agent and manager accounts can only be created by an existing manager through `/auth/staff`. The very first manager is created out-of-band by `app/db/seed.py`, run directly against the database — an idempotent script, safe to re-run.

## External Services

- **Redis** — fleet board response caching and login/register rate limiting.
- **Google Cloud Firestore** — mirrors current per-car status (`fleet_board/{car_id}`) and an event timeline (`dispatch_feed`) for the two write paths that change car/rental state. Writes go through a single `save_document` primitive that stubs gracefully (returns a `"stubbed"` result) instead of failing when no credentials are configured, so the app and test suite run without a live Firestore connection.
- **SMTP** — transactional email via `app/integrations/email.py`, with the same graceful-stub behavior when unconfigured. MailHog is included in `docker-compose.yml` for local testing without a real mail provider.
- **The payment provider (webhook)** — an external, machine caller that confirms deposits by POSTing a signed event to `/webhooks/payment`. Verified against the project's `mock_payment_provider.py` script, including duplicate-delivery and bad-signature scenarios.

## Docker

`docker-compose.yml` defines:

- `api` — the FastAPI app, built from the project `Dockerfile`, bind-mounted at `/workspace`, running via `uv run fastapi dev app/main.py`
- `postgres` — Postgres 17, with a healthcheck
- `redis` — Redis 7, with a healthcheck
- `fleetgo-mailhog` — local SMTP catcher for testing email delivery

Rebuild the API container after any code change:

```bash
docker compose up -d --force-recreate api
```

## Testing

```bash
docker compose exec api uv run pytest -v
```

34 tests currently pass, covering auth, cars, payments, rentals (including the five required hard-problem tests — every allowed/disallowed move, the concurrent-pickup race, state_history row counts, and late-fee correctness), and the payment webhook.

## CI/CD

Not currently configured. A GitHub Actions workflow was set up earlier in the project but was removed after repeated, unresolved lint and environment issues — a deliberate scope cut made under time pressure rather than an oversight.

## Usage

Interactive API documentation is available at `/docs` once the stack is running. A typical flow:

1. `POST /auth/register` as a customer, or log in as the seeded manager.
2. As manager, `POST /cars` to add vehicles and `PUT /pricing/{class}` to set rates.
3. As customer, `GET /cars` to search availability, then `POST /rentals` to reserve one.
4. The payment provider confirms the deposit via the webhook.
5. As agent, `POST /rentals/{id}/pickup`, and later `POST /rentals/{id}/return`.
6. As manager, watch `GET /fleet/board` (cached) or open `GET /fleet/stream` for live updates.

## Important Design Decisions

- **`Rental.car_id` is the foreign key**, not the other way around — a car has many rentals over time, so putting a pointer on `Car` would create two competing sources of truth for "the current rental."
- **Car status and rental state are two separate state machines.** `AVAILABLE ↔ IN_WORKSHOP` is tracked through `workshop_visits`, not through `state_history`, because a car going to the workshop isn't a rental-lifecycle event.
- **One central error handler**, not a custom exception hierarchy — every `HTTPException` and validation error is reshaped into the same `{"error": {...}}` envelope in one place, matching the brief's requirement without duplicating error-shaping logic across services.
- **Password hashing uses real bcrypt**, not a functionally-equivalent PBKDF2 implementation that was briefly used instead — the brief specifies bcrypt by name, and this was treated as non-negotiable even though switching required truncating and re-seeding the `users` table.
- **Webhook idempotency uses INSERT + catch `IntegrityError`** against a unique `event_id` column, not a SELECT-then-INSERT check — the latter has a race window under concurrent duplicate deliveries that the former does not.
- **The webhook signature is verified against the raw request body bytes**, read before any Pydantic parsing, since parsing and re-serializing first can change key order/whitespace and produce a signature mismatch against a real provider.
- **Firestore and email integrations degrade gracefully** rather than failing hard when unconfigured, so the app and test suite don't require live external credentials to run.
- **Cache and external-store writes happen strictly after `db.commit()`**, never before — so a rollback can never leave a stale cache invalidation, Firestore write, or SSE broadcast in its wake.

## Known Limitations

- No CI/CD pipeline currently configured.
- Not yet deployed; no live hosted URL.
- Mileage/condition capture at pickup and return is not yet wired to `Car.mileage`, despite the field existing on the model.
- The workshop feature folder exists with scaffolding but its full functionality is implemented through `cars/service.py` rather than its own dedicated service layer.

## Future Improvements

- Deployment to a managed host with a managed Postgres instance and a live `/docs` URL.
- Re-adding a working CI pipeline.
- Extending the seed script beyond the bootstrap manager account to include sample cars, pricing, and rentals for demo purposes.
- Writing mileage/condition capture into the pickup and return flows.

## Project Status

Core functionality is complete and tested: authentication and roles, car and pricing management, the rental state machine (the hard problem, with all required tests passing), payments, the signed idempotent webhook, the SSE stream, Redis caching and rate limiting, the stale-reservation scheduled job, and Firestore integration. Remaining work is deployment, CI, and demo-data seeding.

## License

Not currently specified in the project.
```