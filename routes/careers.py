import re

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
)

from database.database import (
    query_all,
    query_one,
    execute,
)

from services.upload_service import (
    save_resume,
    delete_resume,
    UploadError,
)


careers_bp = Blueprint(
    "careers",
    __name__,
)


EMAIL_RE = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


# ============================================================
# Helpers
# ============================================================

def slugify(text: str) -> str:
    """
    Converts text into a URL-friendly slug.
    """

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        text.lower(),
    ).strip("-")

    return slug or "job"


def get_open_jobs():
    """
    Returns all currently open jobs.
    """

    return query_all(
        """
        SELECT *
        FROM jobs
        WHERE status = 'Open'
        ORDER BY posted_at DESC
        """
    )


def get_job_by_slug(slug: str):
    """
    Returns a job by its unique slug.
    """

    return query_one(
        """
        SELECT *
        FROM jobs
        WHERE slug = ?
        """,
        (slug,),
    )


# ============================================================
# Careers list
# ============================================================

@careers_bp.route("/careers")
def careers_list():

    jobs = get_open_jobs()

    return render_template(
        "careers.html",
        jobs=jobs,
    )


# ============================================================
# Job detail + application
# ============================================================

@careers_bp.route(
    "/careers/<slug>",
    methods=["GET", "POST"],
)
def job_detail(slug):

    job = get_job_by_slug(
        slug
    )

    if not job:
        abort(404)

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "job_detail.html",
            job=job,
            form={},
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    # Do not accept applications for closed jobs.
    if job["status"] != "Open":

        flash(
            "This position is no longer accepting applications.",
            "error",
        )

        return redirect(
            url_for(
                "careers.job_detail",
                slug=slug,
            )
        )

    # --------------------------------------------------------
    # Form data
    # --------------------------------------------------------

    full_name = (
        request.form.get("full_name")
        or ""
    ).strip()

    email = (
        request.form.get("email")
        or ""
    ).strip()

    phone = (
        request.form.get("phone")
        or ""
    ).strip()

    portfolio_url = (
        request.form.get("portfolio_url")
        or ""
    ).strip()

    cover_message = (
        request.form.get("cover_message")
        or ""
    ).strip()

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    errors = []

    if len(full_name) < 2:
        errors.append(
            "Please enter your full name."
        )

    if not EMAIL_RE.match(email):
        errors.append(
            "Please enter a valid email address."
        )

    resume_file = request.files.get(
        "resume"
    )

    safe_name = None
    original_name = None

    # --------------------------------------------------------
    # Resume validation + Supabase upload
    # --------------------------------------------------------

    if not errors:

        try:

            safe_name, original_name = save_resume(
                resume_file
            )

        except UploadError as e:

            errors.append(
                str(e)
            )

    # --------------------------------------------------------
    # Validation/upload failed
    # --------------------------------------------------------

    if errors:

        for error in errors:

            flash(
                error,
                "error",
            )

        return render_template(
            "job_detail.html",
            job=job,
            form=request.form,
        ), 400

    # --------------------------------------------------------
    # Save application in PostgreSQL
    # --------------------------------------------------------

    try:

        execute(
            """
            INSERT INTO applications
            (
                job_id,
                full_name,
                email,
                phone,
                portfolio_url,
                cover_message,
                resume_filename,
                resume_original_name
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job["id"],
                full_name,
                email,
                phone,
                portfolio_url,
                cover_message,
                safe_name,
                original_name,
            ),
        )

    except Exception:

        # ----------------------------------------------------
        # IMPORTANT:
        # Resume was already uploaded to Supabase.
        #
        # If PostgreSQL insert fails, delete the uploaded
        # resume so we don't leave an orphaned file.
        # ----------------------------------------------------

        if safe_name:

            try:

                delete_resume(
                    safe_name
                )

            except Exception:
                # Do not hide the original database error.
                pass

        flash(
            "We couldn't submit your application right now. "
            "Please try again.",
            "error",
        )

        return render_template(
            "job_detail.html",
            job=job,
            form=request.form,
        ), 500

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    flash(
        "Your application has been submitted. "
        "We'll be in touch soon.",
        "success",
    )

    return redirect(
        url_for(
            "careers.job_detail",
            slug=slug,
        )
    )