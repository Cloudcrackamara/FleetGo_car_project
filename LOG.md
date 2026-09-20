## Day 1–4 (Catch-up) — 2026-09-20

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

### Team Responsibilities

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
