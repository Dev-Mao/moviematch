# Modelo de Dominio — MovieMatch

> Primer entregable · Asignatura: Calidad de Software 2025-2
> Diagrama fuente: [`diagrams/modelo-de-dominio.puml`](../diagrams/modelo-de-dominio.puml)

## 1. Propósito

El Modelo de Dominio captura los **conceptos del negocio** de MovieMatch, sus
atributos y las relaciones entre ellos, independientemente de la tecnología de
implementación. Sirve como vocabulario común (lenguaje ubicuo) para el resto de
artefactos: casos de uso, especificaciones y mockups.

## 2. Diagrama

> Si tienes la extensión **PlantUML** en VSCode, abre el `.puml` y usa
> `Alt+D` para previsualizar. Alternativamente se puede exportar a PNG/SVG.

![Modelo de Dominio](../diagrams/modelo-de-dominio.png)

```plantuml
' Ver archivo completo en diagrams/modelo-de-dominio.puml
```

## 3. Entidades del dominio

| Entidad | Descripción | Atributos clave |
|---|---|---|
| **Usuario** | Persona registrada en la plataforma. | nombreCompleto, email, contrasenaHash, fechaRegistro, estado |
| **Administrador** | Especialización de Usuario con permisos de gestión. | nivelAcceso |
| **Perfil** | Información personal y de personalización del usuario (1:1). | alias, avatarUrl, biografia |
| **Género** | Categoría de clasificación del contenido (Acción, Drama…). | nombre |
| **Preferencia** | Clase de asociación Perfil↔Género con peso de interés. | nivelInteres |
| **ContenidoAudiovisual** | Abstracción de obra audiovisual. | titulo, sinopsis, anioEstreno, posterUrl, clasificacion |
| **Película** | Contenido de un solo bloque. | duracionMin |
| **Serie** | Contenido episódico. | numTemporadas, numEpisodios, enEmision |
| **Valoración** | Calificación que un usuario da a un contenido. | puntuacion (1–5), comentario, fecha |
| **ListaDeRecomendaciones** | Colección curada y compartible de contenidos. | nombre, descripcion, esPublica |
| **Amistad** | Relación social entre dos usuarios. | estado, fechaSolicitud, fechaAceptacion |
| **MotorDeRecomendaciones** | Servicio de IA que produce recomendaciones. | version, algoritmo |
| **Recomendación** | Sugerencia generada para un usuario sobre un contenido. | score, motivo, fechaGenerada |
| **MetricaDeUso** | Indicador agregado para el panel administrativo. | tipo, valor, fechaCorte |

## 4. Relaciones principales

| Relación | Tipo | Cardinalidad |
|---|---|---|
| Usuario — Perfil | Composición | 1 — 1 |
| Usuario ◁ Administrador | Generalización | — |
| ContenidoAudiovisual ◁ Película / Serie | Generalización | — |
| Perfil — Género (vía Preferencia) | Asociación | 1 — * — 1 |
| ContenidoAudiovisual — Género | Asociación | * — * |
| Usuario — Valoración — Contenido | Asociación | 1 — * — 1 |
| Usuario — ListaDeRecomendaciones | Asociación | 1 — * |
| Lista — Contenido | Asociación | * — * |
| Usuario — Amistad — Usuario | Asociación reflexiva | * — * |
| MotorDeRecomendaciones — Recomendación | Asociación | 1 — * |
| Usuario — Recomendación — Contenido | Asociación | 1 — * — 1 |
| Administrador — MetricaDeUso | Asociación | 1 — * |

## 5. Enumeraciones

- **EstadoUsuario:** `ACTIVO`, `INACTIVO`, `SUSPENDIDO`
- **EstadoAmistad:** `PENDIENTE`, `ACEPTADA`, `RECHAZADA`, `BLOQUEADA`
- **NivelAcceso:** `MODERADOR`, `SUPERADMIN`

## 6. Reglas de dominio relevantes

- RN-D1: Un `email` es único por `Usuario`.
- RN-D2: La `puntuacion` de una `Valoración` está en el rango 1–5.
- RN-D3: Un `Usuario` solo puede tener **una** `Valoración` vigente por `Contenido`.
- RN-D4: Una `Amistad` es válida solo cuando su `estado = ACEPTADA` para que las
  valoraciones del amigo influyan en las recomendaciones.
- RN-D5: Una `Recomendación` siempre es generada por el `MotorDeRecomendaciones`,
  nunca creada manualmente por un usuario.
