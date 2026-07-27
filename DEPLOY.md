# Despliegue en PythonAnywhere

Guía paso a paso para publicar MovieMatch en la capa gratuita de
[PythonAnywhere](https://www.pythonanywhere.com/). El nombre de usuario del
usuario es `maagudeloo`.

## 1. Crear la cuenta

1. Regístrate en pythonanywhere.com con una cuenta **Beginner** (gratuita).
2. Tu aplicación quedará en `https://maagudeloo.pythonanywhere.com`.

## 2. Traer el código

Abre una consola **Bash** desde el panel de PythonAnywhere y clona el repositorio:

```bash
git clone https://github.com/Dev-Mao/moviematch.git
cd moviematch
```

## 3. Entorno virtual e instalación

```bash
python3.13 -m venv venv           # usa la versión de Python disponible más alta
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Base de datos y datos de prueba

```bash
python manage.py migrate
python manage.py loaddata fixtures/catalogo.json
python manage.py seed_demo
python manage.py collectstatic --noinput
```

Esto crea la base SQLite, carga las 60 películas y series, genera los usuarios de
demostración y reúne los archivos estáticos. **No se necesita la API de TMDB.**

## 5. Crear la aplicación web

1. En el panel, ve a la pestaña **Web** y pulsa **Add a new web app**.
2. Elige **Manual configuration** (no "Django") y la misma versión de Python del
   entorno virtual.

## 6. Configurar la web app

En la pestaña **Web**, ajusta:

- **Virtualenv:** `/home/maagudeloo/moviematch/venv`
- **Source code:** `/home/maagudeloo/moviematch`
- **Static files:** agrega un mapeo
  - URL: `/static/`  →  Directory: `/home/maagudeloo/moviematch/staticfiles`

## 7. Archivo WSGI

Edita el archivo WSGI (enlace en la pestaña **Web**) y reemplaza su contenido por:

```python
import os
import sys

path = "/home/maagudeloo/moviematch"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DJANGO_SECRET_KEY"] = "pega-aqui-una-clave-larga-y-aleatoria"
os.environ["DJANGO_DEBUG"] = "False"
os.environ["DJANGO_ALLOWED_HOSTS"] = "maagudeloo.pythonanywhere.com"
os.environ["DJANGO_CSRF_TRUSTED_ORIGINS"] = "https://maagudeloo.pythonanywhere.com"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Para generar la clave secreta:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 8. Publicar

1. Pulsa el botón verde **Reload** en la pestaña **Web**.
2. Abre `https://maagudeloo.pythonanywhere.com`.
3. Inicia sesión con `mariana` / `moviematch2026`, o `admin` para el panel.

## Actualizar el despliegue

Cuando haya cambios nuevos en el repositorio:

```bash
cd ~/moviematch
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Y pulsa **Reload** en la pestaña **Web**.
