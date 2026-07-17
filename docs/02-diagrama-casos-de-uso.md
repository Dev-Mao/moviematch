# Diagrama de Casos de Uso — MovieMatch

> Primer entregable · Asignatura: Calidad de Software 2025-2
> Diagrama fuente: [`diagrams/casos-de-uso.puml`](../diagrams/casos-de-uso.puml)

## 1. Propósito

El Diagrama de Casos de Uso muestra el **alcance funcional** del sistema: qué
actores interactúan con MovieMatch y qué objetivos (casos de uso) persiguen.

## 2. Diagrama

![Casos de Uso](../diagrams/casos-de-uso.png)

```plantuml
' Ver archivo completo en diagrams/casos-de-uso.puml
```

## 3. Actores

| Actor | Tipo | Descripción |
|---|---|---|
| **Usuario** | Principal (humano) | Persona registrada que valora contenido, recibe recomendaciones e interactúa socialmente. El *amigo* es otro Usuario vinculado por una Amistad aceptada. |
| **Administrador** | Principal (humano) | Especialización de Usuario; gestiona usuarios, contenido y consulta métricas. Hereda los CU del Usuario. |
| **Motor de Recomendaciones** | Sistema/secundario | Servicio de IA invocado por el sistema para generar recomendaciones. |

## 4. Inventario de Casos de Uso

| ID | Caso de Uso | Actor principal |
|---|---|---|
| CU-01 | Registrarse | Usuario |
| CU-02 | Iniciar sesión | Usuario |
| CU-03 | Gestionar perfil y preferencias | Usuario |
| CU-04 | Valorar película/serie | Usuario |
| CU-05 | Recibir recomendaciones personalizadas | Usuario |
| CU-06 | Buscar/explorar catálogo | Usuario |
| CU-07 | Gestionar solicitudes de amistad | Usuario |
| CU-08 | Compartir lista de recomendaciones | Usuario |
| CU-09 | Ver valoraciones de amigos | Usuario |
| CU-10 | Gestionar usuarios | Administrador |
| CU-11 | Gestionar contenido | Administrador |
| CU-12 | Consultar métricas de uso | Administrador |

## 5. Relaciones del diagrama

- **Generalización:** `Administrador ▷ Usuario` — el administrador puede ejecutar
  también los casos de uso del usuario.
- **`<<include>>`** (obligatorio): los casos que requieren sesión activa incluyen
  **CU-02 Iniciar sesión** (CU-03, CU-04, CU-05, CU-07, CU-08, CU-09).
- **`<<include>>`**: **CU-05** incluye al **Motor de Recomendaciones** para
  producir las sugerencias.
- **`<<extend>>`** (opcional): **CU-08** y **CU-09** extienden a **CU-05** (desde
  la pantalla de recomendaciones se puede compartir lista o ver valoraciones de
  amigos); **CU-04** extiende a **CU-06** (desde el catálogo se puede valorar).

## 6. Trazabilidad con requisitos funcionales

| Requisito funcional (caso de estudio) | Casos de uso que lo cubren |
|---|---|
| Registro y creación de perfil | CU-01, CU-03 |
| Guardar preferencias y valoraciones | CU-03, CU-04 |
| Motor de recomendaciones (historial + amigos) | CU-05 |
| Panel de control del administrador | CU-10, CU-11, CU-12 |
| Interacción entre amigos / compartir listas | CU-07, CU-08, CU-09 |
