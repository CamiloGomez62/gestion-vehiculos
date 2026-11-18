-- Base de datos SQLite del Sistema de Gestión: Venta y Almacén de Vehículos
--
-- NO es necesario ejecutar este archivo: el programa crea automáticamente la
-- base de datos (proyectofinal.db) en la PC de cada usuario la primera vez que
-- se abre. Este script es solo una referencia del esquema y sirve para crear
-- la base a mano con:   sqlite3 proyectofinal.db < proyectofinal.sql
-- (o desde "DB Browser for SQLite").
--
-- Reemplaza al volcado de MySQL/phpMyAdmin anterior.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS clientes (
  cedula   TEXT PRIMARY KEY,
  nombre   TEXT NOT NULL,
  telefono TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vehiculos (
  vin           TEXT PRIMARY KEY,
  marca         TEXT NOT NULL,
  modelo        TEXT NOT NULL,
  anio          INTEGER NOT NULL CHECK (anio BETWEEN 1900 AND 2100),
  precio_base   REAL NOT NULL CHECK (precio_base > 0),
  tipo_vehiculo TEXT NOT NULL CHECK (tipo_vehiculo IN ('Auto', 'Moto', 'Camión'))
);

CREATE TABLE IF NOT EXISTS detalles_auto (
  vin              TEXT PRIMARY KEY REFERENCES vehiculos (vin) ON DELETE CASCADE,
  num_puertas      INTEGER NOT NULL,
  tipo_combustible TEXT NOT NULL,
  tiene_camara     INTEGER NOT NULL DEFAULT 0 CHECK (tiene_camara IN (0, 1))
);

CREATE TABLE IF NOT EXISTS detalles_moto (
  vin           TEXT PRIMARY KEY REFERENCES vehiculos (vin) ON DELETE CASCADE,
  cilindraje    INTEGER NOT NULL,
  tipo_manubrio TEXT NOT NULL,
  tiene_abs     INTEGER NOT NULL DEFAULT 0 CHECK (tiene_abs IN (0, 1))
);

CREATE TABLE IF NOT EXISTS detalles_camion (
  vin             TEXT PRIMARY KEY REFERENCES vehiculos (vin) ON DELETE CASCADE,
  capacidad_carga REAL NOT NULL,
  num_ejes        INTEGER NOT NULL,
  tipo_carroceria TEXT NOT NULL
);

-- Un VIN solo puede venderse una vez (UNIQUE) y el historial de ventas no se
-- borra en cascada: no se puede eliminar un cliente o vehículo ya vendido.
CREATE TABLE IF NOT EXISTS ventas (
  id_venta       TEXT PRIMARY KEY,
  cedula_cliente TEXT NOT NULL REFERENCES clientes (cedula) ON DELETE RESTRICT,
  vin_vehiculo   TEXT NOT NULL UNIQUE REFERENCES vehiculos (vin) ON DELETE RESTRICT,
  precio_venta   REAL NOT NULL CHECK (precio_venta > 0),
  fecha          TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas (cedula_cliente);
