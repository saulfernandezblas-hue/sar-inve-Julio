"""
SAR-INVENTORY - Modelos de Base de Datos
========================================
Definición de los modelos SQLAlchemy para el sistema de inventario.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    """Modelo de usuario del sistema con soporte para autenticación y control de acceso."""

    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(100), nullable=False)
    grado_cargo = db.Column(db.String(100), nullable=False)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # Administrador, Logística, Consulta
    estado = db.Column(db.String(10), default='Activo')  # Activo, Inactivo
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ultimo_acceso = db.Column(db.DateTime)
    intentos_fallidos = db.Column(db.Integer, default=0)
    bloqueado_hasta = db.Column(db.DateTime)

    def to_dict(self):
        """Serializa el usuario a diccionario, excluyendo el hash de la contraseña."""
        return {
            'id': self.id,
            'nombre_completo': self.nombre_completo,
            'grado_cargo': self.grado_cargo,
            'nombre_usuario': self.nombre_usuario,
            'rol': self.rol,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion.strftime('%d/%m/%Y %H:%M') if self.fecha_creacion else None,
            'ultimo_acceso': self.ultimo_acceso.strftime('%d/%m/%Y %H:%M') if self.ultimo_acceso else 'Nunca',
            'intentos_fallidos': self.intentos_fallidos,
            'bloqueado_hasta': self.bloqueado_hasta.strftime('%d/%m/%Y %H:%M') if self.bloqueado_hasta else None,
        }


class Equipo(db.Model):
    """Modelo de equipo/material del inventario SAR."""

    __tablename__ = 'equipos'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(10), nullable=False)  # Bueno, Regular, Malo
    categoria = db.Column(db.String(50), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_modificacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        """Serializa el equipo a diccionario."""
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'cantidad': self.cantidad,
            'estado': self.estado,
            'categoria': self.categoria,
            'fecha_registro': self.fecha_registro.strftime('%d/%m/%Y %H:%M') if self.fecha_registro else None,
            'fecha_modificacion': self.fecha_modificacion.strftime('%d/%m/%Y %H:%M') if self.fecha_modificacion else None,
        }


class Movimiento(db.Model):
    """Modelo de registro de movimientos/auditoría del sistema."""

    __tablename__ = 'movimientos'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    accion = db.Column(db.String(20), nullable=False)  # Agregó, Modificó, Eliminó
    equipo_codigo = db.Column(db.String(20))
    equipo_nombre = db.Column(db.String(100))
    detalle = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    usuario = db.relationship('Usuario', backref='movimientos')

    def to_dict(self):
        """Serializa el movimiento a diccionario."""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario.nombre_completo if self.usuario else 'Sistema',
            'accion': self.accion,
            'equipo_codigo': self.equipo_codigo,
            'equipo_nombre': self.equipo_nombre,
            'detalle': self.detalle,
            'fecha': self.fecha.strftime('%d/%m/%Y %H:%M') if self.fecha else None,
        }
