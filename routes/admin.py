from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session,
    send_file, abort,
)

from database.database import query_all, query_one, execute
from services.auth import authenticate, login_required, current_admin
from services.asset_service import file_to_data_uri, AssetError
from services.upload_service import resume_path
from routes.enquiries import (
    list_enquiries, get_enquiry, update_enquiry_status, delete_enquiry,
)
from routes.careers import slugify


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ENQUIRY_STATUSES = ["New", "Contacted", "In Discussion", "Converted", "Closed"]
APPLICATION_STATUSES = ["New", "Reviewing", "Shortlisted", "Interview", "Selected", "Rejected"]
JOB_STATUSES = ["Draft", "Open", "Closed"]


# ---------- Auth ----------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        admin = authenticate(email, password)

        if admin:
            session.clear()
            session["admin_id"] = admin["id"]
            flash(f"Welcome back, {admin['name']}.", "success")

            next_url = request.args.get("next") or url_for("admin.dashboard")
            return redirect(next_url)

        flash("Invalid email or password.", "error")
        return render_template("admin/login.html"), 401

    return render_template("admin/login.html")


@admin_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You've been logged out.", "success")
    return redirect(url_for("admin.login"))


# ---------- Dashboard ----------

@admin_bp.route("/")
@login_required
def dashboard():
    stats = {
        "total_enquiries": query_one(
            "SELECT COUNT(*) c FROM enquiries"
        )["c"],

        "new_enquiries": query_one(
            "SELECT COUNT(*) c FROM enquiries WHERE status='New'"
        )["c"],

        "active_projects": query_one(
            "SELECT COUNT(*) c FROM projects WHERE is_published = TRUE"
        )["c"],

        "open_jobs": query_one(
            "SELECT COUNT(*) c FROM jobs WHERE status='Open'"
        )["c"],

        "applications": query_one(
            "SELECT COUNT(*) c FROM applications"
        )["c"],
    }

    recent_enquiries = query_all(
        "SELECT * FROM enquiries ORDER BY created_at DESC LIMIT 5"
    )

    recent_applications = query_all(
        """SELECT applications.*, jobs.title AS job_title
           FROM applications
           JOIN jobs ON jobs.id = applications.job_id
           ORDER BY applications.created_at DESC
           LIMIT 5"""
    )

    active_jobs = query_all(
        "SELECT * FROM jobs WHERE status='Open' ORDER BY posted_at DESC"
    )

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_enquiries=recent_enquiries,
        recent_applications=recent_applications,
        active_jobs=active_jobs,
    )


# ---------- Enquiries ----------

@admin_bp.route("/enquiries")
@login_required
def enquiries():
    status = request.args.get("status", "")
    items = list_enquiries(status or None)

    return render_template(
        "admin/enquiries.html",
        enquiries=items,
        statuses=ENQUIRY_STATUSES,
        active_status=status,
    )


@admin_bp.route("/enquiries/<int:enquiry_id>", methods=["GET", "POST"])
@login_required
def enquiry_detail(enquiry_id):
    enquiry = get_enquiry(enquiry_id)

    if not enquiry:
        abort(404)

    if request.method == "POST":
        new_status = request.form.get("status")

        if new_status in ENQUIRY_STATUSES:
            update_enquiry_status(enquiry_id, new_status)
            flash("Status updated.", "success")

        return redirect(
            url_for("admin.enquiry_detail", enquiry_id=enquiry_id)
        )

    return render_template(
        "admin/enquiry_detail.html",
        enquiry=enquiry,
        statuses=ENQUIRY_STATUSES,
    )


@admin_bp.route("/enquiries/<int:enquiry_id>/delete", methods=["POST"])
@login_required
def enquiry_delete(enquiry_id):
    delete_enquiry(enquiry_id)
    flash("Enquiry deleted.", "success")
    return redirect(url_for("admin.enquiries"))


# ---------- Projects ----------

@admin_bp.route("/projects")
@login_required
def projects():
    items = query_all(
        "SELECT * FROM projects ORDER BY sort_order, created_at DESC"
    )

    return render_template(
        "admin/projects.html",
        projects=items,
    )


def _unique_slug(base_slug, existing_id=None):
    slug = base_slug
    n = 1

    while True:
        row = query_one(
            "SELECT id FROM projects WHERE slug = ?",
            (slug,),
        )

        if not row or row["id"] == existing_id:
            return slug

        n += 1
        slug = f"{base_slug}-{n}"


@admin_bp.route("/projects/new", methods=["GET", "POST"])
@login_required
def project_new():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()

        if not title:
            flash("Title is required.", "error")
            return render_template(
                "admin/project_form.html",
                project=None,
                form=request.form,
            ), 400

        image_data = None
        image_file = request.files.get("image")

        if image_file and image_file.filename:
            try:
                image_data = file_to_data_uri(image_file)
            except AssetError as e:
                flash(str(e), "error")
                return render_template(
                    "admin/project_form.html",
                    project=None,
                    form=request.form,
                ), 400

        slug = _unique_slug(slugify(title))

        execute(
            """INSERT INTO projects
               (
                   title,
                   slug,
                   category,
                   description,
                   case_study,
                   technology,
                   live_url,
                   image_data,
                   is_published,
                   is_featured,
                   sort_order
               )
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title,
                slug,
                request.form.get("category", "").strip(),
                request.form.get("description", "").strip(),
                request.form.get("case_study", "").strip(),
                request.form.get("technology", "").strip(),
                request.form.get("live_url", "").strip(),
                image_data,
                True if request.form.get("is_published") else False,
                True if request.form.get("is_featured") else False,
                int(request.form.get("sort_order") or 0),
            ),
        )

        flash("Project created.", "success")
        return redirect(url_for("admin.projects"))

    return render_template(
        "admin/project_form.html",
        project=None,
        form={},
    )


@admin_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def project_edit(project_id):
    project = query_one(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,),
    )

    if not project:
        abort(404)

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()

        if not title:
            flash("Title is required.", "error")
            return render_template(
                "admin/project_form.html",
                project=project,
                form=request.form,
            ), 400

        image_data = project["image_data"]
        image_file = request.files.get("image")

        if image_file and image_file.filename:
            try:
                image_data = file_to_data_uri(image_file)
            except AssetError as e:
                flash(str(e), "error")
                return render_template(
                    "admin/project_form.html",
                    project=project,
                    form=request.form,
                ), 400

        execute(
            """UPDATE projects SET
               title=?,
               category=?,
               description=?,
               case_study=?,
               technology=?,
               live_url=?,
               image_data=?,
               is_published=?,
               is_featured=?,
               sort_order=?,
               updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (
                title,
                request.form.get("category", "").strip(),
                request.form.get("description", "").strip(),
                request.form.get("case_study", "").strip(),
                request.form.get("technology", "").strip(),
                request.form.get("live_url", "").strip(),
                image_data,
                True if request.form.get("is_published") else False,
                True if request.form.get("is_featured") else False,
                int(request.form.get("sort_order") or 0),
                project_id,
            ),
        )

        flash("Project updated.", "success")
        return redirect(url_for("admin.projects"))

    return render_template(
        "admin/project_form.html",
        project=project,
        form=project,
    )


@admin_bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def project_delete(project_id):
    execute(
        "DELETE FROM projects WHERE id = ?",
        (project_id,),
    )

    flash("Project deleted.", "success")
    return redirect(url_for("admin.projects"))


@admin_bp.route("/projects/<int:project_id>/toggle-publish", methods=["POST"])
@login_required
def project_toggle_publish(project_id):
    project = query_one(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,),
    )

    if not project:
        abort(404)

    execute(
        "UPDATE projects SET is_published = ? WHERE id = ?",
        (
            not bool(project["is_published"]),
            project_id,
        ),
    )

    return redirect(url_for("admin.projects"))


@admin_bp.route("/projects/<int:project_id>/toggle-featured", methods=["POST"])
@login_required
def project_toggle_featured(project_id):
    project = query_one(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,),
    )

    if not project:
        abort(404)

    execute(
        "UPDATE projects SET is_featured = ? WHERE id = ?",
        (
            not bool(project["is_featured"]),
            project_id,
        ),
    )

    return redirect(url_for("admin.projects"))


# ---------- Careers (jobs) ----------

@admin_bp.route("/careers")
@login_required
def careers():
    items = query_all(
        "SELECT * FROM jobs ORDER BY posted_at DESC"
    )

    return render_template(
        "admin/careers.html",
        jobs=items,
    )


def _unique_job_slug(base_slug, existing_id=None):
    slug = base_slug
    n = 1

    while True:
        row = query_one(
            "SELECT id FROM jobs WHERE slug = ?",
            (slug,),
        )

        if not row or row["id"] == existing_id:
            return slug

        n += 1
        slug = f"{base_slug}-{n}"


@admin_bp.route("/careers/new", methods=["GET", "POST"])
@login_required
def career_new():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()

        if not title:
            flash("Job title is required.", "error")
            return render_template(
                "admin/job_form.html",
                job=None,
                form=request.form,
            ), 400

        slug = _unique_job_slug(slugify(title))

        execute(
            """INSERT INTO jobs
               (
                   title,
                   slug,
                   department,
                   employment_type,
                   location,
                   description,
                   responsibilities,
                   requirements,
                   compensation,
                   deadline,
                   status
               )
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title,
                slug,
                request.form.get("department", "").strip(),
                request.form.get("employment_type", "").strip(),
                request.form.get("location", "").strip(),
                request.form.get("description", "").strip(),
                request.form.get("responsibilities", "").strip(),
                request.form.get("requirements", "").strip(),
                request.form.get("compensation", "").strip(),
                request.form.get("deadline", "").strip() or None,
                request.form.get("status")
                if request.form.get("status") in JOB_STATUSES
                else "Draft",
            ),
        )

        flash("Job created.", "success")
        return redirect(url_for("admin.careers"))

    return render_template(
        "admin/job_form.html",
        job=None,
        form={},
    )


@admin_bp.route("/careers/<int:job_id>/edit", methods=["GET", "POST"])
@login_required
def career_edit(job_id):
    job = query_one(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,),
    )

    if not job:
        abort(404)

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()

        if not title:
            flash("Job title is required.", "error")
            return render_template(
                "admin/job_form.html",
                job=job,
                form=request.form,
            ), 400

        execute(
            """UPDATE jobs SET
               title=?,
               department=?,
               employment_type=?,
               location=?,
               description=?,
               responsibilities=?,
               requirements=?,
               compensation=?,
               deadline=?,
               status=?,
               updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (
                title,
                request.form.get("department", "").strip(),
                request.form.get("employment_type", "").strip(),
                request.form.get("location", "").strip(),
                request.form.get("description", "").strip(),
                request.form.get("responsibilities", "").strip(),
                request.form.get("requirements", "").strip(),
                request.form.get("compensation", "").strip(),
                request.form.get("deadline", "").strip() or None,
                request.form.get("status")
                if request.form.get("status") in JOB_STATUSES
                else job["status"],
                job_id,
            ),
        )

        flash("Job updated.", "success")
        return redirect(url_for("admin.careers"))

    return render_template(
        "admin/job_form.html",
        job=job,
        form=job,
    )


@admin_bp.route("/careers/<int:job_id>/status", methods=["POST"])
@login_required
def career_set_status(job_id):
    new_status = request.form.get("status")

    if new_status in JOB_STATUSES:
        execute(
            "UPDATE jobs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_status, job_id),
        )

        flash(
            f"Job marked as {new_status}.",
            "success",
        )

    return redirect(url_for("admin.careers"))


@admin_bp.route("/careers/<int:job_id>/delete", methods=["POST"])
@login_required
def career_delete(job_id):
    execute(
        "DELETE FROM jobs WHERE id = ?",
        (job_id,),
    )

    flash("Job deleted.", "success")
    return redirect(url_for("admin.careers"))


# ---------- Applications ----------

@admin_bp.route("/applications")
@login_required
def applications():
    items = query_all(
        """SELECT applications.*, jobs.title AS job_title
           FROM applications
           JOIN jobs ON jobs.id = applications.job_id
           ORDER BY applications.created_at DESC"""
    )

    return render_template(
        "admin/applications.html",
        applications=items,
        statuses=APPLICATION_STATUSES,
    )


@admin_bp.route("/applications/<int:application_id>", methods=["GET", "POST"])
@login_required
def application_detail(application_id):
    app_row = query_one(
        """SELECT applications.*, jobs.title AS job_title
           FROM applications
           JOIN jobs ON jobs.id = applications.job_id
           WHERE applications.id = ?""",
        (application_id,),
    )

    if not app_row:
        abort(404)

    if request.method == "POST":
        new_status = request.form.get("status")

        if new_status in APPLICATION_STATUSES:
            execute(
                "UPDATE applications SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_status, application_id),
            )

            flash(
                "Application status updated.",
                "success",
            )

        return redirect(
            url_for(
                "admin.application_detail",
                application_id=application_id,
            )
        )

    return render_template(
        "admin/application_detail.html",
        application=app_row,
        statuses=APPLICATION_STATUSES,
    )


@admin_bp.route("/applications/<int:application_id>/resume")
@login_required
def application_resume(application_id):
    app_row = query_one(
        "SELECT * FROM applications WHERE id = ?",
        (application_id,),
    )

    if not app_row:
        abort(404)

    path = resume_path(app_row["resume_filename"])

    return send_file(
        path,
        as_attachment=True,
        download_name=(
            app_row["resume_original_name"]
            or app_row["resume_filename"]
        ),
    )


# ---------- Settings ----------

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    admin = current_admin()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()

        if name:
            execute(
                "UPDATE admins SET name = ? WHERE id = ?",
                (name, admin["id"]),
            )

            flash(
                "Settings saved.",
                "success",
            )

        return redirect(url_for("admin.settings"))

    return render_template(
        "admin/settings.html",
        admin=admin,
    )