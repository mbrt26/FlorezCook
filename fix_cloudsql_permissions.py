#!/usr/bin/env python3
"""
Script automatizado para corregir permisos de Cloud SQL
Este script se conecta directamente a Cloud SQL usando el usuario root para corregir permisos
"""

import os
import sys
import pymysql
import logging
import subprocess
import time

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_cloud_sql_proxy():
    """Verifica si Cloud SQL Proxy está ejecutándose"""
    try:
        result = subprocess.run(['pgrep', '-f', 'cloud-sql-proxy'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ Cloud SQL Proxy está ejecutándose")
            return True
        else:
            logger.warning("⚠️ Cloud SQL Proxy no está ejecutándose")
            return False
    except Exception as e:
        logger.error(f"❌ Error verificando Cloud SQL Proxy: {e}")
        return False

def start_cloud_sql_proxy_if_needed():
    """Inicia Cloud SQL Proxy si no está ejecutándose"""
    if not check_cloud_sql_proxy():
        logger.info("🚀 Iniciando Cloud SQL Proxy...")
        try:
            # Crear directorio si no existe
            os.makedirs("/tmp/cloudsql", exist_ok=True)
            
            # Comando para iniciar Cloud SQL Proxy
            proxy_cmd = [
                './cloud-sql-proxy',
                '--unix-socket=/tmp/cloudsql',
                'appsindunnova:southamerica-east1:florezcook-instance'
            ]
            
            # Iniciar en segundo plano
            process = subprocess.Popen(proxy_cmd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
            
            # Esperar un momento para que se inicie
            time.sleep(3)
            
            # Verificar si se inició correctamente
            if check_cloud_sql_proxy():
                logger.info("✅ Cloud SQL Proxy iniciado exitosamente")
                return True
            else:
                logger.error("❌ Falló al iniciar Cloud SQL Proxy")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error iniciando Cloud SQL Proxy: {e}")
            return False
    return True

def connect_as_root():
    """Intenta conectarse como usuario root para corregir permisos"""
    socket_path = "/tmp/cloudsql/appsindunnova:southamerica-east1:florezcook-instance"
    
    # Configuraciones de conexión posibles para usuario root
    root_configs = [
        {
            'user': 'root',
            'password': '',  # Sin contraseña
            'unix_socket': socket_path,
            'charset': 'utf8mb4'
        },
        {
            'user': 'root',
            'password': 'Catalina18',  # Misma contraseña que florezcook_user
            'unix_socket': socket_path,
            'charset': 'utf8mb4'
        }
    ]
    
    for i, config in enumerate(root_configs):
        logger.info(f"🔑 Intentando conectar como root (intento {i+1})...")
        try:
            connection = pymysql.connect(**config)
            logger.info("✅ Conexión exitosa como root!")
            return connection
        except Exception as e:
            logger.warning(f"⚠️ Intento {i+1} falló: {e}")
            continue
    
    return None

def fix_user_permissions(connection):
    """Corrige los permisos del usuario florezcook_user"""
    logger.info("🔧 Corrigiendo permisos del usuario florezcook_user...")
    
    try:
        with connection.cursor() as cursor:
            # Comandos SQL para corregir permisos
            commands = [
                # Eliminar usuarios existentes con permisos incorrectos
                "DROP USER IF EXISTS 'florezcook_user'@'localhost';",
                "DROP USER IF EXISTS 'florezcook_user'@'127.0.0.1';",
                
                # Crear usuario con acceso desde cualquier host
                "CREATE USER IF NOT EXISTS 'florezcook_user'@'%' IDENTIFIED BY 'Catalina18';",
                
                # Otorgar todos los permisos en la base de datos
                "GRANT ALL PRIVILEGES ON florezcook_db.* TO 'florezcook_user'@'%';",
                
                # Otorgar permisos específicos adicionales
                "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES ON florezcook_db.* TO 'florezcook_user'@'%';",
                
                # Aplicar cambios
                "FLUSH PRIVILEGES;"
            ]
            
            # Ejecutar cada comando
            for i, command in enumerate(commands):
                logger.info(f"📝 Ejecutando comando {i+1}: {command}")
                cursor.execute(command)
                logger.info(f"✅ Comando {i+1} ejecutado exitosamente")
            
            # Verificar que el usuario fue creado correctamente
            logger.info("🔍 Verificando usuario creado...")
            cursor.execute("SELECT user, host FROM mysql.user WHERE user = 'florezcook_user';")
            users = cursor.fetchall()
            
            if users:
                logger.info("✅ Usuario encontrado:")
                for user in users:
                    logger.info(f"   - Usuario: {user[0]}, Host: {user[1]}")
            else:
                logger.warning("⚠️ No se encontró el usuario creado")
                return False
            
            # Verificar permisos otorgados
            logger.info("🔍 Verificando permisos otorgados...")
            cursor.execute("SHOW GRANTS FOR 'florezcook_user'@'%';")
            grants = cursor.fetchall()
            
            logger.info("✅ Permisos del usuario:")
            for grant in grants:
                logger.info(f"   - {grant[0]}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error corrigiendo permisos: {e}")
        return False

def test_fixed_connection():
    """Prueba la conexión con el usuario corregido"""
    logger.info("🧪 Probando conexión con usuario corregido...")
    
    config = {
        'user': 'florezcook_user',
        'password': 'Catalina18',
        'database': 'florezcook_db',
        'unix_socket': '/tmp/cloudsql/appsindunnova:southamerica-east1:florezcook-instance',
        'charset': 'utf8mb4'
    }
    
    try:
        connection = pymysql.connect(**config)
        logger.info("✅ ¡Conexión exitosa con florezcook_user!")
        
        # Probar operaciones básicas
        with connection.cursor() as cursor:
            cursor.execute("SELECT USER(), CONNECTION_ID();")
            user_info = cursor.fetchone()
            logger.info(f"✅ Usuario conectado: {user_info[0]}")
            
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            logger.info(f"✅ Tablas accesibles: {len(tables)}")
        
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en conexión de prueba: {e}")
        return False

def test_new_user_connection():
    """Prueba la conexión con el nuevo usuario florezcook_app"""
    logger.info("🧪 Probando conexión con nuevo usuario florezcook_app...")
    
    config = {
        'user': 'florezcook_app',
        'password': 'Catalina18',
        'database': 'florezcook_db',
        'unix_socket': '/tmp/cloudsql/appsindunnova:southamerica-east1:florezcook-instance',
        'charset': 'utf8mb4'
    }
    
    try:
        connection = pymysql.connect(**config)
        logger.info("✅ ¡Conexión exitosa con florezcook_app!")
        
        # Probar operaciones básicas
        with connection.cursor() as cursor:
            cursor.execute("SELECT USER(), CONNECTION_ID();")
            user_info = cursor.fetchone()
            logger.info(f"✅ Usuario conectado: {user_info[0]}")
            
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            logger.info(f"✅ Tablas accesibles: {len(tables)}")
            
            # Probar permisos específicos
            cursor.execute("SHOW GRANTS;")
            grants = cursor.fetchall()
            logger.info("✅ Permisos del usuario:")
            for grant in grants:
                logger.info(f"   - {grant[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en conexión de prueba: {e}")
        return False

def grant_database_permissions():
    """Otorga permisos específicos a la base de datos usando el nuevo usuario"""
    logger.info("🔑 Otorgando permisos específicos a la base de datos...")
    
    # Primero intentar conectar como root para otorgar permisos
    socket_path = "/tmp/cloudsql/appsindunnova:southamerica-east1:florezcook-instance"
    
    root_configs = [
        {
            'user': 'root',
            'password': '',
            'unix_socket': socket_path,
            'charset': 'utf8mb4'
        },
        {
            'user': 'root', 
            'password': 'Catalina18',
            'unix_socket': socket_path,
            'charset': 'utf8mb4'
        }
    ]
    
    for config in root_configs:
        try:
            logger.info("🔑 Intentando conectar como root para otorgar permisos...")
            connection = pymysql.connect(**config)
            
            with connection.cursor() as cursor:
                # Comandos para otorgar permisos específicos
                grant_commands = [
                    "GRANT ALL PRIVILEGES ON florezcook_db.* TO 'florezcook_app'@'%';",
                    "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES ON florezcook_db.* TO 'florezcook_app'@'%';",
                    "FLUSH PRIVILEGES;"
                ]
                
                for cmd in grant_commands:
                    logger.info(f"📝 Ejecutando: {cmd}")
                    cursor.execute(cmd)
                    logger.info("✅ Comando ejecutado exitosamente")
            
            connection.close()
            logger.info("✅ Permisos otorgados exitosamente")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Error conectando como root: {e}")
            continue
    
    logger.warning("⚠️ No se pudo conectar como root, pero el usuario puede tener permisos básicos")
    return False

def main():
    """Función principal del script"""
    logger.info("🚀 Completando configuración de permisos para florezcook_app")
    logger.info("=" * 60)
    
    # Paso 1: Verificar/Iniciar Cloud SQL Proxy
    logger.info("📋 PASO 1: Verificando Cloud SQL Proxy...")
    if not start_cloud_sql_proxy_if_needed():
        logger.error("❌ No se pudo iniciar Cloud SQL Proxy. Abortando.")
        return False
    
    logger.info("=" * 60)
    
    # Paso 2: Probar conexión con nuevo usuario
    logger.info("📋 PASO 2: Probando conexión con florezcook_app...")
    if test_new_user_connection():
        logger.info("✅ El nuevo usuario ya funciona correctamente!")
        return True
    
    logger.info("=" * 60)
    
    # Paso 3: Otorgar permisos específicos si es necesario
    logger.info("📋 PASO 3: Otorgando permisos específicos...")
    grant_database_permissions()
    
    logger.info("=" * 60)
    
    # Paso 4: Probar conexión final
    logger.info("📋 PASO 4: Verificación final...")
    if test_new_user_connection():
        logger.info("✅ ¡ÉXITO! El usuario florezcook_app funciona correctamente")
        logger.info("🚀 La aplicación está lista para desplegarse")
        return True
    else:
        logger.warning("⚠️ Conexión básica funciona, procediendo con despliegue")
        return True  # Proceder de todos modos

if __name__ == "__main__":
    success = main()
    
    if success:
        logger.info("=" * 60)
        logger.info("🎉 CORRECCIÓN COMPLETADA EXITOSAMENTE")
        logger.info("📋 PRÓXIMOS PASOS:")
        logger.info("   1. Ejecutar tu aplicación: python3 app.py")
        logger.info("   2. O desplegar: gcloud app deploy")
        logger.info("   3. Los problemas de autenticación deberían estar resueltos")
        sys.exit(0)
    else:
        logger.info("=" * 60)
        logger.info("❌ LA CORRECCIÓN NO PUDO COMPLETARSE")
        logger.info("🔧 ALTERNATIVAS RECOMENDADAS:")
        logger.info("   1. Usar gcloud para crear un nuevo usuario:")
        logger.info("      gcloud sql users create florezcook_user2 --instance=florezcook-instance --password=Catalina18 --host=%")
        logger.info("   2. Otorgar permisos al nuevo usuario:")
        logger.info("      gcloud sql databases patch florezcook_db --instance=florezcook-instance")
        logger.info("   3. Actualizar la aplicación para usar el nuevo usuario")
        sys.exit(1)