# __init__.py is a special Python file that allows a directory to become
# a Python package so it can be accessed using the 'import' statement.

import os
from flask import Flask
from flask_mail import Mail
from flask_migrate import Migrate
from flask_user import UserManager, current_user
from flask_gravatar import Gravatar
from flask_wtf.csrf import CSRFProtect
from .models.db import db
from .models.bot_models import Bots, Conversations, Messages
from .models.user_models import User, Role
from .models.site_models import Site
import datetime
from .views import register_blueprints
from app.common.extensions import cache
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_socketio import SocketIO
from .distributed_manager.manager import init_handlers
from .logging_config.logging_config import init_prod_logging, init_dev_logging

# Instantiate Flask extensions
csrf_protect = CSRFProtect()

mail = Mail()
migrate = Migrate()
gravatar = None


def init_data():
    """Initialize site data"""

    # first flush all bots data
    all_bots = Bots.query.all()
    for bot in all_bots:
        db.session.delete(bot)
        db.session.commit()

    if not Site.query.filter(Site.site_name == os.getenv("INIT_SITE_NAME")).first():
        Site.create(
            site_name=os.getenv("INIT_SITE_NAME"),
            site_description="This is a currently ongoing project of building \
            distributed Rasa chatbots with Ray distributed functions library, \
            hence the project name Raysa.",
            site_visitors_total_count=0,
        )

    if not Bots.query.filter(Bots.bot_name == os.getenv("INIT_BOT_NAME1")).first():
        Bots.create(
            bot_name=os.getenv("INIT_BOT_NAME1"),
            bot_description=os.getenv("INIT_BOT_DESCRIPTION"),
            bot_added_at=datetime.datetime.utcnow(),
            vm_name=os.getenv("INIT_VM_NAME_1"),
            vm_type=os.getenv("INIT_VM_TYPE_1"),
            vm_res_group=os.getenv("INIT_VM_RES_GROUP1"),
            vm_ip=os.getenv("INIT_VM_IP_1"),
            vm_vcpu=os.getenv("INIT_VM_VCPU1"),
            vm_region=os.getenv("INIT_VM_REGION"),
            vm_ram=os.getenv("INIT_VM_RAM1"),
        )

    if not Bots.query.filter(Bots.bot_name == os.getenv("INIT_BOT_NAME2")).first():
        Bots.create(
            bot_name=os.getenv("INIT_BOT_NAME2"),
            bot_description=os.getenv("INIT_BOT_DESCRIPTION"),
            bot_added_at=datetime.datetime.utcnow(),
            vm_name=os.getenv("INIT_VM_NAME_2"),
            vm_type=os.getenv("INIT_VM_TYPE_2"),
            vm_res_group=os.getenv("INIT_VM_RES_GROUP2"),
            vm_ip=os.getenv("INIT_VM_IP_2"),
            vm_vcpu=os.getenv("INIT_VM_VCPU2"),
            vm_region=os.getenv("INIT_VM_REGION"),
            vm_ram=os.getenv("INIT_VM_RAM2"),
        )

    if not Bots.query.filter(Bots.bot_name == os.getenv("INIT_BOT_NAME3")).first():
        Bots.create(
            bot_name=os.getenv("INIT_BOT_NAME3"),
            bot_description=os.getenv("INIT_BOT_DESCRIPTION"),
            bot_added_at=datetime.datetime.utcnow(),
            vm_name=os.getenv("INIT_VM_NAME_3"),
            vm_type=os.getenv("INIT_VM_TYPE_3"),
            vm_res_group=os.getenv("INIT_VM_RES_GROUP3"),
            vm_ip=os.getenv("INIT_VM_IP_3"),
            vm_vcpu=os.getenv("INIT_VM_VCPU3"),
            vm_region=os.getenv("INIT_VM_REGION"),
            vm_ram=os.getenv("INIT_VM_RAM3"),
        )


# Initialize Flask Application
def create_app(extra_config_settings={}):
    """Create a Flask application.
    """
    # Instantiate Flask
    app = Flask(__name__)

    # Load common settings
    app.config.from_object("app.settings")
    # Load environment specific settings
    app.config.from_object("app.local_settings")

    # Load .env file if in PRODUCTION
    if app.config["DEBUG"] is False:
        from dotenv import load_dotenv

        load_dotenv(".env")

    # Load extra settings from extra_config_settings param
    app.config.update(extra_config_settings)

    app.config["FLASK_ADMIN_SWATCH"] = "cerulean"

    # Initalize app as socketio instance
    socketio = SocketIO(app, cors_allowed_origins="http://127.0.0.1:5000")
    init_handlers(socketio)

    if app.config["DEBUG"] is False:
        init_prod_logging()
    else:
        init_dev_logging()

    admin = Admin(app, name="Raysa", template_mode="bootstrap3")
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Bots, db.session))
    admin.add_view(ModelView(Conversations, db.session))
    admin.add_view(ModelView(Messages, db.session))
    cache.init_app(app)

    # Setup Flask-SQLAlchemy
    db.init_app(app)
    # db.create_all()

    global gravatar
    gravatar = Gravatar(
        app,
        size=100,
        rating="g",
        default="retro",
        force_default=False,
        use_ssl=False,
        base_url=None,
    )
    # Setup Flask-Migrate
    migrate.init_app(app, db)
    with app.app_context():
        db.create_all()
    # Setup Flask-Mail
    mail.init_app(app)

    # Setup WTForms CSRFProtect
    csrf_protect.init_app(app)

    # Register blueprints
    register_blueprints(app)

    # Define bootstrap_is_hidden_field for flask-bootstrap's bootstrap_wtf.html
    from wtforms.fields import HiddenField

    def is_hidden_field_filter(field):
        return isinstance(field, HiddenField)

    app.jinja_env.globals["bootstrap_is_hidden_field"] = is_hidden_field_filter

    # Setup an error-logger to send emails to app.config.ADMINS
    init_email_error_handler(app)

    # Setup Flask-User to handle user account related forms
    # from .models.user_models import User, Role
    # from .views.main_views import user_profile_page

    # Setup Flask-User
    user_manager = UserManager(app, db, User)

    # Create 'admin@example.com' user with 'Admin' and 'Agent' roles

    with app.app_context():
        init_data()
        if not User.query.filter(User.email == app.config["MAIL_USERNAME"]).first():
            user = User(
                email=app.config["MAIL_USERNAME"],
                email_confirmed_at=datetime.datetime.utcnow(),
                password=user_manager.hash_password(app.config["MAIL_PASSWORD"]),
                active=True,
                first_name="Svetozar",
                last_name="Stojanovic",
            )

            user.roles.append(Role(name="Admin"))
            user.roles.append(Role(name="Agent"))
            db.session.add(user)
            db.session.commit()

    @app.context_processor
    def context_processor():
        return dict(user_manager=user_manager)

    @app.context_processor
    def inject_user():
        return dict(user=current_user)

    return app, socketio


def init_email_error_handler(app):
    """
    Initialize a logger to send emails on error-level messages.
    Unhandled exceptions will now send an email message to app.config.ADMINS.
    """
    if app.debug:
        return  # Do not send error emails while developing

    # Retrieve email settings from app.config
    host = app.config["MAIL_SERVER"]
    port = app.config["MAIL_PORT"]
    from_addr = app.config["MAIL_DEFAULT_SENDER"]
    username = app.config["MAIL_USERNAME"]
    password = app.config["MAIL_PASSWORD"]
    secure = () if app.config.get("MAIL_USE_TLS") else None

    # Retrieve app settings from app.config
    to_addr_list = app.config["ADMINS"]
    subject = app.config.get("APP_SYSTEM_ERROR_SUBJECT_LINE", "System Error")

    # Setup an SMTP mail handler for error-level messages
    import logging
    from logging.handlers import SMTPHandler

    mail_handler = SMTPHandler(
        mailhost=(host, port),  # Mail host and port
        fromaddr=from_addr,  # From address
        toaddrs=to_addr_list,  # To address
        subject=subject,  # Subject line
        credentials=(username, password),  # Credentials
        secure=secure,
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

    # Log errors using: app.logger.error('Some error message')
