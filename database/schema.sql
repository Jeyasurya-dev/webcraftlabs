-- The Webcraft Labs — SQLite schema
-- Designed to be migration-friendly to PostgreSQL (explicit types, no
-- SQLite-only quirks beyond AUTOINCREMENT / TEXT timestamps).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT 'Admin',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS enquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    company TEXT,
    service TEXT NOT NULL,
    budget_range TEXT,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'New'
        CHECK (status IN ('New','Contacted','In Discussion','Converted','Closed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_enquiries_status ON enquiries(status);
CREATE INDEX IF NOT EXISTS idx_enquiries_created ON enquiries(created_at);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    description TEXT,
    case_study TEXT,
    technology TEXT,
    live_url TEXT,
    image_data TEXT,            -- base64 data URI, uploaded via admin
    is_published INTEGER NOT NULL DEFAULT 0,
    is_featured INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_projects_published ON projects(is_published);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    employment_type TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT NOT NULL,
    responsibilities TEXT,
    requirements TEXT,
    compensation TEXT,
    deadline TEXT,
    status TEXT NOT NULL DEFAULT 'Draft'
        CHECK (status IN ('Draft','Open','Closed')),
    posted_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    portfolio_url TEXT,
    cover_message TEXT,
    resume_filename TEXT NOT NULL,   -- server-generated safe filename on disk
    resume_original_name TEXT,
    status TEXT NOT NULL DEFAULT 'New'
        CHECK (status IN ('New','Reviewing','Shortlisted','Interview','Selected','Rejected')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);

CREATE TABLE IF NOT EXISTS site_settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
