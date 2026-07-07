"""
SAR-INVENTORY - Módulo CRUD de Inventario y Usuarios
=====================================================
Blueprint para la gestión completa de equipos y administración de usuarios.
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, Equipo, Usuario, Movimiento
from utils import admin_required, logistica_required, registrar_movimiento

inventario_bp = Blueprint('inventario', __name__)


# =============================================================================
# VISTAS DE PÁGINAS
# =============================================================================

@inventario_bp.route('/dashboard')
@login_required
def dashboard():
    """Renderiza la página principal del dashboard."""
    return render_template('dashboard.html')


@inventario_bp.route('/inventario')
@login_required
def inventario():
    """Renderiza la página de gestión de inventario."""
    return render_template('inventario.html')


@inventario_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    """Renderiza la página de administración de usuarios (solo administradores)."""
    return render_template('usuarios.html')


# =============================================================================
# API DE EQUIPOS
# =============================================================================

@inventario_bp.route('/api/equipos', methods=['GET'])
@login_required
def listar_equipos():
    """
    Retorna la lista paginada de equipos con soporte para filtros.
    Query params: search, estado, categoria, page, per_page.
    """
    search = request.args.get('search', '').strip()
    estado = request.args.get('estado', '').strip()
    categoria = request.args.get('categoria', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Limitar per_page para evitar consultas abusivas
    per_page = min(per_page, 100)

    query = Equipo.query

    # Filtro de búsqueda por código o nombre
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Equipo.codigo.ilike(search_filter),
                Equipo.nombre.ilike(search_filter)
            )
        )

    # Filtro por estado
    if estado and estado.lower() not in ('', 'todos'):
        query = query.filter(Equipo.estado == estado)

    # Filtro por categoría
    if categoria and categoria.lower() not in ('', 'todas'):
        query = query.filter(Equipo.categoria == categoria)

    # Ordenar por código
    query = query.order_by(Equipo.codigo.asc())

    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'equipos': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    })


@inventario_bp.route('/api/equipos/<int:id>', methods=['GET'])
@login_required
def obtener_equipo(id):
    """Retorna un equipo específico por su ID."""
    equipo = Equipo.query.get(id)
    if not equipo:
        return jsonify({'success': False, 'message': 'Equipo no encontrado.'}), 404
    return jsonify({'success': True, 'equipo': equipo.to_dict()})


@inventario_bp.route('/api/equipos', methods=['POST'])
@login_required
@logistica_required
def crear_equipo():
    """
    Crea un nuevo equipo en el inventario.
    Requiere rol de Administrador o Logística.
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No se recibieron datos.'}), 400

    # Validar campos requeridos
    campos_requeridos = ['codigo', 'nombre', 'cantidad', 'estado', 'categoria']
    for campo in campos_requeridos:
        if not data.get(campo) and data.get(campo) != 0:
            return jsonify({
                'success': False,
                'message': f'El campo "{campo}" es requerido.'
            }), 400

    codigo = data['codigo'].strip().upper()
    nombre = data['nombre'].strip()
    estado = data['estado'].strip()
    categoria = data['categoria'].strip()

    # Validar cantidad como entero positivo
    try:
        cantidad = int(data['cantidad'])
        if cantidad < 0:
            return jsonify({
                'success': False,
                'message': 'La cantidad debe ser un número positivo.'
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'message': 'La cantidad debe ser un número entero válido.'
        }), 400

    # Validar estado
    estados_validos = ['Bueno', 'Regular', 'Malo']
    if estado not in estados_validos:
        return jsonify({
            'success': False,
            'message': f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}.'
        }), 400

    # Verificar código único
    if Equipo.query.filter_by(codigo=codigo).first():
        return jsonify({
            'success': False,
            'message': f'Ya existe un equipo con el código "{codigo}".'
        }), 409

    # Crear el equipo
    equipo = Equipo(
        codigo=codigo,
        nombre=nombre,
        cantidad=cantidad,
        estado=estado,
        categoria=categoria
    )
    db.session.add(equipo)
    db.session.commit()

    # Registrar movimiento de auditoría
    registrar_movimiento(
        usuario_id=current_user.id,
        accion='Agregó',
        equipo_codigo=equipo.codigo,
        equipo_nombre=equipo.nombre,
        detalle=f'Nuevo equipo registrado: {equipo.nombre} (Código: {equipo.codigo}, '
                f'Cantidad: {equipo.cantidad}, Estado: {equipo.estado}, '
                f'Categoría: {equipo.categoria})'
    )

    return jsonify({
        'success': True,
        'message': f'Equipo "{equipo.nombre}" registrado exitosamente.',
        'equipo': equipo.to_dict()
    }), 201


@inventario_bp.route('/api/equipos/<int:id>', methods=['PUT'])
@login_required
@logistica_required
def actualizar_equipo(id):
    """
    Actualiza un equipo existente.
    Requiere rol de Administrador o Logística.
    """
    equipo = Equipo.query.get(id)
    if not equipo:
        return jsonify({'success': False, 'message': 'Equipo no encontrado.'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No se recibieron datos.'}), 400

    # Rastrear cambios para el detalle del movimiento
    cambios = []

    if 'nombre' in data and data['nombre'].strip():
        nuevo_nombre = data['nombre'].strip()
        if equipo.nombre != nuevo_nombre:
            cambios.append(f'Nombre: "{equipo.nombre}" → "{nuevo_nombre}"')
            equipo.nombre = nuevo_nombre

    if 'cantidad' in data:
        try:
            nueva_cantidad = int(data['cantidad'])
            if nueva_cantidad < 0:
                return jsonify({
                    'success': False,
                    'message': 'La cantidad debe ser un número positivo.'
                }), 400
            if equipo.cantidad != nueva_cantidad:
                cambios.append(f'Cantidad: {equipo.cantidad} → {nueva_cantidad}')
                equipo.cantidad = nueva_cantidad
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'La cantidad debe ser un número entero válido.'
            }), 400

    if 'estado' in data and data['estado'].strip():
        nuevo_estado = data['estado'].strip()
        estados_validos = ['Bueno', 'Regular', 'Malo']
        if nuevo_estado not in estados_validos:
            return jsonify({
                'success': False,
                'message': f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}.'
            }), 400
        if equipo.estado != nuevo_estado:
            cambios.append(f'Estado: "{equipo.estado}" → "{nuevo_estado}"')
            equipo.estado = nuevo_estado

    if 'categoria' in data and data['categoria'].strip():
        nueva_categoria = data['categoria'].strip()
        if equipo.categoria != nueva_categoria:
            cambios.append(f'Categoría: "{equipo.categoria}" → "{nueva_categoria}"')
            equipo.categoria = nueva_categoria

    if not cambios:
        return jsonify({
            'success': True,
            'message': 'No se detectaron cambios.',
            'equipo': equipo.to_dict()
        })

    equipo.fecha_modificacion = datetime.now(timezone.utc)
    db.session.commit()

    # Registrar movimiento con detalle de los cambios
    registrar_movimiento(
        usuario_id=current_user.id,
        accion='Modificó',
        equipo_codigo=equipo.codigo,
        equipo_nombre=equipo.nombre,
        detalle=f'Cambios realizados: {"; ".join(cambios)}'
    )

    return jsonify({
        'success': True,
        'message': f'Equipo "{equipo.nombre}" actualizado exitosamente.',
        'equipo': equipo.to_dict()
    })


@inventario_bp.route('/api/equipos/<int:id>', methods=['DELETE'])
@login_required
@logistica_required
def eliminar_equipo(id):
    """
    Elimina un equipo del inventario.
    Requiere rol de Administrador o Logística.
    """
    equipo = Equipo.query.get(id)
    if not equipo:
        return jsonify({'success': False, 'message': 'Equipo no encontrado.'}), 404

    codigo = equipo.codigo
    nombre = equipo.nombre

    db.session.delete(equipo)
    db.session.commit()

    # Registrar movimiento de eliminación
    registrar_movimiento(
        usuario_id=current_user.id,
        accion='Eliminó',
        equipo_codigo=codigo,
        equipo_nombre=nombre,
        detalle=f'Equipo eliminado: {nombre} (Código: {codigo})'
    )

    return jsonify({
        'success': True,
        'message': f'Equipo "{nombre}" eliminado exitosamente.'
    })


# =============================================================================
# API DEL DASHBOARD
# =============================================================================

@inventario_bp.route('/api/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    """
    Retorna estadísticas completas del inventario para el dashboard.
    Incluye conteos por estado, alertas, distribución por categoría y últimos movimientos.
    """
    total_equipos = Equipo.query.count()

    # Conteos por estado
    buenos = Equipo.query.filter_by(estado='Bueno').count()
    regulares = Equipo.query.filter_by(estado='Regular').count()
    malos = Equipo.query.filter_by(estado='Malo').count()

    # Calcular porcentajes (evitar división por cero)
    def porcentaje(valor):
        return round((valor / total_equipos * 100), 1) if total_equipos > 0 else 0

    # Equipos en alerta: estado 'Malo' o cantidad menor a 3
    alertas_query = Equipo.query.filter(
        db.or_(
            Equipo.estado == 'Malo',
            Equipo.cantidad < 3
        )
    ).all()

    # Distribución por categoría
    categorias = db.session.query(
        Equipo.categoria,
        db.func.count(Equipo.id).label('cantidad')
    ).group_by(Equipo.categoria).order_by(Equipo.categoria).all()

    # Últimos 10 movimientos
    ultimos_movimientos = Movimiento.query.order_by(
        Movimiento.fecha.desc()
    ).limit(10).all()

    return jsonify({
        'total_equipos': total_equipos,
        'buenos': {
            'cantidad': buenos,
            'porcentaje': porcentaje(buenos)
        },
        'regulares': {
            'cantidad': regulares,
            'porcentaje': porcentaje(regulares)
        },
        'malos': {
            'cantidad': malos,
            'porcentaje': porcentaje(malos)
        },
        'alertas': [e.to_dict() for e in alertas_query],
        'por_categoria': [
            {'categoria': c[0], 'cantidad': c[1]} for c in categorias
        ],
        'ultimos_movimientos': [m.to_dict() for m in ultimos_movimientos]
    })


# =============================================================================
# API DE USUARIOS
# =============================================================================

@inventario_bp.route('/api/usuarios', methods=['GET'])
@login_required
@admin_required
def listar_usuarios():
    """Retorna la lista completa de usuarios (solo administradores)."""
    usuarios = Usuario.query.order_by(Usuario.nombre_completo).all()
    return jsonify({
        'usuarios': [u.to_dict() for u in usuarios]
    })


@inventario_bp.route('/api/usuarios', methods=['POST'])
@login_required
@admin_required
def crear_usuario():
    """
    Crea un nuevo usuario en el sistema.
    Solo accesible para administradores.
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No se recibieron datos.'}), 400

    # Validar campos requeridos
    campos_requeridos = ['nombre_completo', 'grado_cargo', 'nombre_usuario', 'password', 'rol']
    for campo in campos_requeridos:
        if not data.get(campo, '').strip():
            return jsonify({
                'success': False,
                'message': f'El campo "{campo}" es requerido.'
            }), 400

    nombre_completo = data['nombre_completo'].strip()
    grado_cargo = data['grado_cargo'].strip()
    nombre_usuario = data['nombre_usuario'].strip()
    password = data['password'].strip()
    rol = data['rol'].strip()

    # Validar rol
    roles_validos = ['Administrador', 'Logística', 'Consulta']
    if rol not in roles_validos:
        return jsonify({
            'success': False,
            'message': f'Rol inválido. Debe ser uno de: {", ".join(roles_validos)}.'
        }), 400

    # Verificar nombre de usuario único
    if Usuario.query.filter_by(nombre_usuario=nombre_usuario).first():
        return jsonify({
            'success': False,
            'message': f'El nombre de usuario "{nombre_usuario}" ya está en uso.'
        }), 409

    # Validar longitud de contraseña
    if len(password) < 4:
        return jsonify({
            'success': False,
            'message': 'La contraseña debe tener al menos 4 caracteres.'
        }), 400

    # Crear usuario
    usuario = Usuario(
        nombre_completo=nombre_completo,
        grado_cargo=grado_cargo,
        nombre_usuario=nombre_usuario,
        contraseña_hash=generate_password_hash(password),
        rol=rol
    )
    db.session.add(usuario)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Usuario "{nombre_completo}" creado exitosamente.',
        'usuario': usuario.to_dict()
    }), 201


@inventario_bp.route('/api/usuarios/<int:id>', methods=['PUT'])
@login_required
@admin_required
def actualizar_usuario(id):
    """
    Actualiza los datos de un usuario (sin cambiar la contraseña).
    Solo accesible para administradores.
    """
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'success': False, 'message': 'Usuario no encontrado.'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No se recibieron datos.'}), 400

    # Actualizar campos proporcionados
    if 'nombre_completo' in data and data['nombre_completo'].strip():
        usuario.nombre_completo = data['nombre_completo'].strip()

    if 'grado_cargo' in data and data['grado_cargo'].strip():
        usuario.grado_cargo = data['grado_cargo'].strip()

    if 'nombre_usuario' in data and data['nombre_usuario'].strip():
        nuevo_nombre_usuario = data['nombre_usuario'].strip()
        # Verificar unicidad solo si cambió
        if nuevo_nombre_usuario != usuario.nombre_usuario:
            if Usuario.query.filter_by(nombre_usuario=nuevo_nombre_usuario).first():
                return jsonify({
                    'success': False,
                    'message': f'El nombre de usuario "{nuevo_nombre_usuario}" ya está en uso.'
                }), 409
            usuario.nombre_usuario = nuevo_nombre_usuario

    if 'rol' in data and data['rol'].strip():
        nuevo_rol = data['rol'].strip()
        roles_validos = ['Administrador', 'Logística', 'Consulta']
        if nuevo_rol not in roles_validos:
            return jsonify({
                'success': False,
                'message': f'Rol inválido. Debe ser uno de: {", ".join(roles_validos)}.'
            }), 400
        usuario.rol = nuevo_rol

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Usuario "{usuario.nombre_completo}" actualizado exitosamente.',
        'usuario': usuario.to_dict()
    })


@inventario_bp.route('/api/usuarios/<int:id>/toggle', methods=['PATCH'])
@login_required
@admin_required
def toggle_usuario(id):
    """
    Alterna el estado del usuario entre Activo e Inactivo.
    Solo accesible para administradores.
    """
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'success': False, 'message': 'Usuario no encontrado.'}), 404

    # Evitar que el administrador se desactive a sí mismo
    if usuario.id == current_user.id:
        return jsonify({
            'success': False,
            'message': 'No puede desactivar su propia cuenta.'
        }), 400

    usuario.estado = 'Inactivo' if usuario.estado == 'Activo' else 'Activo'
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Usuario "{usuario.nombre_completo}" ahora está {usuario.estado}.',
        'usuario': usuario.to_dict()
    })


@inventario_bp.route('/api/usuarios/<int:id>/reset-password', methods=['PATCH'])
@login_required
@admin_required
def reset_password(id):
    """
    Restablece la contraseña del usuario a 'sar12345'.
    Solo accesible para administradores.
    """
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'success': False, 'message': 'Usuario no encontrado.'}), 404

    usuario.contraseña_hash = generate_password_hash('sar12345')
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Contraseña de "{usuario.nombre_completo}" restablecida a la contraseña por defecto (sar12345).'
    })
