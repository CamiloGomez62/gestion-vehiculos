# Sistema de Gestión: Venta y Almacén de Vehículos

## Ejecutar desde el código
```
pip install -r requirements.txt
python main.py
```

## Generar el ejecutable (.exe)
Hazlo en Windows para obtener un `.exe` de Windows:
```
pip install -r requirements.txt
pyinstaller main.spec
```
Resultado: `dist/ConcesionarioVehiculos.exe` (un solo archivo; se puede copiar a
cualquier PC con Windows sin instalar Python ni MySQL).

## Base de datos (SQLite)
- No hay que instalar ni configurar nada: la **primera vez** que se abre el
  programa crea solo su base de datos en la PC de cada usuario:

  | Sistema | Ruta |
  |---|---|
  | Windows | `%APPDATA%\ConcesionarioVehiculos\proyectofinal.db` |
  | macOS | `~/Library/Application Support/ConcesionarioVehiculos/proyectofinal.db` |
  | Linux | `~/.local/share/ConcesionarioVehiculos/proyectofinal.db` |

- La ruta exacta también aparece abajo en la ventana del programa.
- Los datos se conservan aunque se cierre, mueva o actualice el `.exe`.
- Para respaldar: copia ese archivo `.db`. Para empezar de cero: bórralo.
- Se puede usar otra ruta con la variable de entorno `CONCESIONARIO_DB`.
- `proyectofinal.sql` es solo una referencia del esquema (el programa no lo necesita).

## Pruebas
```
python -m unittest discover -s pruebas -t . -v
```

## Estructura
- `modelo/` clases (Vehiculo, Automovil, Moto, Camion, Cliente, Venta, Inventario)
  y estructuras de datos (lista doblemente enlazada, pila).
- `controlador/` conexión SQLite y lógica de negocio.
- `Vista/` interfaz gráfica (customtkinter).
