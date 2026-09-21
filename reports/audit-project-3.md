================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack: Python 3.12 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files: 13 analyzed | ~1158 lines of code
Date: 2026-09-21

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 5 | LOW: 3
Total: 16 findings

## Findings

### [CRITICAL] Insecure Password Handling (unsalted MD5)
File: `models/user.py:29,32`
Description: `set_password` stores `hashlib.md5(pwd.encode()).hexdigest()` with no salt and no work factor; `check_password` compares MD5 digests directly.
Impact: MD5 is broken for password storage — rainbow tables and GPU cracking recover every password if the DB leaks (OWASP A02). Also enables trivial credential stuffing.
Recommendation: Use `werkzeug.security.generate_password_hash` / `check_password_hash` (scrypt/pbkdf2 with salt); keep the `password` column but store the strong hash.

### [CRITICAL] Sensitive Data Exposure (password hash serialized)
File: `models/user.py:16-25` (via `user_routes.py:33,85,129,209`)
Description: `User.to_dict()` includes the `password` field, so it is returned in `GET /users/<id>`, `POST /users` (create), `PUT /users/<id>` and inside the `/login` response body.
Impact: The password hash is leaked to any API client on every user read/write and on login — directly exploitable for offline cracking given the MD5 above.
Recommendation: Remove `password` from `to_dict()`; expose only non-sensitive fields; never serialize the hash.

### [CRITICAL] Hardcoded Secrets in Source
File: `app.py:13` (`SECRET_KEY = 'super-secret-key-123'`) and `services/notification_service.py:8-10` (SMTP host/user and `email_password = 'senha123'`)
Description: Flask `SECRET_KEY` and SMTP credentials are hardcoded and version-controlled.
Impact: Any clone/commit leaks production secrets; SECRET_KEY compromise allows session/token forgery; SMTP password enables mail relay abuse.
Recommendation: Load all secrets from environment variables (`config/` module reading `os.environ`, `.env` via python-dotenv); provide `.env.example`; rotate leaked values.

### [CRITICAL] No Authentication / Authorization + Fake Token
File: `user_routes.py:210` (`'token': 'fake-jwt-token-' + str(user.id)`); all mutating routes in `task_routes.py`, `user_routes.py`, `report_routes.py`
Description: `/login` returns a non-cryptographic, guessable "token"; no endpoint validates any token; there is no RBAC (`is_admin()` exists in the model but is never enforced). Any anonymous caller can create/update/delete users, tasks and categories.
Impact: Complete lack of access control — full CRUD by unauthenticated clients; the token is predictable (`fake-jwt-token-<id>`) so it provides zero security even if checked.
Recommendation: Issue a signed token (JWT via `SECRET_KEY`) and add auth/role middleware (`@login_required`, `@admin_required`). Out of MVP scope to fully wire RBAC without breaking the contract, but the fake token must be replaced by a real signed token and documented.

### [HIGH] Business Logic in Routes / Dead Service Layer
File: `task_routes.py:85-154,156-223`; `user_routes.py:42-90`; `report_routes.py:13-101,103-155`; `services/notification_service.py` (never imported); `utils/helpers.py` (never imported)
Description: All validation, persistence and reporting logic lives inside route handlers. `services/` and `utils/helpers.py` are dead code — no module imports them — giving a false impression of layering.
Impact: Logic is not reusable or unit-testable, coupled to HTTP; the cosmetic service/utils layers rot and diverge.
Recommendation: Extract a real service layer (TaskService/UserService/CategoryService/ReportService); controllers/routes only orchestrate I/O; wire or remove the dead modules.

### [HIGH] N+1 Query Problem
File: `task_routes.py:41-57` (per-task `User.query.get` + `Category.query.get` inside the loop); `report_routes.py:15-28,53-68` (many separate `count()` and per-user `filter_by().all()`)
Description: `GET /tasks` runs 2 extra queries per task to resolve user/category names though `Task.user` / `Task.category` relationships already exist. `/reports/summary` fires ~15 `count()` queries plus one query per user.
Impact: Latency grows linearly/quadratically with data volume; needless DB pressure.
Recommendation: Use eager loading (`joinedload(Task.user)`, `joinedload(Task.category)`) and aggregate counts with a single grouped query / in-memory folding over one `.all()`.

### [HIGH] Debug Mode + Side Effects at Import
File: `app.py:31` (`db.create_all()` at module import) and `app.py:34` (`app.run(debug=True, host='0.0.0.0', port=5000)`)
Description: `debug=True` bound to `0.0.0.0`; DDL (`db.create_all`) runs as an import side effect.
Impact: Werkzeug interactive debugger = RCE and stack-trace leakage in production; import-time DDL causes surprising behavior under any WSGI server/test import.
Recommendation: Drive `debug`/host/port from config (default debug=false); move `db.create_all()` into an explicit init/CLI path via app factory; serve via WSGI (gunicorn) in prod.

### [HIGH] Swallowed Exceptions / Bare except (no central error handling)
File: `task_routes.py:62,137,204,236`; `user_routes.py:130,149`; `report_routes.py:186,207,221`; `utils/helpers.py:46-50,88`
Description: Bare `except:` / `except Exception` blocks swallow errors and return generic 500s; `GET /tasks` wraps the whole handler in `try/except: pass`-style catch. No centralized error handler.
Impact: Real errors hidden, hard to debug, inconsistent responses; bare `except` also catches `KeyboardInterrupt`/`SystemExit`.
Recommendation: Register a central `@app.errorhandler(Exception)` returning structured JSON `{error, code}` and logging internally; remove bare excepts.

### [MEDIUM] Missing Pagination (unbounded result sets)
File: `task_routes.py:14` (`Task.query.all()`), `task_routes.py:266`, `user_routes.py:12`, `report_routes.py:159`
Description: List endpoints return `.all()` with no `limit`/`offset`.
Impact: Memory/latency blow-up as data grows.
Recommendation: Add `limit`/`offset` (or `page`/`per_page`) pagination with safe defaults and caps.

### [MEDIUM] Duplicated Code (DRY) — "overdue" logic repeated 4x
File: `models/task.py:50-60` (`is_overdue`, unused), `task_routes.py:30-39,71-80,282-287`, `user_routes.py:171-180`, `report_routes.py:34-37,132-135`
Description: The same overdue computation (`due_date < now and status not in done/cancelled`) is hand-inlined in at least 4 route locations while `Task.is_overdue()` exists but is never called.
Impact: Divergence risk on maintenance; the canonical model method rots.
Recommendation: Centralize in `Task.is_overdue()` (aware datetimes) and reuse everywhere.

### [MEDIUM] Missing / Inconsistent Input Validation
File: `task_routes.py:261,264` (`int(priority)` / `int(user_id)` with no try/except); `report_routes.py` category create (no length checks); marshmallow is installed but unused
Description: Query params are cast with `int(...)` unguarded (500 on non-numeric); validation is ad-hoc and duplicated across handlers though `marshmallow` is a declared dependency.
Impact: Unhandled 500s from bad input; inconsistent validation rules.
Recommendation: Guard casts (return 400) and centralize validation (marshmallow schemas or shared validators in the service layer).

### [MEDIUM] Overly Permissive CORS
File: `app.py:15` (`CORS(app)`)
Description: CORS enabled globally with no origin allowlist (defaults to `*`).
Impact: Any origin can call the API from a browser; combined with the missing auth this widens the attack surface.
Recommendation: Restrict `origins`/methods/headers via config-driven allowlist.

### [MEDIUM] Weak / Duplicated Email Regex
File: `user_routes.py:61,106` and `utils/helpers.py:19-23`
Description: `^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$` accepts `a@b` (no TLD required) and is copy-pasted in three places (the helpers copy being dead).
Impact: Invalid emails accepted; divergent rules across call sites.
Recommendation: Single shared validator with a stricter pattern (require a dotted domain); reuse it.

### [LOW] print()-based Logging
File: `task_routes.py:149,153,219,234`; `user_routes.py:83,89,147`; `services/notification_service.py:21,24`; `utils/helpers.py:38-40`
Description: Uses `print(...)` for telemetry and error reporting instead of the `logging` module.
Impact: No levels, no structure, unusable in production observability.
Recommendation: Use `app.logger` / structured `logging`.

### [LOW] Dead / Unused Imports
File: `app.py:7` (`os, sys, json` unused); `task_routes.py:7` (`json, os, sys, time` unused); `user_routes.py:6` (`hashlib, json` unused); `report_routes.py:8` (`json`), `models/task.py:3` (`json`)
Description: Multiple modules import symbols they never use.
Impact: Noise, misleading dependencies.
Recommendation: Remove unused imports.

### [LOW] Verbose Boolean Returns / Naming
File: `models/user.py:34-38` (`is_admin` if/else returning True/False), `models/task.py:38-48` (`validate_status`/`validate_priority` verbose), loop vars `u`, `t`, `c`, `cat`
Description: `if x: return True else: return False` patterns and cryptic single-letter loop variables.
Impact: Readability.
Recommendation: Return the boolean expression directly; use domain names.

## Deprecated APIs
- `datetime.utcnow()` (`models/user.py:14`; `models/task.py:15,16`; `task_routes.py:31,72,215,285`; `user_routes.py:172`; `report_routes.py:35,42,45,71`; `seed.py:66-74`; `utils/helpers.py:38`) → use `datetime.now(timezone.utc)` (timezone-aware; `utcnow()` is deprecated in Python 3.12).
- `Model.query.get(id)` (`task_routes.py:42,51,67,117,122,158,188,195,227`; `user_routes.py:29,94,136,155`; `report_routes.py:105,192,213`) → use `db.session.get(Model, id)` (SQLAlchemy 2.0 LegacyAPIWarning).
- `Model.query` legacy accessor used broadly for filtering/counting → acceptable but prefer `db.session.execute(select(...))` in SQLAlchemy 2.0; not blocking.

================================
Total: 16 findings
================================
