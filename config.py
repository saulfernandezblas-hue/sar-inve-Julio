"""
SAR-INVENTORY - Configuración del Sistema
==========================================
Archivo de configuración central para la aplicación Flask.
"""

from datetime import timedelta


import os

class Config:
    """Configuración principal de la aplicación."""

    # Clave secreta para sesiones y protección CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sar-inventory-dev-key-change-in-prod')

    # Configuración de la base de datos SQLite
    SQLALCHEMY_DATABASE_URI = 'sqlite:///sar_inventory.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # Configuración de seguridad de inicio de sesión
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_TIME = 300  # 5 minutos en segundos
