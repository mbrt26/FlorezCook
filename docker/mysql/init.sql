-- Script de inicialización para FlorezCook Database
-- Se ejecuta automáticamente cuando se crea el contenedor MySQL

-- Configurar charset y collation
ALTER DATABASE florezcook CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Configuraciones MySQL optimizadas para FlorezCook
SET GLOBAL innodb_buffer_pool_size = 268435456; -- 256MB
SET GLOBAL max_connections = 200;
SET GLOBAL innodb_log_file_size = 67108864; -- 64MB
SET GLOBAL query_cache_size = 16777216; -- 16MB
SET GLOBAL query_cache_type = 1;

-- Usar la base de datos FlorezCook
USE florezcook;

-- Mensaje de confirmación
SELECT 'FlorezCook Database inicializada correctamente' as mensaje;

-- Configurar zona horaria para Colombia
SET time_zone = '-05:00';

-- Configurar formato de fechas
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- Crear usuario adicional de solo lectura para reportes (opcional)
CREATE USER IF NOT EXISTS 'florezcook_readonly'@'%' IDENTIFIED BY 'readonly_pass_2025';
GRANT SELECT ON florezcook.* TO 'florezcook_readonly'@'%';

-- Flush privileges
FLUSH PRIVILEGES;

-- Log final
SELECT 'Configuración de FlorezCook MySQL completada' as status;

-- [START init_sql]
-- Crear la base de datos si no existe
CREATE DATABASE IF NOT EXISTS `florezcook_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE `florezcook_db`;

-- Crear un usuario para la aplicación con privilegios limitados
CREATE USER IF NOT EXISTS 'florezcook_user'@'%' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON `florezcook_db`.* TO 'florezcook_user'@'%';
FLUSH PRIVILEGES;

-- Crear tablas iniciales
-- Nota: Estas tablas se crearán automáticamente mediante SQLAlchemy si usas create_all()
-- Se incluyen aquí como referencia o para migraciones manuales

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(80) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(128),
    `is_admin` BOOLEAN DEFAULT FALSE,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de perfiles de usuario
CREATE TABLE IF NOT EXISTS `user_profiles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `first_name` VARCHAR(80),
    `last_name` VARCHAR(80),
    `phone` VARCHAR(20),
    `address` TEXT,
    `profile_image` VARCHAR(255),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar usuario administrador por defecto (cambiar la contraseña en producción)
-- La contraseña es 'admin123' (hash bcrypt)
INSERT IGNORE INTO `users` (`username`, `email`, `password_hash`, `is_admin`, `is_active`) VALUES
('admin', 'admin@florezcook.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', TRUE, TRUE);

-- Insertar perfil para el administrador
INSERT IGNORE INTO `user_profiles` (`user_id`, `first_name`, `last_name`) 
SELECT id, 'Admin', 'User' FROM `users` WHERE username = 'admin';

-- Crear índices para mejorar el rendimiento
CREATE INDEX idx_users_email ON `users`(`email`);
CREATE INDEX idx_users_username ON `users`(`username`);
CREATE INDEX idx_user_profiles_user_id ON `user_profiles`(`user_id`);

-- [END init_sql]
