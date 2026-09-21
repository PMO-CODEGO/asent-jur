from flask import render_template, request, flash, redirect, session, url_for, current_app, Blueprint
from app.services.auth_service import AuthService
from app.utils.decorators import role_required
from app.services.log_service import gravar_log

auth_user_bp = Blueprint("auth_user", __name__)

DEPARTAMENTOS_POR_ROLE = {
    'admin': {'Gestor - Assentamento', 'Gestor - Jurídico', 'Administrador',
              'Usuário - Assentamento', 'Usuário - Jurídico'},
    'assent_gestor': {'Usuário - Assentamento'},
    'jur_gestor': {'Usuário - Jurídico'},
}


@auth_user_bp.route('/registrar-usuario', methods=['GET', 'POST'])
@role_required('admin', 'assent_gestor', 'jur_gestor')
def registrar_usuario():
    if request.method == 'POST':
        try:
            departamento = request.form.get('departamento', '').strip()
            if departamento not in DEPARTAMENTOS_POR_ROLE[session.get('role')]:
                raise ValueError('Você não tem permissão para criar usuários nesse departamento.')
            AuthService.registrar_usuario(request.form)
            novo_username = request.form.get('username', '').strip()
            gravar_log('USUARIO_CRIADO', f"Novo usuário registrado: '{novo_username}'")
            flash('Usuário registrado com sucesso!', 'success')
            return redirect(url_for('auth_login.login'))

        except ValueError as e:
            flash(str(e), 'danger')

        except Exception as e:
            current_app.logger.error(f"Erro ao registrar usuário: {str(e)}")
            flash('Erro interno. Contate o administrador.', 'danger')

    return render_template('registrar_usuario.html')

@auth_user_bp.route('/registrar-colaborador')
@role_required('assent_gestor', 'jur_gestor', 'admin') # Garantindo que só gestores acessem
def registrar_colaborador():
    role = session.get('role')
    
    # Define o departamento automático baseado na role do gestor
    if role == 'jur_gestor':
        depto_predefinido = "Usuário - Jurídico"
    elif role == 'assent_gestor':
        depto_predefinido = "Usuário - Assentamento"
    else:
        # Se for admin acessando por aqui, podemos deixar um padrão ou redirecionar
        depto_predefinido = "Administrador"
        
    return render_template('registrar_colaborador.html', depto=depto_predefinido)