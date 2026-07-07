"""
SAR-INVENTORY - Utilidades del Sistema
======================================
Decoradores de autorización y funciones auxiliares.
"""

from functools import wraps
from flask import jsonify, redirect, url_for, flash, request
from flask_login import current_user
from models import db, Movimiento


def admin_required(f):
    """
    Decorador que restringe el acceso a usuarios con rol 'Administrador'.
    Para rutas API retorna JSON 403; para rutas web redirige con flash.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Autenticación requerida.'}), 401
            return redirect(url_for('auth.login'))

        if current_user.rol != 'Administrador':
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'message': 'Acceso denegado. Se requiere rol de Administrador.'
                }), 403
            flash('Acceso denegado. Se requiere rol de Administrador.', 'danger')
            return redirect(url_for('inventario.dashboard'))

        return f(*args, **kwargs)
    return decorated_function


def logistica_required(f):
    """
    Decorador que restringe el acceso a usuarios con rol 'Administrador' o 'Logística'.
    El rol 'Consulta' es de solo lectura y no puede modificar datos.
    Para rutas API retorna JSON 403; para rutas web redirige con flash.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Autenticación requerida.'}), 401
            return redirect(url_for('auth.login'))

        if current_user.rol not in ['Administrador', 'Logística']:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'message': 'Acceso denegado. Se requiere rol de Administrador o Logística.'
                }), 403
            flash('Acceso denegado. Se requiere rol de Administrador o Logística.', 'danger')
            return redirect(url_for('inventario.dashboard'))

        return f(*args, **kwargs)
    return decorated_function


def registrar_movimiento(usuario_id, accion, equipo_codigo, equipo_nombre, detalle):
    """
    Registra un movimiento de auditoría en el sistema.

    Args:
        usuario_id: ID del usuario que realiza la acción.
        accion: Tipo de acción ('Agregó', 'Modificó', 'Eliminó').
        equipo_codigo: Código del equipo afectado.
        equipo_nombre: Nombre del equipo afectado.
        detalle: Descripción detallada de los cambios realizados.
    """
    movimiento = Movimiento(
        usuario_id=usuario_id,
        accion=accion,
        equipo_codigo=equipo_codigo,
        equipo_nombre=equipo_nombre,
        detalle=detalle
    )
    db.session.add(movimiento)
    db.session.flush()
