# Contributing to Mini-oLx

Thanks for your interest in making Mini-oLx better! This guide covers
how to set up a dev environment, our coding conventions, and how to
ship a change.

---

## 1. Code of conduct

Be kind. We follow the [Django Code of Conduct](https://www.djangoproject.com/conduct/).
Harassment of any kind is not tolerated.

---

## 2. Project layout (TL;DR)

* `mini_olx/` — Django project (settings, root URLs, ASGI/WSGI).
* `accounts/` — signup, OTP, login, custom user model.
* `product/` — listings (CRUD + image upload).
* `chat/` — WebSocket chat (consumer + http views + models).
* `templates/` — server-rendered HTML.
* `static/` — CSS design system, tiny JS helpers.
* `SCALING.md`, `product.md`, `context.md` — read these before
  opening a non-trivial PR.

---

## 3. Local dev setup

```bash
# 1. Clone and create a virtualenv
git clone https://github.com/<your-fork>/mini_olx.git
cd mini_olx
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1

# 2. Install deps
pip install -r requirements.txt

# 3. Copy environment template and fill in values
cp .env.example .env          # (or hand-create based on README)
# Required vars: SECRET_KEY, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD,
#                DEFAULT_FROM_EMAIL, CLOUD_NAME, CLOUD_API_KEY,
#                CLOUD_API_SECRET

# 4. Migrate and run
python manage.py migrate
python manage.py runserver
```

> **Tip:** To run chat locally without Redis, leave `REDIS_URL` empty —
> the app will fall back to `InMemoryChannelLayer`. That works only on
> a single process.

### Running with Redis (recommended)

```bash
docker run --name molx-redis -p 6379:6379 -d redis:7-alpine
export REDIS_URL=redis://localhost:6379/0
python manage.py runserver
```

---

## 4. Coding conventions

### Python

* **PEP 8**, max line length 100.
* **Models** — class names `PascalCase`; lowercase fields; always set
  `related_name` on FKs that may be reversed.
* **Views** — function-based unless a CBV is genuinely clearer. Use
  `@login_required` for any authenticated endpoint.
* **Async** — `consumers.py` only. Never call the ORM from a sync
  consumer — wrap it in `database_sync_to_async`.

### Templates

* Templates extend `base.html`; do not redefine the navbar.
* Use the `molx-` CSS namespace. No utility-first frameworks in
  templates — keep styles in `static/style.css`.
* Always pass `request` context (it's needed for `request.user`).

### Front-end

* Vanilla JS only — no build step. Keep `static/js/app.js` tiny.
* Test the chat page with the WebSocket dev tools open
  (DevTools → Network → WS filter).

### Database

* **Always** generate a migration after editing a model:
  ```bash
  python manage.py makemigrations
  ```
* Add an index in the same migration when adding a column that is
  used in `filter()` or `order_by()`.

### Settings

* All secrets via `python-decouple` (`config(...)`).
* Never hardcode hostnames or email addresses.
* New optional infra (e.g. Sentry, S3) should default to `None` and
  be wired conditionally.

---

## 5. Branch & commit workflow

1. **Branch off `main`.**  Prefix the branch:
   * `feat/<short-name>` for new features
   * `fix/<short-name>` for bug fixes
   * `docs/<short-name>` for docs-only changes
   * `chore/<short-name>` for tooling / dependency bumps

2. **Commit messages** — Conventional Commits, scoped where useful:
   ```
   feat(chat): add typing indicator
   fix(product): bust home cache on delete
   docs(readme): add Redis docker step
   ```

3. **Tests** — Add or update tests for any behavioural change. We
   use Django's built-in `TestCase`. To run:
   ```bash
   python manage.py test
   ```

4. **Lint** — Keep imports tidy. Project doesn't ship a linter config
   yet — `python -m pyflakes <changed-files>` is the minimum bar.

---

## 6. Pull request checklist

Before requesting review, confirm:

- [ ] `python manage.py makemigrations` produced no pending changes
      (or the new migration is committed).
- [ ] `python manage.py test` passes locally.
- [ ] `python manage.py check --deploy` raises no new warnings.
- [ ] Updated docs (`product.md`, `context.md`, `SCALING.md`) if you
      touched architecture, the home page, or the chat system.
- [ ] Screenshots / screen recordings attached for any UI change.
- [ ] No secrets in the diff (`.env`, API keys, etc.).
- [ ] If you changed a model: the corresponding migration is in the
      same PR.

---

## 7. Deployment notes

Production deploys go through `render.yaml` (Render Blueprint).

* Trigger a deploy by pushing to `main` (auto-deploy is on).
* Migrations run automatically inside `start.sh`.
* If you add a new env var, **also add it to `render.yaml`**.
* WebSockets require daphne — keep `start.sh` using daphne, not
  gunicorn, unless the chat feature is intentionally disabled.

---

## 8. Performance & scaling

Read `SCALING.md` before changing:

* `settings.py` (`CHANNEL_LAYERS`, `CACHES`, `DATABASES`).
* `asgi.py` (worker count, middleware order).
* `chat/consumers.py` (broadcast frequency, payload size).

The cardinal rule: **a chat room has exactly 2 participants.** Any
feature that scales with N participants (e.g. "room of N buyers per
listing") needs its own scaling review.

---

## 9. Getting help

* Open a GitHub issue for bugs / proposals.
* Tag `@maintainers` for review-nudge.
* Security issues: email `security@miniolx.example` (do **not** open a
  public issue).

Thanks for contributing! 🚀