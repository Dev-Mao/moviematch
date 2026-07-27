# MovieMatch

Aplicación de recomendaciones de películas y series que combina los gustos del
usuario con las valoraciones de sus amigos.

**Asignatura:** Calidad de Software 2025-2
**Profesor:** Albeiro Espinosa Bedoya, Ph.D., M.Sc.
**Estudiante:** Mariana Agudelo Ospina (Equipo 1)

**Aplicación en línea:** https://maagudeloo.pythonanywhere.com
(entra con `mariana` / `moviematch2026`; sin necesidad de instalar nada)

## Descripción

MovieMatch busca resolver la saturación de opciones en las plataformas de
streaming. En lugar de navegar listas interminables, el usuario recibe
recomendaciones personalizadas a partir de su historial de valoraciones, sus
géneros preferidos y lo que han valorado sus amigos, convirtiendo la elección de
qué ver en una experiencia social.

## Estructura del repositorio

```
.
├── docs/            Documentación de análisis y diseño
├── diagrams/        Diagramas UML (PlantUML + PNG/SVG)
├── mockups/         Prototipos de interfaz (Pencil) y sus exportaciones
└── ENTREGABLE-1.md  Informe consolidado del primer entregable
```

## Entregables

### Primer entregable (análisis y diseño)

- Modelo de dominio
- Diagrama de casos de uso
- Especificación de los 12 casos de uso (formato RUP)
- Mockups de las 12 pantallas

Informe consolidado: `ENTREGABLE-1.pdf`

### Segundo entregable (implementación)

- Diagramas de diseño (modelo de dominio, casos de uso, clases, secuencia y
  entidad-relación)
- Aplicación web desarrollada en Django
- Despliegue en producción

## Tecnologías

- **Backend:** Python, Django
- **Base de datos:** SQLite
- **Frontend:** Plantillas de Django con CSS propio
- **Diagramas:** PlantUML
- **Prototipos:** Pencil

## Puesta en marcha

```bash
# 1. Entorno virtual e instalación de dependencias
python -m venv venv
venv\Scripts\activate          # En Linux o macOS: source venv/bin/activate
pip install -r requirements.txt

# 2. Base de datos
python manage.py migrate

# 3. Catálogo de películas y series
python manage.py loaddata fixtures/catalogo.json

# 4. Datos de demostración (usuarios, amistades y valoraciones)
python manage.py seed_demo

# 5. Servidor de desarrollo
python manage.py runserver
```

La aplicación queda disponible en `http://127.0.0.1:8000/`.

### Cuentas de demostración

| Usuario | Contraseña | Rol |
|---|---|---|
| `mariana` | `moviematch2026` | Usuario con amigos, valoraciones y listas |
| `admin` | `moviematch2026` | Administrador (acceso al panel) |

Los demás usuarios de prueba (`ana`, `luis`, `sofia`, `diego`, `valentina`,
`nicolas`, `maria`, `julian`) comparten la misma contraseña.

### Qué revisar

Recorrido sugerido para evaluar los 12 casos de uso (entrando como `mariana`):

1. **Inicio** – recomendaciones personalizadas con la explicación de por qué se
   sugiere cada título; el botón *Actualizar* las recalcula (CU-05).
2. **Catálogo** – grid de 60 películas y series con filtros por género y tipo
   (CU-06); clic en un título abre su ficha de detalle (CU-08).
3. **Valorar** – en la ficha de detalle, califica con estrellas y observa cómo
   cambian las recomendaciones al actualizar (CU-04).
4. **Perfil** – edición de datos y niveles de interés por género 1–5 (CU-03).
5. **Listas** – crear una lista, agregar y quitar contenido (CU-11, CU-12).
6. **Amigos** – enviar, aceptar o rechazar solicitudes de amistad (CU-07).
7. **Actividad** – historial de valoraciones del usuario (CU-09).

Entrando como `admin` se habilita la **gestión** (barra lateral):

- **Usuarios** – activar o suspender cuentas (CU-10).
- **Contenido** – publicar o retirar películas y series (CU-06 admin).
- **Métricas** – panel con estadísticas de uso.

### Regenerar el catálogo desde TMDB (opcional)

El catálogo ya viene cargado en `fixtures/catalogo.json`, por lo que la
aplicación **no necesita conexión a internet ni credenciales** para funcionar.
Si quieres reconstruirlo, crea un archivo `.env` en la raíz con tu clave de TMDB
y ejecuta el comando de importación:

```bash
# .env  (este archivo no se versiona)
TMDB_API_KEY=tu_clave_de_tmdb
```

```bash
python manage.py import_tmdb --peliculas 45 --series 15
python manage.py dumpdata catalog --indent 2 --output fixtures/catalogo.json
```

## Créditos

Los datos del catálogo (títulos, sinopsis, pósters y géneros) provienen de
**TMDB**.

> This product uses the TMDB API but is not endorsed or certified by TMDB.
