import os
from flask import Flask, render_template, send_from_directory, Response

from config import Config
from database.database import init_db
from embedded_assets import assets as brand_assets
from routes.public import public_bp
from routes.careers import careers_bp
from routes.admin import admin_bp


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    app.register_blueprint(public_bp)
    app.register_blueprint(careers_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_globals():
        import datetime
        return {
            "logo_main": brand_assets.LOGO_MAIN,
            "logo_small": brand_assets.LOGO_SMALL,
            "brand_name": "The Webcraft Labs",
            "brand_tagline": "Web • AI Solutions",
            "current_year": datetime.datetime.now(datetime.timezone.utc).year,
        }

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500

    @app.route("/favicon.ico")
    def favicon():
        import base64
        raw = base64.b64decode(brand_assets.FAVICON_32.split(",", 1)[1])
        return Response(raw, mimetype="image/png")

    @app.route("/robots.txt")
    def robots():
        return Response(
            "User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: /sitemap.xml\n",
            mimetype="text/plain",
        )

    @app.route("/sitemap.xml")
    def sitemap():
        from flask import request
        from database.database import query_all
        base = request.host_url.rstrip("/")
        pages = ["/", "/services", "/portfolio", "/about", "/careers", "/contact"]
        jobs = query_all("SELECT slug FROM jobs WHERE status='Open'")
        urls = "".join(f"<url><loc>{base}{p}</loc></url>" for p in pages)
        urls += "".join(f"<url><loc>{base}/careers/{j['slug']}</loc></url>" for j in jobs)
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "</urlset>"
        )
        return Response(xml, mimetype="application/xml")

    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("Database initialized.")

    @app.cli.command("create-admin")
    def create_admin_command():
        from services.auth import create_admin, get_admin_by_email
        email = app.config["ADMIN_EMAIL"]
        password = app.config["ADMIN_PASSWORD"]
        if get_admin_by_email(email):
            print(f"Admin {email} already exists.")
            return
        create_admin(email, password, "Studio Admin")
        print(f"Admin account created: {email}")

    return app


def ensure_bootstrapped(app):
    """Create tables and a first admin account on first run, using env vars."""
    with app.app_context():
        init_db()
        from services.auth import create_admin, get_admin_by_email
        email = app.config["ADMIN_EMAIL"]
        password = app.config["ADMIN_PASSWORD"]
        if not get_admin_by_email(email):
            create_admin(email, password, "Studio Admin")


app = create_app()
ensure_bootstrapped(app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "0") == "1")
