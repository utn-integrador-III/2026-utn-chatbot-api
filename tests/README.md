 # Ejecutar pruebas (pytest) — cheatsheet y guía

Resumen rápido — comandos esenciales

```powershell
# 1) Activar entorno virtual (PowerShell)
.\env_chatbot\Scripts\Activate.ps1

# 2) Ejecutar toda la suite de tests
.\env_chatbot\Scripts\python -m pytest -q

# 3) Ejecutar un archivo de tests específico
.\env_chatbot\Scripts\python -m pytest tests/test_services_login_service.py -q

# 4) Ejecutar con reporte de cobertura (mostrando líneas faltantes)
.\env_chatbot\Scripts\python -m pytest --cov=app --cov-report=term-missing
```

---

Guía detallada

1) Activar entorno virtual

- Qué hace: carga el environment virtual `env_chatbot` del proyecto y apunta `python`/`pip` a ese entorno.
- Cuándo usar: siempre antes de instalar dependencias o ejecutar `pytest` para usar las mismas dependencias que el proyecto.
- Comando:

```powershell
.\env_chatbot\Scripts\Activate.ps1
```

- Ejemplo de salida esperada: el prompt de PowerShell cambia mostrando el nombre del entorno (p. ej. `(env_chatbot) PS C:\...`).
- Si no ves ese cambio: asegúrate de que la carpeta `env_chatbot` exista y que estés en la raíz del repo.


2) Ejecutar toda la suite de tests

- Qué hace: corre todos los tests detectados por `pytest` según `pytest.ini` (`tests/` y `test_*.py`).
- Cuándo usar: validar rápidamente que nada se rompió después de un cambio.
- Comando:

```powershell
.\env_chatbot\Scripts\python -m pytest -q
```

- Ejemplo de salida esperada (resumen):

```
......                                                           [ 50%]
...................................                                [100%]
106 passed in 8.24s
```

- Qué significa: `passed` indica tests exitosos. Si ves `failed` o `errors`, abre el detalle que pytest muestra para identificar fallos.


3) Ejecutar un archivo de tests específico

- Qué hace: corre solo los tests definidos en el archivo indicado.
- Cuándo usar: depuración o desarrollo de tests en una sola área (ej: `services`).
- Comando:

```powershell
.\env_chatbot\Scripts\python -m pytest tests/test_services_login_service.py -q
```

- Ejemplo de salida esperada:

```
...                                                                 [100%]
3 passed in 0.45s
```


4) Ejecutar con reporte de cobertura

- Qué hace: ejecuta tests y muestra cobertura por módulo en la carpeta `app/`, indicando líneas faltantes.
- Cuándo usar: antes de un merge para revisar cobertura o para detectar áreas no probadas.
- Comando:

```powershell
.\env_chatbot\Scripts\python -m pytest --cov=app --cov-report=term-missing
```

- Ejemplo de salida esperada (fragmento):

```
Name                            Stmts   Miss  Cover   Missing
-------------------------------------------------------------
app/repositories/admin_repository.py    50     30    40%   61-68,72-79
app/services/login_service.py           200    48    76%   60,62,116,...
```

- Qué significa: `Stmts` = líneas instrumentadas, `Miss` = líneas no ejecutadas por tests, `Cover` = porcentaje de cobertura. Un % bajo indica deuda de tests.


Requisitos previos

- Python 3.11+ (el proyecto usó Python 3.11 en el entorno virtual proporcionado).
- Paquetes: `pytest`, `pytest-cov` y dependencias del proyecto. El proyecto incluye `requirements.txt` con `pytest` y `pytest-cov`.

- Para instalar dependencias (desde la raíz del repo, con el entorno activado):

```powershell
.\env_chatbot\Scripts\python -m pip install -r requirements.txt
```


Estructura de la carpeta `tests/`

- Convención usada en este repo: un archivo de test por módulo. Nombre: `test_<module>.py` o `test_<layer>_<module>.py`.
- `pytest.ini` en la raíz configura `testpaths = tests` y `python_files = test_*.py`.


Cómo correr solo una capa (controllers / services / repositories)

- Usando patrón de nombre de archivo (ejemplos):

```powershell
# Todos los tests de services
.\env_chatbot\Scripts\python -m pytest tests/test_services_*.py -q

# Todos los tests de repositories
.\env_chatbot\Scripts\python -m pytest tests/test_repositories_*.py -q
```

- También puedes usar `-k` para filtrar por parte del nombre del test:

```powershell
.\env_chatbot\Scripts\python -m pytest -k "login and signup" -q
```


Interpretar el reporte de cobertura

- Columnas principales:
  - `Stmts`: número de líneas instrumentadas por coverage
  - `Miss`: líneas no cubiertas
  - `Cover`: porcentaje de cobertura
  - `Missing`: rangos de líneas sin ejecutar

- Un % bajo significa que hay áreas sin tests. Para localizar las líneas exactas, usa el flag `--cov-report=term-missing` (muestra `Missing`).

- Para mejorar cobertura: añadir tests que ejerciten ramas, excepciones y condiciones no cubiertas.


Errores comunes y soluciones

- ModuleNotFoundError al importar módulos del paquete `app`:

  - Causa típica: pytest no está ejecutado desde la raíz del proyecto o `pythonpath` no incluye `.`.
  - En este repo, `pytest.ini` ya contiene `pythonpath = .`, por lo que ejecutar pytest desde la raíz con el entorno activado debe resolverlo.
  - Solución rápida: ejecutar desde la raíz del repo:

  ```powershell
  .\env_chatbot\Scripts\python -m pytest -q
  ```

  - Si sigues con `ModuleNotFoundError`, confirma que estás en la carpeta que contiene `app/` y `pytest.ini`.


- Ejecutar un solo test por nombre:

```powershell
.\env_chatbot\Scripts\python -m pytest -k "test_signup_with_missing_fields_returns_400" -q
```

Si el test exacto no se ejecuta, revisa la cadena usada con `-k` (coincidencia de substring).


- Obtener salida más detallada y rastreo de errores:

```powershell
# Verbose
.\env_chatbot\Scripts\python -m pytest -v

# Traza corta
.\env_chatbot\Scripts\python -m pytest --tb=short

# Traza larga
.\env_chatbot\Scripts\python -m pytest --tb=long
```


Consejos rápidos

- Siempre activa el entorno virtual antes de ejecutar `pytest` para usar dependencias del proyecto.
- Usa `-q` para salida compacta durante ejecuciones frecuentes, y `-v` cuando necesites detalle.
- Revisa `pytest.ini` si cambias la convención de nombres o la ruta de tests.

Si necesitas que añada un `tests/conftest.py` con helpers compartidos (por ejemplo, mapeos para `sys.modules` que actualmente se repiten en varios tests), dímelo y lo preparo — lo único que haría sería crear el archivo `tests/conftest.py` (no modificaría tests existentes).

Fin del README de tests
