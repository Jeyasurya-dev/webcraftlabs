import os

from flask import (
    Flask,
    render_template,
    Response,
)

from config import Config
from database.database import init_db
from embedded_assets import assets as brand_assets

from routes.public import public_bp
from routes.careers import careers_bp
from routes.admin import admin_bp


def create_app(config_object=Config):
    app = Flask(__name__)

    app.config.from_object(config_object)

    # ========================================================
    # Blueprints
    # ========================================================

    app.register_blueprint(public_bp)
    app.register_blueprint(careers_bp)
    app.register_blueprint(admin_bp)

    # ========================================================
    # Global template variables
    # ========================================================

    @app.context_processor
    def inject_globals():
        import datetime

        return {
            # ------------------------------------------------
            # Brand
            # ------------------------------------------------
            "brand_name": "The Webcraft Labs",
            "brand_tagline": "Web • AI Solutions",

            # ------------------------------------------------
            # Website identity
            # ------------------------------------------------
            "site_url": "https://webcraftlabs.site",
            "brand_legal_name": "The Webcraft Labs",

            # ------------------------------------------------
            # Brand assets
            # ------------------------------------------------
            "logo_main": brand_assets.LOGO_MAIN,
            "logo_small": brand_assets.LOGO_SMALL,

            # ------------------------------------------------
            # Current year
            # ------------------------------------------------
            "current_year": (
                datetime.datetime
                .now(datetime.timezone.utc)
                .year
            ),
        }

    # ========================================================
    # Error handlers
    # ========================================================

    @app.errorhandler(404)
    def not_found(e):
        return render_template(
            "404.html"
        ), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template(
            "500.html"
        ), 500

    # ========================================================
    # Favicon
    # ========================================================

    @app.route("/favicon.ico")
    def favicon():
        import base64

        raw = base64.b64decode(
            brand_assets.FAVICON_32.split(
                ",",
                1
            )[1]
        )

        return Response(
            raw,
            mimetype="image/png",
        )

    # ========================================================
    # Robots.txt
    # ========================================================

    @app.route("/robots.txt")
    def robots():

        return Response(
            (
                "User-agent: *\n"
                "Allow: /\n"
                "Disallow: /admin/\n"
                "Sitemap: https://webcraftlabs.site/sitemap.xml\n"
            ),
            mimetype="text/plain",
        )

    # ========================================================
    # Sitemap
    # ========================================================

    @app.route("/sitemap.xml")
    def sitemap():

        from database.database import query_all

        base = "https://webcraftlabs.site"

        pages = [
            "/",
            "/services",
            "/portfolio",
            "/about",
            "/careers",
            "/contact",
        ]

        jobs = query_all(
            """
            SELECT slug
            FROM jobs
            WHERE status = 'Open'
            """
        )

        urls = "".join(
            f"<url><loc>{base}{page}</loc></url>"
            for page in pages
        )

        urls += "".join(
            f"<url><loc>{base}/careers/{job['slug']}</loc></url>"
            for job in jobs
        )

        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset '
            'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"{urls}"
            "</urlset>"
        )

        return Response(
            xml,
            mimetype="application/xml",
        )

    # ========================================================
    # Flask CLI — Initialize database
    # ========================================================

    @app.cli.command("init-db")
    def init_db_command():

        init_db()

        print(
            "Database initialized."
        )

    # ========================================================
    # Flask CLI — Create admin
    # ========================================================

    @app.cli.command("create-admin")
    def create_admin_command():

        from services.auth import (
            create_admin,
            get_admin_by_email,
        )

        email = app.config[
            "ADMIN_EMAIL"
        ]

        password = app.config[
            "ADMIN_PASSWORD"
        ]

        if get_admin_by_email(email):

            print(
                f"Admin {email} already exists."
            )

            return

        create_admin(
            email,
            password,
            "Studio Admin",
        )

        print(
            f"Admin account created: {email}"
        )

    return app


# ============================================================
# Application bootstrap
# ============================================================

def ensure_bootstrapped(app):
    """
    Initialize the database and create the first admin
    account when the application starts.
    """

    with app.app_context():

        # ----------------------------------------------------
        # Database
        # ----------------------------------------------------

        init_db()

        # ----------------------------------------------------
        # First admin
        # ----------------------------------------------------

        from services.auth import (
            create_admin,
            get_admin_by_email,
        )

        email = app.config[
            "ADMIN_EMAIL"
        ]

        password = app.config[
            "ADMIN_PASSWORD"
        ]

        if not get_admin_by_email(email):

            create_admin(
                email,
                password,
                "Studio Admin",
            )


# ============================================================
# Application instance
# ============================================================

app = create_app()

ensure_bootstrapped(
    app
)


# ============================================================
# Local development
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000,
        )
    )

    debug = (
        os.environ.get(
            "FLASK_DEBUG",
            "0",
        )
        == "1"
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
    )