# Especificación de Casos de Uso — MovieMatch

> Primer entregable · Asignatura: Calidad de Software 2025-2
> Plantilla basada en RUP (Rational Unified Process).
> Artefactos relacionados: [Modelo de Dominio](01-modelo-de-dominio.md) · [Diagrama de Casos de Uso](02-diagrama-casos-de-uso.md)

## Convenciones

- **CU-XX:** identificador de caso de uso. **FA:** flujo alternativo. **FE:** flujo de excepción. **RN:** regla de negocio.
- Prioridad y Frecuencia: `Alta` | `Media` | `Baja`.
- Todos los casos que requieren sesión incluyen implícitamente **CU-02 Iniciar sesión**.

---

# CU-01 · Registrarse

| Campo | Detalle |
|---|---|
| **Identificador** | CU-01 |
| **Nombre** | Registrarse |
| **Objetivo** | Permitir que una persona cree una cuenta en MovieMatch para acceder a las funcionalidades de la plataforma. |
| **Actor principal** | Usuario (visitante no registrado) |
| **Actores secundarios** | — |
| **Disparador** | El visitante selecciona "Crear cuenta" en la pantalla de inicio. |
| **Prioridad** | Alta |
| **Frecuencia de uso** | Media (una vez por usuario, picos en campañas de marketing) |

**Precondiciones**
- El visitante no tiene una sesión activa.
- El visitante dispone de un correo electrónico válido.

**Flujo principal**
1. El sistema muestra el formulario de registro (nombre, email, contraseña, confirmación).
2. El usuario completa los campos y acepta los términos y la política de tratamiento de datos.
3. El usuario confirma el registro.
4. El sistema valida formato y unicidad del email (RN-01).
5. El sistema cifra la contraseña y crea el `Usuario` con estado `ACTIVO` y un `Perfil` vacío asociado.
6. El sistema envía un correo de verificación y muestra confirmación.

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | En el paso 2, el usuario elige "Registrarse con red social"; el sistema obtiene los datos del proveedor OAuth y continúa en el paso 5. |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | Email ya registrado (RN-01): el sistema informa y solicita otro o sugiere iniciar sesión. |
| FE-02 | Contraseñas no coinciden o no cumplen la política: el sistema marca el error y no crea la cuenta. |
| FE-03 | Fallo del servicio de correo: la cuenta se crea pero se notifica que la verificación se reenviará. |

**Postcondiciones**
- Existe un nuevo `Usuario` con su `Perfil` asociado.
- Se registra el evento para métricas de adquisición (CU-12).

**Reglas de negocio**
- RN-01: El email es único en el sistema.
- RN-02: La contraseña debe cumplir la política mínima (≥8 caracteres, mayúscula, número).

**Requerimientos especiales (RNF)** · Cumplimiento GDPR: consentimiento explícito y cifrado de la contraseña. Tiempo de respuesta < 2 s.
**Suposiciones** · El usuario tiene acceso a su bandeja de correo.
**Dependencias** · Proveedor de email; proveedor OAuth (si FA-01).
**Restricciones** · Datos personales almacenados según normativa de protección de datos.
**Prototipos UI** · Mockup *Registro*.
**Casos relacionados** · CU-02, CU-03.

---

# CU-02 · Iniciar sesión

| Campo | Detalle |
|---|---|
| **Identificador** | CU-02 |
| **Nombre** | Iniciar sesión |
| **Objetivo** | Autenticar a un usuario registrado para darle acceso a sus funcionalidades. |
| **Actor principal** | Usuario |
| **Actores secundarios** | — |
| **Disparador** | El usuario selecciona "Iniciar sesión". |
| **Prioridad** | Alta |
| **Frecuencia de uso** | Alta |

**Precondiciones** · El usuario tiene una cuenta `ACTIVA`.

**Flujo principal**
1. El sistema muestra el formulario de inicio de sesión (email, contraseña).
2. El usuario ingresa sus credenciales y confirma.
3. El sistema valida las credenciales contra la cuenta.
4. El sistema crea la sesión y redirige al *home* con recomendaciones (CU-05).

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | El usuario elige "Iniciar con red social"; el sistema autentica vía OAuth y continúa en el paso 4. |
| FA-02 | El usuario selecciona "¿Olvidaste tu contraseña?"; el sistema envía enlace de restablecimiento. |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | Credenciales inválidas: el sistema informa sin revelar cuál campo falló. |
| FE-02 | Cuenta `SUSPENDIDA`/`INACTIVA`: el sistema deniega el acceso e informa el motivo. |
| FE-03 | Tras N intentos fallidos, el sistema aplica bloqueo temporal (RN-03). |

**Postcondiciones** · El usuario tiene una sesión activa.
**Reglas de negocio** · RN-03: tras 5 intentos fallidos se bloquea el acceso por 15 minutos.
**Requerimientos especiales (RNF)** · Transmisión cifrada (HTTPS); respuesta < 2 s.
**Suposiciones** · El usuario recuerda sus credenciales o usa OAuth.
**Dependencias** · Servicio de autenticación; proveedor OAuth.
**Restricciones** · No se almacenan contraseñas en texto plano.
**Prototipos UI** · Mockup *Login*.
**Casos relacionados** · CU-01; incluido por CU-03, CU-04, CU-05, CU-07, CU-08, CU-09.

---

# CU-03 · Gestionar perfil y preferencias

| Campo | Detalle |
|---|---|
| **Identificador** | CU-03 |
| **Nombre** | Gestionar perfil y preferencias |
| **Objetivo** | Permitir al usuario editar sus datos de perfil y sus preferencias de géneros para afinar las recomendaciones. |
| **Actor principal** | Usuario |
| **Disparador** | El usuario abre la sección "Mi perfil". |
| **Prioridad** | Alta |
| **Frecuencia de uso** | Media |

**Precondiciones** · Sesión activa (incluye CU-02).

**Flujo principal**
1. El sistema muestra los datos del `Perfil` y las `Preferencias` actuales.
2. El usuario edita alias, avatar, biografía y/o selecciona géneros de interés con su nivel.
3. El usuario guarda los cambios.
4. El sistema valida y persiste el `Perfil` y las `Preferencias`.
5. El sistema confirma y marca las recomendaciones para recálculo (CU-05).

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | El usuario sube un avatar; el sistema valida formato/tamaño y lo almacena. |
| FA-02 | El usuario solicita eliminar su cuenta (derecho GDPR); el sistema inicia el proceso de baja y anonimización. |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | Archivo de avatar inválido: el sistema rechaza la carga e informa. |
| FE-02 | Fallo al persistir: el sistema conserva los datos previos e informa el error. |

**Postcondiciones** · El `Perfil`/`Preferencias` quedan actualizados; las recomendaciones se recalcularán.
**Reglas de negocio** · RN-04: las preferencias influyen en el peso del algoritmo de recomendación.
**Requerimientos especiales (RNF)** · Usabilidad (SUS ≥ 80); respuesta < 2 s.
**Suposiciones** · El usuario conoce sus géneros preferidos.
**Dependencias** · Servicio de almacenamiento de archivos (avatar).
**Restricciones** · GDPR: derecho de acceso, rectificación y olvido.
**Prototipos UI** · Mockup *Perfil*.
**Casos relacionados** · CU-01, CU-05.

---

# CU-04 · Valorar película/serie

| Campo | Detalle |
|---|---|
| **Identificador** | CU-04 |
| **Nombre** | Valorar película/serie |
| **Objetivo** | Permitir al usuario calificar un contenido para enriquecer su historial y mejorar las recomendaciones. |
| **Actor principal** | Usuario |
| **Disparador** | El usuario selecciona "Valorar" en la ficha de un contenido. |
| **Prioridad** | Alta |
| **Frecuencia de uso** | Alta |

**Precondiciones** · Sesión activa; el contenido existe en el catálogo.

**Flujo principal**
1. El sistema muestra la ficha del `ContenidoAudiovisual` y el control de valoración (1–5) y comentario opcional.
2. El usuario asigna una puntuación y, opcionalmente, un comentario.
3. El usuario confirma.
4. El sistema valida el rango (RN-05) y registra/actualiza la `Valoración` (RN-06).
5. El sistema confirma y marca las recomendaciones para recálculo (CU-05).

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | El usuario edita una valoración previa; el sistema actualiza la existente. |
| FA-02 | El usuario elimina su valoración; el sistema la retira del historial. |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | Puntuación fuera de rango: el sistema rechaza y solicita un valor 1–5. |
| FE-02 | Contenido retirado del catálogo: el sistema impide valorar e informa. |

**Postcondiciones** · El historial de valoraciones del usuario queda actualizado.
**Reglas de negocio** · RN-05: puntuación entre 1 y 5. · RN-06: una sola valoración vigente por usuario y contenido.
**Requerimientos especiales (RNF)** · Respuesta < 2 s; confiabilidad (< 1 % de errores).
**Suposiciones** · El usuario ha visto el contenido.
**Dependencias** · Catálogo de contenido (CU-11).
**Restricciones** · Moderación de comentarios ofensivos.
**Prototipos UI** · Mockup *Detalle de película*.
**Casos relacionados** · CU-05, CU-06, CU-09.

---

# CU-05 · Recibir recomendaciones personalizadas

| Campo | Detalle |
|---|---|
| **Identificador** | CU-05 |
| **Nombre** | Recibir recomendaciones personalizadas |
| **Objetivo** | Ofrecer al usuario una lista de contenidos sugeridos a partir de su historial y las valoraciones de sus amigos. |
| **Actor principal** | Usuario |
| **Actores secundarios** | Motor de Recomendaciones (sistema) |
| **Disparador** | El usuario accede al *home* o solicita "Actualizar recomendaciones". |
| **Prioridad** | Alta (funcionalidad central del producto) |
| **Frecuencia de uso** | Alta |

**Precondiciones** · Sesión activa; existe historial de valoraciones y/o preferencias.

**Flujo principal**
1. El usuario accede al *home*.
2. El sistema solicita al **Motor de Recomendaciones** sugerencias para el usuario (`<<include>>`).
3. El motor analiza el historial del usuario, sus preferencias y las valoraciones de sus amigos `ACEPTADOS` (RN-07).
4. El motor devuelve un conjunto ordenado de `Recomendaciones` con su `score` y `motivo`.
5. El sistema muestra las recomendaciones en menos de 2 segundos (RNF).

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | Usuario nuevo sin historial (*cold start*): el motor recomienda por popularidad y géneros declarados en preferencias. |
| FA-02 | El usuario filtra las recomendaciones por género o por "lo que ven mis amigos". |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | El motor no responde a tiempo: el sistema muestra recomendaciones en caché o populares y registra el incidente. |
| FE-02 | No hay datos suficientes: el sistema invita al usuario a valorar contenido o definir preferencias. |

**Postcondiciones** · Se muestran y registran las recomendaciones generadas.
**Reglas de negocio** · RN-07: solo las valoraciones de amigos con `Amistad ACEPTADA` influyen en la recomendación.
**Requerimientos especiales (RNF)** · Tiempo de respuesta ≤ 2 s; disponibilidad 99.9 %; precisión del motor como métrica de calidad.
**Suposiciones** · El motor de IA está entrenado y disponible.
**Dependencias** · Motor de Recomendaciones; CU-03, CU-04, CU-07.
**Restricciones** · No exponer datos sensibles de amigos más allá de sus valoraciones públicas.
**Prototipos UI** · Mockup *Home / Recomendaciones*.
**Casos relacionados** · CU-04, CU-08 (extiende), CU-09 (extiende).

---

# CU-06 · Buscar/explorar catálogo

| Campo | Detalle |
|---|---|
| **Identificador** | CU-06 |
| **Nombre** | Buscar/explorar catálogo |
| **Objetivo** | Permitir al usuario localizar contenidos por texto, género u otros filtros. |
| **Actor principal** | Usuario |
| **Disparador** | El usuario usa la barra de búsqueda o navega por categorías. |
| **Prioridad** | Media |
| **Frecuencia de uso** | Alta |

**Precondiciones** · El catálogo contiene contenidos publicados.

**Flujo principal**
1. El usuario ingresa un término o selecciona filtros (género, año, tipo).
2. El sistema consulta el catálogo y devuelve resultados paginados.
3. El usuario selecciona un contenido para ver su ficha.
4. El sistema muestra el detalle (sinopsis, valoraciones, acción de valorar — extiende CU-04).

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | Búsqueda por voz o sugerencias automáticas mientras escribe. |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | Sin resultados: el sistema sugiere términos alternativos o contenido popular. |

**Postcondiciones** · Se muestra el resultado o la ficha seleccionada.
**Reglas de negocio** · RN-08: solo se listan contenidos con estado publicado.
**Requerimientos especiales (RNF)** · Respuesta < 2 s; compatibilidad multidispositivo.
**Suposiciones** · El índice de búsqueda está actualizado.
**Dependencias** · Catálogo (CU-11).
**Restricciones** · Resultados acordes a la clasificación por edad.
**Prototipos UI** · Mockup *Catálogo/Búsqueda*.
**Casos relacionados** · CU-04, CU-05.

---

# CU-07 · Gestionar solicitudes de amistad

| Campo | Detalle |
|---|---|
| **Identificador** | CU-07 |
| **Nombre** | Gestionar solicitudes de amistad |
| **Objetivo** | Permitir al usuario enviar, aceptar o rechazar solicitudes de amistad para construir su red social. |
| **Actor principal** | Usuario |
| **Actores secundarios** | Otro Usuario (destinatario) |
| **Disparador** | El usuario busca a otro usuario o abre "Solicitudes pendientes". |
| **Prioridad** | Media |
| **Frecuencia de uso** | Media |

**Precondiciones** · Sesión activa.

**Flujo principal**
1. El usuario busca a otro usuario por alias o email.
2. El usuario envía una solicitud; el sistema crea una `Amistad` con estado `PENDIENTE`.
3. El destinatario recibe la notificación y acepta o rechaza.
4. El sistema actualiza el estado a `ACEPTADA` o `RECHAZADA`.
5. Si es `ACEPTADA`, ambos quedan habilitados para ver sus valoraciones (CU-09) e influir en recomendaciones (CU-05).

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | El usuario elimina una amistad existente; el sistema la retira. |
| FA-02 | El usuario bloquea a otro; el sistema fija estado `BLOQUEADA`. |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | Ya existe una amistad o solicitud: el sistema lo informa y no duplica. |
| FE-02 | Usuario destinatario inexistente o inactivo: el sistema informa. |

**Postcondiciones** · La relación de `Amistad` queda en el estado correspondiente.
**Reglas de negocio** · RN-09: una `Amistad` es única entre dos usuarios. · RN-07 (influye en recomendaciones).
**Requerimientos especiales (RNF)** · Notificaciones; respuesta < 2 s.
**Suposiciones** · Ambos usuarios están registrados.
**Dependencias** · Servicio de notificaciones.
**Restricciones** · Privacidad: no exponer email completo en resultados de búsqueda.
**Prototipos UI** · Mockup *Amigos*.
**Casos relacionados** · CU-08, CU-09, CU-05.

---

# CU-08 · Compartir lista de recomendaciones

| Campo | Detalle |
|---|---|
| **Identificador** | CU-08 |
| **Nombre** | Compartir lista de recomendaciones |
| **Objetivo** | Permitir al usuario crear y compartir listas curadas de contenidos con sus amigos. |
| **Actor principal** | Usuario |
| **Disparador** | El usuario selecciona "Crear/compartir lista". |
| **Prioridad** | Media |
| **Frecuencia de uso** | Media |

**Precondiciones** · Sesión activa; el usuario tiene amigos `ACEPTADOS` o desea lista pública.

**Flujo principal**
1. El usuario crea una `ListaDeRecomendaciones` (nombre, descripción, visibilidad).
2. El usuario agrega contenidos desde el catálogo o desde sus recomendaciones (extiende CU-05).
3. El usuario elige compartirla con amigos seleccionados o hacerla pública.
4. El sistema persiste la lista y notifica a los destinatarios.

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | El usuario edita o elimina una lista existente. |
| FA-02 | El usuario comparte mediante enlace público. |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | Lista vacía al compartir: el sistema solicita agregar al menos un contenido. |
| FE-02 | Destinatario sin amistad aceptada: el sistema impide compartir de forma privada. |

**Postcondiciones** · La lista queda creada y compartida según la visibilidad elegida.
**Reglas de negocio** · RN-10: una lista privada solo es visible para amigos aceptados.
**Requerimientos especiales (RNF)** · Respuesta < 2 s; usabilidad.
**Suposiciones** · El usuario tiene contenidos para curar.
**Dependencias** · CU-05, CU-06, CU-07; notificaciones.
**Restricciones** · Contenido conforme a la clasificación por edad de los destinatarios.
**Prototipos UI** · Mockup *Listas*.
**Casos relacionados** · CU-05, CU-07, CU-09.

---

# CU-09 · Ver valoraciones de amigos

| Campo | Detalle |
|---|---|
| **Identificador** | CU-09 |
| **Nombre** | Ver valoraciones de amigos |
| **Objetivo** | Permitir al usuario consultar qué han valorado sus amigos para apoyar sus decisiones de visualización. |
| **Actor principal** | Usuario |
| **Disparador** | El usuario abre "Actividad de amigos" o la ficha de un contenido. |
| **Prioridad** | Media |
| **Frecuencia de uso** | Media |

**Precondiciones** · Sesión activa; el usuario tiene amistades `ACEPTADAS`.

**Flujo principal**
1. El usuario abre la actividad social.
2. El sistema recupera las `Valoraciones` recientes de los amigos `ACEPTADOS` (RN-07).
3. El sistema muestra contenidos valorados, puntuación y comentario.
4. El usuario puede abrir la ficha (CU-06) o valorar (CU-04).

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | El usuario filtra por un amigo específico. |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | Sin amigos o sin actividad: el sistema sugiere agregar amigos (CU-07). |

**Postcondiciones** · Se muestran las valoraciones de los amigos.
**Reglas de negocio** · RN-07: solo amigos con amistad aceptada. · RN-11: respetar la visibilidad de cada valoración.
**Requerimientos especiales (RNF)** · Respuesta < 2 s; privacidad.
**Suposiciones** · Los amigos han valorado contenido.
**Dependencias** · CU-04, CU-07.
**Restricciones** · No mostrar valoraciones marcadas como privadas.
**Prototipos UI** · Mockup *Actividad de amigos*.
**Casos relacionados** · CU-04, CU-05, CU-07.

---

# CU-10 · Gestionar usuarios

| Campo | Detalle |
|---|---|
| **Identificador** | CU-10 |
| **Nombre** | Gestionar usuarios |
| **Objetivo** | Permitir al administrador consultar, suspender, reactivar o eliminar cuentas de usuario. |
| **Actor principal** | Administrador |
| **Disparador** | El administrador abre el módulo "Usuarios" del panel. |
| **Prioridad** | Alta |
| **Frecuencia de uso** | Media |

**Precondiciones** · Sesión activa con rol Administrador.

**Flujo principal**
1. El administrador consulta el listado de usuarios con filtros (estado, fecha, rol).
2. El sistema muestra los usuarios paginados.
3. El administrador selecciona un usuario y una acción (ver detalle, suspender, reactivar, eliminar).
4. El sistema valida la acción y actualiza el `estado` del `Usuario`.
5. El sistema registra la acción para auditoría.

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | Suspensión por incumplimiento: el sistema fija estado `SUSPENDIDO` y notifica al usuario. |
| FA-02 | Eliminación por solicitud GDPR: el sistema anonimiza/elimina los datos personales. |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | Acción sin privilegios suficientes: el sistema la deniega (RN-12). |
| FE-02 | Usuario inexistente: el sistema informa. |

**Postcondiciones** · El estado del usuario queda actualizado y auditado.
**Reglas de negocio** · RN-12: solo `SUPERADMIN` puede eliminar cuentas; `MODERADOR` solo suspende.
**Requerimientos especiales (RNF)** · Auditoría; seguridad (control de acceso por rol).
**Suposiciones** · Existen usuarios en el sistema.
**Dependencias** · Servicio de auditoría; notificaciones.
**Restricciones** · GDPR para eliminación de datos.
**Prototipos UI** · Mockup *Admin · Usuarios*.
**Casos relacionados** · CU-01, CU-12.

---

# CU-11 · Gestionar contenido

| Campo | Detalle |
|---|---|
| **Identificador** | CU-11 |
| **Nombre** | Gestionar contenido (catálogo) |
| **Objetivo** | Permitir al administrador crear, editar, publicar o retirar películas y series del catálogo. |
| **Actor principal** | Administrador |
| **Disparador** | El administrador abre el módulo "Contenido" del panel. |
| **Prioridad** | Alta |
| **Frecuencia de uso** | Media |

**Precondiciones** · Sesión activa con rol Administrador.

**Flujo principal**
1. El administrador consulta el catálogo con filtros.
2. El administrador crea o edita un `ContenidoAudiovisual` (Película/Serie) con sus datos y géneros.
3. El administrador define la visibilidad (publicado/retirado).
4. El sistema valida y persiste el contenido.
5. El sistema actualiza el índice de búsqueda (CU-06).

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | Carga masiva por importación de archivo/API externa de metadatos. |
| FA-02 | Retiro de contenido: el sistema lo oculta del catálogo conservando el historial. |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | Datos obligatorios faltantes: el sistema rechaza el guardado. |
| FE-02 | Contenido duplicado: el sistema advierte antes de crear. |

**Postcondiciones** · El catálogo y el índice de búsqueda quedan actualizados.
**Reglas de negocio** · RN-13: un contenido retirado no aparece en búsquedas ni recomendaciones, pero conserva sus valoraciones históricas.
**Requerimientos especiales (RNF)** · Integridad de datos; respuesta < 2 s.
**Suposiciones** · El administrador dispone de los metadatos.
**Dependencias** · Servicio de indexación; API externa (si FA-01).
**Restricciones** · Derechos de autor / licencias de las imágenes.
**Prototipos UI** · Mockup *Admin · Contenido*.
**Casos relacionados** · CU-04, CU-06.

---

# CU-12 · Consultar métricas de uso

| Campo | Detalle |
|---|---|
| **Identificador** | CU-12 |
| **Nombre** | Consultar métricas de uso |
| **Objetivo** | Permitir al administrador visualizar indicadores de uso y desempeño para la toma de decisiones. |
| **Actor principal** | Administrador |
| **Disparador** | El administrador abre el módulo "Métricas/Dashboard". |
| **Prioridad** | Media |
| **Frecuencia de uso** | Media |

**Precondiciones** · Sesión activa con rol Administrador.

**Flujo principal**
1. El administrador selecciona el periodo y el tipo de métrica (usuarios activos, recomendaciones generadas, valoraciones, tiempo de respuesta).
2. El sistema agrega los datos y construye las `MetricasDeUso`.
3. El sistema muestra tableros con gráficos y tablas.
4. El administrador exporta el informe (opcional).

**Flujos alternativos**

| ID | Descripción |
|---|---|
| FA-01 | El administrador exporta a CSV/PDF. |
| FA-02 | El administrador configura alertas por umbral (p. ej. tasa de error > 1 %). |

**Flujos de excepción**

| ID | Descripción |
|---|---|
| FE-01 | Sin datos en el periodo: el sistema muestra estado vacío. |
| FE-02 | Fallo al agregar datos: el sistema informa y registra el incidente. |

**Postcondiciones** · Se presentan las métricas del periodo seleccionado.
**Reglas de negocio** · RN-14: las métricas se calculan sobre datos anonimizados/agregados.
**Requerimientos especiales (RNF)** · Confiabilidad (< 1 % de errores); disponibilidad 99.9 %.
**Suposiciones** · Existen eventos registrados.
**Dependencias** · Almacén de eventos/analítica.
**Restricciones** · GDPR: no exponer datos personales individuales en métricas agregadas.
**Prototipos UI** · Mockup *Admin · Dashboard*.
**Casos relacionados** · CU-10, CU-11, CU-05.

---

## Matriz de trazabilidad CU ↔ Requisitos de Calidad

| Caso de uso | RNF / Calidad asociado |
|---|---|
| CU-05 Recomendaciones | Rendimiento ≤ 2 s; disponibilidad 99.9 %; precisión del motor |
| CU-01, CU-02, CU-03 | Seguridad/GDPR; usabilidad (SUS ≥ 80) |
| CU-04, CU-12 | Confiabilidad (< 1 % de errores) |
| Todos | Compatibilidad multidispositivo/navegador; mantenibilidad |
