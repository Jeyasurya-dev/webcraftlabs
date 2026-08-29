-- The Webcraft Labs — PostgreSQL schema

CREATE TABLE IF NOT EXISTS admins (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT 'Admin',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);


CREATE TABLE IF NOT EXISTS enquiries (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    company TEXT,
    service TEXT NOT NULL,
    budget_range TEXT,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'New'
        CHECK (
            status IN (
                'New',
                'Contacted',
                'In Discussion',
                'Converted',
                'Closed'
            )
        ),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_enquiries_status
    ON enquiries(status);

CREATE INDEX IF NOT EXISTS idx_enquiries_created
    ON enquiries(created_at);


CREATE TABLE IF NOT EXISTS projects (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    description TEXT,
    case_study TEXT,
    technology TEXT,
    live_url TEXT,

    -- Supabase Storage path only.
    -- Example: projects/uuid.webp
    image_data TEXT,

    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_published
    ON projects(is_published);


CREATE TABLE IF NOT EXISTS jobs (
    id BIGSERIAL PRIMARY KEY,
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
        CHECK (
            status IN (
                'Draft',
                'Open',
                'Closed'
            )
        ),
    posted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_status
    ON jobs(status);


CREATE TABLE IF NOT EXISTS applications (
    id BIGSERIAL PRIMARY KEY,

    job_id BIGINT NOT NULL
        REFERENCES jobs(id)
        ON DELETE CASCADE,

    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    portfolio_url TEXT,
    cover_message TEXT,

    -- Supabase Storage path only.
    -- Example: resumes/uuid.pdf
    --
    -- Nullable because the resume is deleted
    -- when an application is rejected.
    resume_filename TEXT,

    resume_original_name TEXT,

    status TEXT NOT NULL DEFAULT 'New'
        CHECK (
            status IN (
                'New',
                'Reviewing',
                'Shortlisted',
                'Interview',
                'Selected',
                'Rejected'
            )
        ),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_applications_job
    ON applications(job_id);

CREATE INDEX IF NOT EXISTS idx_applications_status
    ON applications(status);


CREATE TABLE IF NOT EXISTS site_settings (
    key TEXT PRIMARY KEY,
    value TEXT
);