from flask import Flask, flash, redirect, request
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFError
from app.extensions import bcrypt, csrf
from app.config import Config
from app.services.guia_service import obter_guia

def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.config.from_object(Config)

    bcrypt.init_app(app)
    csrf.init_app(app)

    app.jinja_env.globals['guia_dicas'] = obter_guia

    @app.errorhandler(CSRFError)
    def erro_csrf(e):
        flash('Sua sessão expirou ou o formulário é inválido. Tente novamente.', 'danger')
        return redirect(request.referrer or '/')

    # registrar blueprints
    from app.routes.auth_login import auth_login_bp
    from app.routes.auth_password import auth_password_bp
    from app.routes.auth_user import auth_user_bp
    from app.routes.cadastro import cadastro_bp
    from app.routes.relatorios import relatorio_bp
    from app.routes.logs import logs_bp
    from app.routes.edicao import edicao_bp
    from app.routes.juridico import juridico_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.areas_brutas import areas_brutas_bp
    from app.routes.areas_brutas_parceladas import areas_brutas_parceladas_bp
    from app.routes.cadastro_modulos import cadastro_modulos_bp

    app.register_blueprint(auth_login_bp)
    app.register_blueprint(auth_password_bp)
    app.register_blueprint(auth_user_bp)
    app.register_blueprint(cadastro_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(edicao_bp)
    app.register_blueprint(juridico_bp)
    app.register_blueprint(areas_brutas_bp)
    app.register_blueprint(areas_brutas_parceladas_bp)
    app.register_blueprint(cadastro_modulos_bp)

    return app
