import os
from datetime import datetime
from flask import Flask, render_template
from sqlalchemy import create_engine
from config import Config
from models import db
from models.user import User
from models.income import Income
from models.expense import Expense
from models.budget import Budget

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.income import income_bp
from routes.expenses import expenses_bp
from routes.budgets import budgets_bp
from routes.reports import reports_bp

def determine_db_uri():
    if Config.DB_TYPE == 'sqlite':
        return Config.SQLITE_URI

    # Attempt connection to MySQL server
    try:
        engine = create_engine(Config.MYSQL_URI, connect_args={'connect_timeout': 3})
        with engine.connect() as conn:
            pass
        print("Connected to MySQL server successfully.")
        return Config.MYSQL_URI
    except Exception as e:
        print(f"Notice: MySQL connection check ({e}). Using SQLite database for server session...")
        return Config.SQLITE_URI

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Determine valid database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = determine_db_uri()

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(reports_bp)

    # Inject global date string into Jinja2 templates
    @app.context_processor
    def inject_global_vars():
        return {
            'now_str': datetime.utcnow().strftime('%B %d, %Y')
        }

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('base.html'), 500

    # Auto-initialize database tables
    with app.app_context():
        db.create_all()
        print(f"Database tables ready using: {app.config['SQLALCHEMY_DATABASE_URI']}")

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
