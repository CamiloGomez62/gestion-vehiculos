import os
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

NOMBRE_APP = "ConcesionarioVehiculos"
NOMBRE_BD = "proyectofinal.db"
VERSION_ESQUEMA = 1

# El esquema vive dentro del código a propósito: así el ejecutable no depende
# de ningún archivo externo y la base se crea sola la primera vez que se abre.
ESQUEMA = """
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
"""


def carpeta_datos() -> Path:
  """Carpeta de datos del usuario en su propia PC (no depende del .exe).

  Windows: %APPDATA%\\ConcesionarioVehiculos
  macOS:   ~/Library/Application Support/ConcesionarioVehiculos
  Linux:   ~/.local/share/ConcesionarioVehiculos
  """
  if sys.platform.startswith("win"):
    base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
  elif sys.platform == "darwin":
    base = Path.home() / "Library" / "Application Support"
  else:
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
  return base / NOMBRE_APP


def ruta_base_datos() -> Path:
  """Ruta del archivo .db. Se puede cambiar con CONCESIONARIO_DB."""
  personalizada = os.environ.get("CONCESIONARIO_DB")
  if personalizada:
    return Path(personalizada)
  return carpeta_datos() / NOMBRE_BD


class Conexion:
  """Acceso a la base SQLite local. Crea el archivo y las tablas si faltan."""

  def __init__(self, ruta=None):
    self.ruta = Path(ruta) if ruta else ruta_base_datos()
    self._inicializar()

  def _inicializar(self):
    self.ruta.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(self.ruta)
    try:
      conexion.executescript(ESQUEMA)
      conexion.execute(f"PRAGMA user_version = {VERSION_ESQUEMA}")
      conexion.commit()
    finally:
      conexion.close()

  def conectar(self) -> sqlite3.Connection:
    conexion = sqlite3.connect(self.ruta, timeout=10)
    conexion.row_factory = sqlite3.Row
    # SQLite ignora las llaves foráneas si no se activan en cada conexión.
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion

  @contextmanager
  def transaccion(self):
    """Abre una conexión; confirma al salir bien y deshace si hay error."""
    conexion = self.conectar()
    try:
      yield conexion
      conexion.commit()
    except BaseException:
      conexion.rollback()
      raise
    finally:
      conexion.close()
