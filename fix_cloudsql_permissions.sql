-- Script para corregir permisos de usuario en Cloud SQL
-- Ejecutar estos comandos en la consola de Google Cloud SQL
-- Ve a: https://console.cloud.google.com/sql/instances/florezcook-instance/overview

-- 1. Eliminar usuarios existentes con permisos incorrectos (si existen)
DROP USER IF EXISTS 'florezcook_user'@'localhost';
DROP USER IF EXISTS 'florezcook_user'@'127.0.0.1';
DROP USER IF EXISTS 'florezcook_user'@'%';

-- 2. Crear usuario correcto que coincida con app.yaml (florezcook_app)
CREATE USER IF NOT EXISTS 'florezcook_app'@'%' IDENTIFIED BY 'Catalina18';

-- 3. Otorgar todos los permisos en la base de datos florezcook_db
GRANT ALL PRIVILEGES ON florezcook_db.* TO 'florezcook_app'@'%';

-- 4. Otorgar permisos específicos adicionales para asegurar acceso completo
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES ON florezcook_db.* TO 'florezcook_app'@'%';

-- 5. Aplicar cambios inmediatamente
FLUSH PRIVILEGES;

-- 6. Verificar que el usuario fue creado correctamente
SELECT user, host FROM mysql.user WHERE user = 'florezcook_app';

-- 7. Verificar permisos otorgados
SHOW GRANTS FOR 'florezcook_app'@'%';

-- RESULTADO ESPERADO:
-- El comando SELECT debe mostrar:
-- florezcook_app | %
-- 
-- El comando SHOW GRANTS debe mostrar algo como:
-- GRANT USAGE ON *.* TO `florezcook_app`@`%`
-- GRANT ALL PRIVILEGES ON `florezcook_db`.* TO `florezcook_app`@`%`