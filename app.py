"""
SAR-INVENTORY - Aplicación Principal
=====================================
Punto de entrada del sistema de gestión de inventario SAR.
Inicializa Flask, registra blueprints y carga datos iniciales.
"""

import os
from datetime import datetime, timedelta, timezone
from flask import Flask, redirect, url_for, render_template, session, request
from flask_login import LoginManager, current_user, login_required
from werkzeug.security import generate_password_hash

from config import Config
from models import db, Usuario, Equipo, Movimiento
from auth import auth_bp
from crud import inventario_bp
from reportes_logic import reportes_bp


def create_app():
    """Factory para crear y configurar la aplicación Flask."""

    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)

    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Inicie sesión para acceder al sistema.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(reportes_bp)

    # ==========================================================================
    # MIDDLEWARE - Control de sesión
    # ==========================================================================

    @app.before_request
    def before_request():
        """Verifica timeout de sesión y refresca la marca de tiempo."""
        # Excluir rutas estáticas y de login
        if request.endpoint and request.endpoint in ('auth.login', 'static'):
            return

        if current_user.is_authenticated:
            session.permanent = True
            ultimo_actividad = session.get('last_activity')

            if ultimo_actividad:
                try:
                    ultima = datetime.fromisoformat(ultimo_actividad)
                    timeout = app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(minutes=30))
                    if isinstance(timeout, timedelta):
                        if datetime.now(timezone.utc) - ultima > timeout:
                            from flask_login import logout_user
                            logout_user()
                            from flask import flash
                            flash('Su sesión ha expirado por inactividad.', 'warning')
                            return redirect(url_for('auth.login'))
                except (ValueError, TypeError):
                    pass

            session['last_activity'] = datetime.now(timezone.utc).isoformat()

    # ==========================================================================
    # RUTAS PRINCIPALES
    # ==========================================================================

    @app.route('/')
    def index():
        """Redirige a la página de inicio de sesión."""
        if current_user.is_authenticated:
            return redirect(url_for('inventario.dashboard'))
        return redirect(url_for('auth.login'))

    @app.route('/ayuda')
    @login_required
    def ayuda():
        """Renderiza la página del manual de ayuda."""
        return render_template('ayuda.html')

    # ==========================================================================
    # INICIALIZACIÓN DE BASE DE DATOS Y DATOS SEMILLA
    # ==========================================================================

    with app.app_context():
        db.create_all()
        _seed_data()


    return app
def _seed_data():
    """
    Carga datos iniciales en la base de datos si está vacía.
    Crea usuarios predeterminados, equipos de muestra y movimientos de ejemplo.
    """
    # Solo sembrar si no hay usuarios (primera ejecución)
    if Usuario.query.first() is not None:
        return

    # ---- Usuarios predeterminados ----
    usuarios = [
        Usuario(
            nombre_completo='Administrador General',
            grado_cargo='Administrador del Sistema',
            nombre_usuario='admin',
            contraseña_hash=generate_password_hash('admin123'),
            rol='Administrador'
        ),
        Usuario(
            nombre_completo='Juan Pérez',
            grado_cargo='Sargento Primero',
            nombre_usuario='jperez',
            contraseña_hash=generate_password_hash('log123'),
            rol='Logística'
        ),
        Usuario(
            nombre_completo='María López',
            grado_cargo='Cabo Primero',
            nombre_usuario='mlopez',
            contraseña_hash=generate_password_hash('con123'),
            rol='Consulta'
        ),
    ]

    for u in usuarios:
        db.session.add(u)

    db.session.flush()  # Para obtener los IDs generados

    # ---- Equipos de muestra ----
    equipos_data = [
        ('CAM-001', 'Camilla Rígida', 8, 'Bueno', 'Primeros Auxilios'),
        ('CAM-002', 'Camilla Flexible', 5, 'Regular', 'Primeros Auxilios'),
        ('BOT-001', 'Botiquín de Emergencia', 12, 'Bueno', 'Primeros Auxilios'),
        ('DEF-001', 'Desfibrilador Portátil', 2, 'Bueno', 'Primeros Auxilios'),
        ('MOT-001', 'Motor Fuera de Borda 15HP', 3, 'Bueno', 'Rescate Acuático'),
        ('MOT-002', 'Motor Fuera de Borda 40HP', 1, 'Malo', 'Rescate Acuático'),
        ('CHA-001', 'Chaleco Salvavidas', 25, 'Bueno', 'Rescate Acuático'),
        ('BOT-002', 'Bote Inflable', 4, 'Regular', 'Rescate Acuático'),
        ('CUE-001', 'Cuerdas de Rescate 50m', 10, 'Bueno', 'Rescate Terrestre'),
        ('ARN-001', 'Arnés de Seguridad', 6, 'Regular', 'Rescate Terrestre'),
        ('CAR-001', 'Carpa de Comando', 3, 'Bueno', 'Logística'),
        ('GEN-001', 'Generador Eléctrico', 2, 'Malo', 'Logística'),
        ('RAD-001', 'Radio Portátil VHF', 15, 'Bueno', 'Comunicaciones'),
        ('RAD-002', 'Radio Base UHF', 1, 'Regular', 'Comunicaciones'),
        ('CAS-001', 'Casco de Protección', 20, 'Bueno', 'Protección Personal'),
    ]

    equipos = []
    for codigo, nombre, cantidad, estado, categoria in equipos_data:
        equipo = Equipo(
            codigo=codigo,
            nombre=nombre,
            cantidad=cantidad,
            estado=estado,
            categoria=categoria
        )
        db.session.add(equipo)
        equipos.append(equipo)

    db.session.flush()

    # ---- Movimientos de ejemplo ----
    admin_user = usuarios[0]
    logistica_user = usuarios[1]

    movimientos_ejemplo = [
        Movimiento(
            usuario_id=admin_user.id,
            accion='Agregó',
            equipo_codigo='CAM-001',
            equipo_nombre='Camilla Rígida',
            detalle='Registro inicial del equipo: Camilla Rígida (8 unidades, Estado: Bueno)',
            fecha=datetime.now(timezone.utc) - timedelta(days=7)
        ),
        Movimiento(
            usuario_id=admin_user.id,
            accion='Agregó',
            equipo_codigo='BOT-001',
            equipo_nombre='Botiquín de Emergencia',
            detalle='Registro inicial del equipo: Botiquín de Emergencia (12 unidades, Estado: Bueno)',
            fecha=datetime.now(timezone.utc) - timedelta(days=6)
        ),
        Movimiento(
            usuario_id=logistica_user.id,
            accion='Modificó',
            equipo_codigo='MOT-002',
            equipo_nombre='Motor Fuera de Borda 40HP',
            detalle='Cambios realizados: Estado: "Regular" → "Malo"; Cantidad: 2 → 1',
            fecha=datetime.now(timezone.utc) - timedelta(days=5)
        ),
        Movimiento(
            usuario_id=logistica_user.id,
            accion='Agregó',
            equipo_codigo='CHA-001',
            equipo_nombre='Chaleco Salvavidas',
            detalle='Registro inicial del equipo: Chaleco Salvavidas (25 unidades, Estado: Bueno)',
            fecha=datetime.now(timezone.utc) - timedelta(days=4)
        ),
        Movimiento(
            usuario_id=admin_user.id,
            accion='Modificó',
            equipo_codigo='GEN-001',
            equipo_nombre='Generador Eléctrico',
            detalle='Cambios realizados: Estado: "Regular" → "Malo"',
            fecha=datetime.now(timezone.utc) - timedelta(days=3)
        ),
        Movimiento(
            usuario_id=logistica_user.id,
            accion='Agregó',
            equipo_codigo='RAD-001',
            equipo_nombre='Radio Portátil VHF',
            detalle='Registro inicial del equipo: Radio Portátil VHF (15 unidades, Estado: Bueno)',
            fecha=datetime.now(timezone.utc) - timedelta(days=2)
        ),
        Movimiento(
            usuario_id=admin_user.id,
            accion='Modificó',
            equipo_codigo='ARN-001',
            equipo_nombre='Arnés de Seguridad',
            detalle='Cambios realizados: Cantidad: 8 → 6; Estado: "Bueno" → "Regular"',
            fecha=datetime.now(timezone.utc) - timedelta(days=1)
        ),
    ]

    for m in movimientos_ejemplo:
        db.session.add(m)

    db.session.commit()
    print('Base de datos inicializada con datos de ejemplo.')
    print('   Usuarios creados:')
    print('   - admin / admin123 (Administrador)')
    print('   - jperez / log123 (Logística)')
    print('   - mlopez / con123 (Consulta)')
    print(f'   - {len(equipos)} equipos registrados')
    print(f'   - {len(movimientos_ejemplo)} movimientos de ejemplo')


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
