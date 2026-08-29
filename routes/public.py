from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from database.database import query_all

from routes.enquiries import (
    create_enquiry,
    ValidationError,
    SERVICE_OPTIONS,
)

from services.asset_service import (
    create_project_image_signed_url,
    AssetError,
)


public_bp = Blueprint(
    "public",
    __name__,
)


# ============================================================
# Project image helper
# ============================================================

def prepare_project_images(projects):
    """
    Converts Supabase Storage paths into temporary signed URLs.

    Old Base64 images are kept working for backward compatibility.
    """

    prepared_projects = []

    for project in projects:

        # Convert sqlite.Row / dict-like row into a normal dict.
        project = dict(project)

        image_path = project.get(
            "image_data"
        )

        if image_path:

            try:

                project["image_url"] = (
                    create_project_image_signed_url(
                        image_path,
                        expires_in=3600,
                    )
                )

            except AssetError:

                # If an image cannot be accessed,
                # don't break the whole public page.
                project["image_url"] = None

        else:

            project["image_url"] = None

        prepared_projects.append(
            project
        )

    return prepared_projects


# ============================================================
# Home
# ============================================================

@public_bp.route("/")
def home():

    featured_projects = query_all(
        """
        SELECT *
        FROM projects
        WHERE is_published = TRUE
          AND is_featured = TRUE
        ORDER BY sort_order
        LIMIT 3
        """
    )

    featured_projects = prepare_project_images(
        featured_projects
    )

    return render_template(
        "index.html",
        featured_projects=featured_projects,
    )


# ============================================================
# Services
# ============================================================

@public_bp.route("/services")
def services():

    return render_template(
        "services.html"
    )


# ============================================================
# Portfolio
# ============================================================

@public_bp.route("/portfolio")
def portfolio():

    category = (
        request.args.get(
            "category",
            ""
        )
        .strip()
    )

    if category:

        projects = query_all(
            """
            SELECT *
            FROM projects
            WHERE is_published = TRUE
              AND category = ?
            ORDER BY sort_order
            """,
            (category,),
        )

    else:

        projects = query_all(
            """
            SELECT *
            FROM projects
            WHERE is_published = TRUE
            ORDER BY sort_order
            """
        )

    categories = query_all(
        """
        SELECT DISTINCT category
        FROM projects
        WHERE is_published = TRUE
        ORDER BY category
        """
    )

    projects = prepare_project_images(
        projects
    )

    return render_template(
        "portfolio.html",
        projects=projects,
        categories=[
            c["category"]
            for c in categories
        ],
        active_category=category,
    )


# ============================================================
# About
# ============================================================

@public_bp.route("/about")
def about():

    return render_template(
        "about.html"
    )


# ============================================================
# Contact / Enquiry
# ============================================================

@public_bp.route(
    "/contact",
    methods=["GET", "POST"],
)
def contact():

    if request.method == "POST":

        try:

            create_enquiry(
                request.form
            )

            flash(
                "Thanks — your project enquiry has been sent. "
                "We'll respond within one business day.",
                "success",
            )

            return redirect(
                url_for(
                    "public.contact"
                )
            )

        except ValidationError as e:

            for field, msg in e.errors.items():

                flash(
                    msg,
                    "error",
                )

            return render_template(
                "contact.html",
                services=SERVICE_OPTIONS,
                form=request.form,
            ), 400

    return render_template(
        "contact.html",
        services=SERVICE_OPTIONS,
        form={},
    )