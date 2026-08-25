from flask import Blueprint, render_template, request, redirect, url_for, flash

from database.database import query_all
from routes.enquiries import create_enquiry, ValidationError, SERVICE_OPTIONS

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    featured_projects = query_all(
        "SELECT * FROM projects WHERE is_published = 1 AND is_featured = 1 ORDER BY sort_order LIMIT 3"
    )
    return render_template("index.html", featured_projects=featured_projects)


@public_bp.route("/services")
def services():
    return render_template("services.html")


@public_bp.route("/portfolio")
def portfolio():
    category = request.args.get("category", "").strip()
    if category:
        projects = query_all(
            "SELECT * FROM projects WHERE is_published = 1 AND category = ? ORDER BY sort_order",
            (category,),
        )
    else:
        projects = query_all("SELECT * FROM projects WHERE is_published = 1 ORDER BY sort_order")
    categories = query_all(
        "SELECT DISTINCT category FROM projects WHERE is_published = 1 ORDER BY category"
    )
    return render_template(
        "portfolio.html", projects=projects, categories=[c["category"] for c in categories],
        active_category=category,
    )


@public_bp.route("/about")
def about():
    return render_template("about.html")


@public_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        try:
            create_enquiry(request.form)
            flash("Thanks — your project enquiry has been sent. We'll respond within one business day.", "success")
            return redirect(url_for("public.contact"))
        except ValidationError as e:
            for field, msg in e.errors.items():
                flash(msg, "error")
            return render_template(
                "contact.html", services=SERVICE_OPTIONS, form=request.form
            ), 400
    return render_template("contact.html", services=SERVICE_OPTIONS, form={})
