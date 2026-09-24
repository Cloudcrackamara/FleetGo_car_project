## Day 1–4 

### Team: Amara & Abigail

### Work Completed

During the first four days of the project, we finalized and approved the database design and system architecture. The Entity Relationship Diagram (ERD) was completed and validated, covering the following core entities:

* Users
* Cars
* Rentals
* Pricing
* Payments
* State History
* Workshop Visits
* Processed Events

Database migrations were successfully generated and applied, resulting in the creation of all required tables in PostgreSQL.

The Cars and Pricing module was implemented end-to-end, including:

* Request and response schemas
* Repository layer
* Service layer
* API routers/endpoints
* Car availability search logic using an overlap-query approach to prevent conflicting reservations

The Authentication and Authorization system was also completed, including:

* User registration
* User login
* JWT-based authentication
* Current user dependency injection
* Role-based authorization using `require_role()`

To improve API consistency and maintainability, error handling was standardized across the application using a single response structure for HTTP exceptions.

Infrastructure and observability improvements included:

* Request ID middleware for request tracing
* Timing middleware for response-time monitoring
* API versioning using the `/api/v1` prefix

Continuous Integration (CI) was configured and successfully passed all checks.


### Issues Encountered and Resolutions

#### 1. Docker Application Startup Failure

**Issue**

The API container failed to start and produced the following error:

```text
uvicorn: command not found
```

**Root Cause**

The application relied on PATH-based virtual environment detection inside the container. As a result, the `uvicorn` executable could not be reliably located at runtime.

**Resolution**

The Docker startup command was updated to execute Uvicorn through the uv environment manager:

```dockerfile
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Outcome**

The API container started successfully and became accessible through the configured port.

---

#### 2. Alembic Database Connection Failure

**Issue**

Alembic was unable to resolve the database hostname when executed from the host machine.

**Root Cause**

The hostname `postgres` exists only within Docker's internal network and is not resolvable from the local operating system.

**Resolution**

The database connection URL used by host-based tools was updated to use:

```text
localhost
```

instead of:

```text
postgres
```

**Outcome**

Alembic migrations were generated and executed successfully from the host environment.

---

#### 3. Continuous Integration Failure

**Issue**

The GitHub Actions workflow failed during the linting stage with the following error:

```text
ruff: command not found
```

**Root Cause**

The Ruff linter was referenced in the CI workflow but had not been declared as a project dependency.

**Resolution**

The dependency was installed and synchronized using:

```bash
uv add --dev ruff
uv sync
```

**Outcome**

The linting stage completed successfully and the CI pipeline returned a passing status.

---

### Key Learnings

* Docker service names such as `postgres` and `redis` are only accessible within the Docker network. When running tools directly from the host machine, `localhost` and the published container ports must be used instead.
* FastAPI route dependencies specified in the `dependencies=[]` parameter must be dependency callables wrapped with `Depends()`, rather than plain function references.
* Running applications through `uv run` provides a more reliable execution environment than relying on virtual environment PATH resolution inside containers.
* Middleware can be used to improve observability by tracking request identifiers and response times across the system.

---

#### Amara

* Infrastructure setup
* Docker and Docker Compose configuration
* Continuous Integration (CI)
* Application configuration and settings
* Security and authentication
* Dependency management
* Error handling
* Middleware implementation
* Cars/Pricing repository and service layers

#### Abigail

* Cars and Pricing schemas
* Support for repository query design
* Validation of car availability search logic
* Collaborative testing and review of the Cars/Pricing feature

---

### Next Steps

The next development phase will focus on:

1. Rental Management Feature
2. Rental Lifecycle State Machine (Hard Problem)
3. Payment Webhook Integration
4. Server-Sent Events (SSE) for real-time updates
5. Lifecycle transition validation and concurrency testing
6. State history auditing and event tracking


  ```
- **Docker networking gotcha**: `postgres`/`redis` as hostnames only
  resolve *inside* the Docker network. Host-side tools (pgAdmin, a
  host Python) must use `localhost` + the published port instead.
  `.env` (used by `alembic`/`uv run` from the host or inside the
  container) vs. `docker-compose.yml`'s `environment:` override for
  the `api` service are two different views of the same values —
  this was a recurring point of confusion early on.
- **Dockerfile fix**: switched `CMD` to `uv run uvicorn ...` instead of
  relying on `PATH` pointing at a venv — the original PATH-based
  approach intermittently failed with "uvicorn not found."

  The PgAdmin problem in coming up was resolved by logging in as Admin.

---

## Major incident: Git root misconfiguration

At one point `git status` showed the *entire project* (and unrelated
sibling folders on the Desktop) as deleted. Root cause: `.git` had
been initialized at the **Desktop** level, not inside the project
folder — `git rev-parse --show-toplevel` confirmed this. Recovery:
cloned fresh from GitHub into a new folder
(`Desktop/New folder/FleetGo_car_project`) rather than risk a
destructive `git clean`/`reset --hard` against a repo root that
included unrelated personal files. **This is the project's current
working location.** No data was lost — GitHub had the full, correct
history throughout.

---

##  Design decisions made (and the reasoning, for viva prep)

- **Rental state machine** — exactly three moves, per the original
  hand-drawn ERD, no extra PENDING state:
  - `RESERVED → ACTIVE` (pickup)
  - `ACTIVE → RETURNED` (return)
  - `RESERVED → CANCELLED` (cancel)
  - `POST /rentals` creates a rental **already RESERVED** (booking
    *is* the hold); the payment webhook records the deposit but
    doesn't transition state, since there's nothing before RESERVED
    to move from.
  - Car status (`AVAILABLE ↔ IN_WORKSHOP`) is a **separate** machine
    from rental state — tracked via `workshop_visits`
    (opened_at/closed_at), not through `state_history`.
- **`Rental.car_id` is the foreign key** (not `Car.rental_id`) — a
  car has many rentals over time; a rental has one car. Putting a
  pointer on Car would create two sources of truth for "current
  rental."
- **`state_history.rental_id` is kept** — without it a history row
  can't be tied to which rental it describes.
- **Error handling**: standardized on plain `HTTPException` raised
  from services (per the brief's own wording), with **one central
  handler** (`register_error_handlers` in `core/error.py`) that
  reshapes every `HTTPException`/`RequestValidationError` into the
  one required error envelope: `{"error": {"code","message",
  "request_id"}}`. No custom `AppError` class hierarchy — that was
  an earlier draft, deliberately abandoned for this simpler approach.
- **API versioning**: `settings.api_prefix = "/api/v1"`, single
  source of truth in `config.py`, every router mounted with
  `prefix=settings.api_prefix` in `main.py` — never hardcoded per
  router.
- **`require_role(*roles)`** returns `Depends(...)` already wrapped,
  so route declarations read `dependencies=[require_role("manager")]`
  with no extra `Depends()` wrapper needed.
- **Registration**: `POST /auth/register` is public but **forces
  UserRole.CUSTOMER** — it does not accept a role from the request
  body. Creating agent/manager accounts is a separate, **manager-only**
  endpoint: `POST /auth/staff`. This closed a real gap where a
  customer could originally self-assign any role.
- **Bootstrap problem**: the very first manager can't be created via
  `/auth/staff` (which itself requires a manager token). Solved with
  `app/db/seed.py` — a one-time script run directly against the DB
  (not through the API), idempotent (checks for the email before
  inserting).
- **Password hashing — bcrypt, not PBKDF2.** The codebase briefly
  drifted onto stdlib PBKDF2-SHA256 (functionally secure, but not
  what the brief specifies by name). Reverted to real bcrypt
  (`bcrypt.hashpw`/`bcrypt.checkpw`) to match the brief's explicit
  "bcrypt-hashed passwords" requirement and to actually use the
  already-declared `bcrypt` dependency. **This was a breaking
  change** — every existing password hash became unverifiable, so
  the `users` table was cleared (`TRUNCATE ... CASCADE` — a plain
  `DELETE FROM users` fails on the `rentals.customer_id` FK) and the
  manager was re-seeded.
- **Webhook signature vs. password hashing are deliberately
  different algorithms** — bcrypt (slow, salted, one-way, for
  passwords) vs. HMAC-SHA256 (fast, deterministic, shared-secret,
  for message authentication). These are not interchangeable and
  the webhook was never actually affected by the bcrypt/PBKDF2
  question — `verify_webhook_signature` used HMAC-SHA256 throughout.
- **Webhook idempotency**: INSERT into `processed_events`
  (`event_id UNIQUE`) and catch `IntegrityError` — not
  SELECT-then-INSERT, which has a race window under concurrent
  duplicate deliveries.
- **Webhook signature check**: verified against the **raw request
  body bytes**, read via `await request.body()` *before* any Pydantic
  parsing — parsing first and hashing a re-serialized version would
  pass local tests but fail against a real provider, since key order
  and whitespace differ.
- **Damage charge**: added to `POST /rentals/{id}/return` as a
  request body (`RentalReturn.damage_charge`, defaults to `Decimal("0")`),
  threaded through `perform_move` and `_apply_return`, added to
  `rental.total` alongside the computed late fee. This made `/return`
  require a body where it previously didn't — broke two existing
  tests until they were updated to send `json={}`.
- **SSE stream**: in-process `Broadcaster` (`app/events/broadcaster.py`)
  with pub/sub queues and a 15-second heartbeat comment (keeps
  proxies from closing an idle connection, per the brief).
  `perform_move` calls `fleet_broadcaster.publish(...)`
  **after** `db.commit()`/`db.refresh()` — never before, so a broadcast
  is never sent for a change that could still roll back.
  `GET /api/v1/fleet/stream` (manager-only) returns a
  `StreamingResponse` over `text/event-stream`.

---

## 4. What's built and PROVEN 

- **Auth**: register (customer-only), login, JWT issue/verify,
  `require_role`, manager-only staff creation, seed script — verified
  via Swagger login flow.
- **Cars + Pricing**: full CRUD, the availability-overlap query
  (`NOT EXISTS` correlated subquery against overlapping
  RESERVED/ACTIVE rentals) — manually verified via Python shell
  before and after inserting an overlapping rental.
- **Rentals + the hard problem**: `perform_move`, `ALLOWED_MOVES` as
  data (not branches), effects dispatched via a lookup dict, the row
  lock (`SELECT ... FOR UPDATE` in `repository.get_for_update`).
  **Five hard-problem tests, all passing**, including the genuinely
  hard concurrent-pickup race test (two real threads, two real DB
  sessions, asserting exactly one success and one 409). Full test
  suite currently green (13 passing after the damage-charge test
  fixes).
- **Payments**: agent-recorded payments against a rental.
- **The signed, idempotent webhook**: verified against the
  **provided `mock_payment_provider.py`** — all four scenarios
  passed exactly as expected (valid → confirms once; duplicate → no
  change; bad signature → 401; unknown reference → 200, orphan).
  Confirmed via direct DB query that `processed_events` contains the
  event_id exactly once.
- **SSE stream**: built, manually verified once via a two-terminal
  `curl -N` test (one terminal holds the stream open, a second
  terminal triggers a rental move, event appears on the first).


---

## 7. Recurring commands (cheat sheet)

```bash
# Rebuild + restart after any code change
docker compose up -d --force-recreate api

# Import sanity check (does the code even load?)
docker compose exec api uv run python -c "from app.main import app; print('ok')"

# Lint (uv run, not uvx — uvx re-fetches over the network every time
# and has failed on flaky connections; uv run uses the locked,
# already-installed dependency)
docker compose exec api uv run ruff check .
docker compose exec api uv run ruff check . --fix

# Full test suite
docker compose exec api uv run pytest -v

# One-off Python shell inside the container (for manual DB checks)
docker compose exec api uv run python

# Direct DB query
docker compose exec postgres psql -U fleetgo -d fleetgo -c "SELECT ...;"

# Seed the first manager account (idempotent, safe to re-run)
docker compose exec api uv run python -m app.db.seed

# Generate a random secret (for .env values)
docker compose exec api uv run python -c "import secrets; print(secrets.token_urlsafe(32))"

# Run the provided mock payment webhook tester
python mock_payment_provider.py \
  --url http://127.0.0.1:8000/api/v1/webhooks/payment \
  --secret <WEBHOOK_SECRET from .env> \
  --reference <a real rental id> \
  --amount 45000 \
  --duplicate --bad-signature --orphan
# (or, if host python isn't on PATH:)
docker compose exec api uv run python mock_payment_provider.py --url http://localhost:8000/api/v1/webhooks/payment ...
```

---

## 8. Git / commit workflow agreed for this 

- Live Share used for genuine pairing sessions; commits made through
  VS Code's **Source Control panel** (not the terminal) so Live
  Share can auto-append a `Co-authored-by:` trailer — this is known
  to sometimes stop working after the first commit of a session, so
  the trailer should be visually confirmed in the message box before
  committing, and added by hand if missing.
- For work that's genuinely one person's own (not paired), that
  person should be the sole author — `Co-authored-by` is only added
  when both people actually touched files in that specific commit,
  not as a blanket habit.
- Commit messages follow a `type(scope): summary` header with a
  bullet-point body explaining **what and why** — this was
  specifically tightened after a supervisor/CTO complaint about
  vague early messages ("configuration done", "ci test fixed",
  "folder structure"). Decision made: fix going forward rather than
  rewrite pushed history (rewriting risks breaking Abigail's local
  clone since history would diverge).
- Never commit `.env` or any real credentials/service-account JSON —
  a Firebase admin SDK key was caught in an early upload and flagged
  for rotation; `.gitignore` was tightened to catch
  `*firebase-adminsdk*.json` patterns specifically.

---

## 9. Immediate next step (where the session left off)

Debugging why `app/core/redis_client.py` was not importing even after
being created — verify:
1. `docker compose exec api ls -la app/core/redis_client.py` (does
   the file physically exist where the container can see it, exact
   filename/case)
2. `docker compose exec api ls app/core/` (does the bind mount show
   it at all)
3. Full, exact error text from the failing import (not paraphrased)

.


## Redis caching + rate limiting

- **Did:** Wrapped `fleet/service.get_board` in a Redis get/setex cache (30s TTL,
  key `fleet:board`), wired invalidation into `perform_move` and both workshop
  status-change functions. Added a reusable `rate_limit(prefix)` dependency
  (fixed-window `INCR`/`EXPIRE`, 5 attempts/60s per IP) on `/auth/login` and
  `/auth/register`.
- **Broke:** The central error handler (`core/error.py`) rebuilt every
  `HTTPException` into a fresh `JSONResponse` without copying `exc.headers` —
  silently dropping the `Retry-After` header on every 429, app-wide, not just
  on rate limiting.
- **Learnt:** A dependency that never runs looks identical to one that runs and
  fails silently — the fastest way to tell them apart is checking Redis
  directly (`KEYS`/`GET`/`TTL`) rather than trusting the HTTP response alone.
- **Next:** Firestore (`fleet_board`/`dispatch_feed`) and the scheduled job for
  stale reservations.
- **Who:** Amara — caching, rate limiting, and the header-passthrough fix.

---

## Debugging the rate limiter 

- **Did:** Traced a rate limiter that produced zero Redis keys despite six
  requests landing, through: container-rebuild checks, an empty-`KEYS` false
  alarm (checked before rebuilding), and a `curl` header check that missed
  `Retry-After` because grep was case-sensitive against a lowercase header.
- **Broke:** The real cause was mundane — the `rate_limit(...)` dependency and
  its import had never actually been saved into `auth/router.py`; a different
  router (`cars/router.py`) was pasted in its place during debugging.
- **Learnt:** When a fix "does nothing" after multiple rebuilds, verify the
  edit actually landed in the right file before re-checking infrastructure —
  wasted several debugging cycles on Docker/Redis before finding a plain
  unsaved edit.
- **Next:** Same as above — Firestore and the scheduled job.
- **Who:** Amara.

---

## 2026-09-23/24 — Firestore integration + credential rotation (Amara)

- **Did:** Built `app/integrations/firestore.py` around a `save_document`
  primitive (mirroring `email.py`'s graceful-stub pattern for when Firestore
  isn't configured), with `update_fleet_board`/`append_dispatch_event` as thin
  wrappers, wired into `perform_move` and the workshop transitions. Rotated a
  leaked Firebase admin SDK key after a GCP policy-violation email and moved
  the new key path into `Settings`/`.env`.
- **Broke:** A chain of import errors — a typo (`update_fleet_boarde`), a stale
  function name (`log_rental_state_change`) left over from an earlier draft,
  a `.env` path that didn't match the real on-disk filename, and a `.gitignore`
  entry that also didn't match the real filename (meaning the rotated key
  briefly wasn't actually ignored).
- **Learnt:** Renamed/downloaded files silently drifting from what
  `.env`/`.gitignore` expect is a repeatable failure mode — worth diffing the
  literal filename (`ls -la`) against config values instead of assuming they
  match.
- **Next:** Merge Abigail's workshop + scheduled-job work; re-verify test suite.
- **Who:** Amara — Firestore, key rotation, config wiring.

---

## Merge with Abigail's workshop + scheduled job (Amara & Abigail)

- **Did:** Pulled Abigail's scheduled-job (stale `RESERVED` auto-cancellation)
  and workshop feature work; resolved a real merge conflict in
  `firestore.py` where her version's `save_document(collection, document_id,
  payload)` design (with graceful stubbing, matching `email.py`) conflicted
  with the wrapper-only version built the day before.
- **Broke:** Accepting "our" side of the conflict wholesale silently deleted
  `save_document`, which her own test file (`test_fleetgo.py`) depended on —
  surfaced as a pytest collection error (`ImportError`), not a merge error.
- **Learnt:** Resolving a conflict by picking one side isn't always correct
  even when one side "already works" — the right fix was combining both
  designs (her primitive + the existing wrapper functions), not discarding
  either wholesale.
- **Next:** Re-add CI, deploy, seed script, README's "hard problem"/"why this
  design" sections.
- **Who:** Amara — Firestore/merge resolution; Abigail — scheduled job,
  workshop feature, expanded test coverage across auth/cars/payments/rentals/
  webhooks, `notifications.py`.

---

##  Full suite green 

- **Did:** Ran the full test suite after the merge.
- **Broke:** Nothing — 34 tests passing (up from 13 pre-merge), no failures.
- **Learnt:** A clean `pytest -v` run after a non-trivial merge is worth doing
  immediately, before trusting the merge is actually safe — collection errors
  (like the `save_document` one above) hide behind a successful `git push` if
  you don't run it.
-