# The Webcraft Labs

A complete, production-quality website and admin management system for
**The Webcraft Labs** — a premium web & AI solutions studio.

Built with HTML5, CSS3, vanilla JavaScript, Python Flask, and SQLite.

## 1. Overview

The application has two halves:

- **Public site** — homepage, services, portfolio, about, careers (job board +
  application form), and a project-enquiry contact form.
- **Admin panel** — session-authenticated dashboard for managing enquiries,
  portfolio projects, job postings, and job applications.

The official brand logo is embedded directly into the app as a Base64 data
URI (see `embedded_assets/assets.py`) — there are no external image
dependencies anywhere in the site.

## 2. Features

**Public**
- Responsive homepage, services, portfolio (filterable by category), about,
  careers list, individual job pages, and a contact/enquiry form.
- Database-driven portfolio and careers — nothing is hardcoded.
- Empty states instead of fake placeholder data when no content exists yet.
- SEO: page titles, meta descriptions, Open Graph tags, `robots.txt`,
  `sitemap.xml`, semantic HTML, accessible alt text.
- Accessibility: semantic structure, visible focus states, labeled form
  fields, keyboard-navigable nav and forms.

**Admin**
- Session-based login with hashed passwords (never stored in plaintext).
- Dashboard with real counts pulled from SQLite (no fake stats).
- Enquiry management with status workflow (New → Contacted → In Discussion
  → Converted → Closed).
- Portfolio CRUD: create/edit/delete, publish/unpublish, feature/unfeature,
  image upload (stored as an embedded Base64 image, no external hosting).
- Career/job management: create/edit/delete, Draft/Open/Closed status
  workflow. Publishing a job requires no code changes.
- Application management: review submissions, update status, download
  resumes (only from authenticated admin routes — never public).

**Security**
- Parameterized SQL everywhere — no string-built queries.
- Passwords hashed with Werkzeug's `pbkdf2`/`scrypt`.
- Resume uploads validated by extension, MIME type, and size; stored under
  a server-generated random filename outside any public static directory.
- All admin routes protected by a `login_required` decorator.
- Request body size capped; per-file upload size capped (default 5MB,
  configurable).

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, vanilla JavaScript (no frameworks) |
| Backend | Python 3, Flask |
| Database | SQLite (schema written to be Postgres-migration-friendly) |
| Auth | Flask sessions + Werkzeug password hashing |

## 4. Installation

```bash
cd the-webcraft-labs
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 5. Environment Setup

Copy the example environment file and edit as needed:

```bash
cp .env.example .env
```

Key variables:

- `SECRET_KEY` — session signing key. Generate one with:
  `python -c "import secrets; print(secrets.token_hex(32))"`
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` — used to auto-create the first admin
  account on startup, if one doesn't already exist. **Change the password
  immediately after first login** (or before deploying).
- `DATABASE_URL` — SQLite file path (defaults to `webcraft.db`).
- `UPLOAD_MAX_MB` — max resume upload size in MB.

## 6. Database Initialization

The database and first admin account are created automatically the first
time the app starts (see `ensure_bootstrapped()` in `app.py`). You can also
run these manually via Flask CLI:

```bash
flask --app app init-db
flask --app app create-admin
```

## 7. Admin Account Setup

On first run, an admin account is created using `ADMIN_EMAIL` /
`ADMIN_PASSWORD` from your `.env` file. Log in at `/admin/login` and change
your password/details from `/admin/settings` as needed.

## 8. Running Locally

```bash
python3 app.py
```

The app runs at `http://127.0.0.1:5000` by default. Set `PORT` to change
the port, and `FLASK_DEBUG=1` to enable debug mode locally (never in
production).

## 9. Running Tests

The test suite uses Python's built-in `unittest` (compatible with `pytest`
as well — `pytest` will auto-discover the same files):

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
# or, if pytest is installed:
pytest
```

Tests cover: authentication, enquiry validation & SQL-injection resilience,
the full careers → application → resume-download workflow (including
closed-job rejection and unauthenticated resume access being blocked),
portfolio CRUD and publish/feature toggles, and route-level access control
across every admin endpoint.

## 10. Project Structure

```
the-webcraft-labs/
├── app.py                   # Flask app factory, global context, CLI commands
├── config.py                 # Config from environment
├── requirements.txt
├── .env.example
├── database/
│   ├── schema.sql
│   └── database.py           # Parameterized query helpers
├── routes/
│   ├── public.py              # Home, services, portfolio, about, contact
│   ├── admin.py                # All /admin/* routes
│   ├── careers.py              # Public careers + job detail + apply
│   └── enquiries.py            # Enquiry validation/persistence logic
├── services/
│   ├── auth.py                 # Password hashing, session, login_required
│   ├── asset_service.py        # Admin-uploaded image -> Base64
│   └── upload_service.py       # Resume upload validation & storage
├── templates/                  # Jinja2 templates (public + admin/)
├── static/
│   ├── css/                    # main.css, components.css, admin.css
│   └── js/                     # main.js, forms.js, admin.js
├── embedded_assets/
│   └── assets.py                # Base64-embedded brand logo/favicon
├── uploads/                     # Resume storage (not publicly served)
└── tests/                       # unittest/pytest-compatible test suite
```

## 11. Asset Embedding Process

The official Webcraft Labs logo was resized into web-appropriate variants
(512px for hero/about, 128px for the navbar, 32/64px favicons), converted
to WebP where beneficial for size, and Base64-encoded once into
`embedded_assets/assets.py`. Every template imports from this single
module via the app's Jinja context processor (`logo_main`, `logo_small`),
so the same encoded string is never duplicated across files.

Admin-uploaded portfolio images follow the same pattern at runtime: the
`asset_service.file_to_data_uri()` helper validates and Base64-encodes the
upload, and the resulting data URI is stored directly in the `projects`
table — no image ever touches a public static folder or external host.

> **Note on the other uploaded marketing images**: the four promotional
> banner images provided alongside the logo contain a different placeholder
> brand name ("Rokt"), hardcoded personal contact details, and baked-in
> marketing copy — they were freelancer promo graphics, not reusable site
> assets. Using them as-is would have put the wrong brand name and someone's
> phone number on The Webcraft Labs' live site, so they were intentionally
> left out. The official circular logo is the only asset embedded and used
> throughout the site. The hero visual is instead a custom CSS/JS-animated
> mockup consistent with the brand's futuristic-but-trustworthy direction.

## 12. Deployment Considerations

- Set `FLASK_DEBUG=0` (default) and use a production WSGI server (e.g.
  `gunicorn app:app`) — never the Flask dev server in production.
- Set a strong, random `SECRET_KEY` and change the default admin password.
- SQLite is fine for low-to-moderate traffic; the database layer
  (`database/database.py`) uses explicit column types and parameterized
  queries so migrating to PostgreSQL later mainly means swapping the
  connection/driver, not rewriting call sites.
- Put the app behind HTTPS in production; set `SESSION_COOKIE_SECURE=True`
  once served over HTTPS.
- Back up `webcraft.db` and the `uploads/` directory (resumes) regularly.
- Consider moving uploaded resumes to object storage (e.g. S3) at scale;
  the `upload_service.py` abstraction keeps that swap contained.
#   w e b c r a f t l a b s  
 