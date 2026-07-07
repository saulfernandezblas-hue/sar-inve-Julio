"""
SAR-INVENTORY - Módulo de Autenticación
=======================================
Blueprint para inicio de sesión, cierre de sesión y control de acceso.
"""

from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import db, Usuario

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Maneja la autenticación de usuarios.
    GET: Muestra el formulario de inicio de sesión.
    POST: Procesa las credenciales y autentica al usuario.
    """
    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('inventario.dashboard'))

    if request.method == 'POST':
        nombre_usuario = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Validar que se proporcionaron credenciales
        if not nombre_usuario or not password:
            flash('Por favor ingrese usuario y contraseña.', 'warning')
            return render_template('login.html')

        # Buscar usuario en la base de datos
        usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()

        if not usuario:
            flash('Usuario o contraseña incorrectos.', 'danger')
            return render_template('login.html')

        # Verificar si el usuario está activo
        if usuario.estado != 'Activo':
            flash('Su cuenta está inactiva. Contacte al administrador.', 'danger')
            return render_template('login.html')

        # Verificar si el usuario está bloqueado por intentos fallidos
        if usuario.bloqueado_hasta and usuario.bloqueado_hasta > datetime.now(timezone.utc):
            tiempo_restante = (usuario.bloqueado_hasta - datetime.now(timezone.utc)).seconds
            minutos = tiempo_restante // 60
            segundos = tiempo_restante % 60
            flash(
                f'Cuenta bloqueada por demasiados intentos fallidos. '
                f'Intente nuevamente en {minutos}m {segundos}s.',
                'danger'
            )
            return render_template('login.html')

        # Si el bloqueo ya expiró, resetear
        if usuario.bloqueado_hasta and usuario.bloqueado_hasta <= datetime.now(timezone.utc):
            usuario.bloqueado_hasta = None
            usuario.intentos_fallidos = 0
            db.session.commit()

        # Verificar contraseña
        if check_password_hash(usuario.contraseña_hash, password):
            # Autenticación exitosa
            usuario.ultimo_acceso = datetime.now(timezone.utc)
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
            db.session.commit()

            login_user(usuario)
            flash(f'Bienvenido, {usuario.nombre_completo}.', 'success')

            # Redirigir a la página solicitada o al dashboard
            next_page = request.args.get('next')
            # Validar que sea una URL interna para evitar open redirect
            if next_page and urlparse(next_page).netloc != '':
                next_page = None
            return redirect(next_page or url_for('inventario.dashboard'))
        else:
            # Contraseña incorrecta
            usuario.intentos_fallidos += 1
            max_intentos = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
            lockout_time = current_app.config.get('LOCKOUT_TIME', 300)

            if usuario.intentos_fallidos >= max_intentos:
                usuario.bloqueado_hasta = datetime.now(timezone.utc) + timedelta(seconds=lockout_time)
                db.session.commit()
                flash(
                    f'Cuenta bloqueada por {lockout_time // 60} minutos '
                    f'debido a {max_intentos} intentos fallidos.',
                    'danger'
                )
            else:
                intentos_restantes = max_intentos - usuario.intentos_fallidos
                db.session.commit()
                flash(
                    f'Usuario o contraseña incorrectos. '
                    f'Intentos restantes: {intentos_restantes}.',
                    'danger'
                )

            return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Cierra la sesión del usuario actual y redirige al login."""
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))
