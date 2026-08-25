import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from database.database import query_all, query_one, execute
from services.upload_service import save_resume, UploadError

careers_bp = Blueprint("careers", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "job"


def get_open_jobs():
    return query_all("SELECT * FROM jobs WHERE status = 'Open' ORDER BY posted_at DESC")


def get_job_by_slug(slug: str):
    return query_one("SELECT * FROM jobs WHERE slug = ?", (slug,))


@careers_bp.route("/careers")
def careers_list():
    jobs = get_open_jobs()
    return render_template("careers.html", jobs=jobs)


@careers_bp.route("/careers/<slug>", methods=["GET", "POST"])
def job_detail(slug):
    job = get_job_by_slug(slug)
    if not job:
        abort(404)

    if request.method == "POST":
        if job["status"] != "Open":
            flash("This position is no longer accepting applications.", "error")
            return redirect(url_for("careers.job_detail", slug=slug))

        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        portfolio_url = (request.form.get("portfolio_url") or "").strip()
        cover_message = (request.form.get("cover_message") or "").strip()

        errors = []
        if len(full_name) < 2:
            errors.append("Please enter your full name.")
        if not EMAIL_RE.match(email):
            errors.append("Please enter a valid email address.")

        resume_file = request.files.get("resume")
        safe_name = None
        original_name = None
        if not errors:
            try:
                safe_name, original_name = save_resume(resume_file)
            except UploadError as e:
                errors.append(str(e))

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("job_detail.html", job=job, form=request.form), 400

        execute(
            """INSERT INTO applications
               (job_id, full_name, email, phone, portfolio_url, cover_message,
                resume_filename, resume_original_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (job["id"], full_name, email, phone, portfolio_url, cover_message,
             safe_name, original_name),
        )
        flash("Your application has been submitted. We'll be in touch soon.", "success")
        return redirect(url_for("careers.job_detail", slug=slug))

    return render_template("job_detail.html", job=job, form={})
