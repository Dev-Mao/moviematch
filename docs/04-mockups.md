# Mockups (Prototipos de Interfaz) — MovieMatch

> Primer entregable · Asignatura: Calidad de Software 2025-2
> Archivo fuente: [`mockups/moviematch.pen`](../mockups/moviematch.pen) (editor **Pencil**)

## 1. Propósito

Los mockups son prototipos de alta fidelidad de las pantallas clave de
MovieMatch. Cada pantalla soporta uno o más casos de uso y materializa los
requisitos no funcionales de **usabilidad** y **consistencia** definidos en el
caso de estudio.

## 2. Sistema de diseño

Diseñado con un **tema oscuro cinematográfico**, apropiado para una plataforma
de contenido audiovisual.

| Token | Valor | Uso |
|---|---|---|
| `--background` | `#0E1117` | Fondo de la app |
| `--card` / `--card-elevated` | `#171C26` / `#1F2632` | Tarjetas y superficies |
| `--foreground` | `#F5F7FA` | Texto principal |
| `--muted-foreground` | `#9AA4B2` | Texto secundario |
| `--border` | `#2A313D` | Bordes y divisores |
| `--primary` | `#7C5CFC` (violeta) | Acción principal, acentos, enlaces |
| `--rating` | `#F5B301` (dorado) | Estrellas de valoración |
| `--color-success/-warning/-error` | verde / amarillo / rojo | Estados |
| Tipografías | **Poppins** (títulos) · **Inter** (texto) | — |

**Componentes reutilizables** (10): `Button/Primary`, `Button/Outline`,
`Button/Ghost`, `Brand/Logo`, `Badge`, `Input/Field`, `Rating/Stars`,
`Card/Poster`, `Nav/Item`, `Avatar`. Cambiar un token (p. ej. el color de
acento) se propaga automáticamente a todas las pantallas.

## 3. Inventario de pantallas y trazabilidad con Casos de Uso

| # | Pantalla | Caso(s) de uso | Contenido principal |
|---|---|---|---|
| 1 | **Login** | CU-02 | Panel hero + formulario de acceso, login social, recuperar contraseña |
| 2 | **Registro** | CU-01 | Formulario de alta, aceptación de términos (GDPR), login social |
| 3 | **Home / Recomendaciones** | CU-05 | Banner destacado, "Recomendado para ti", "Lo que ven tus amigos" |
| 4 | **Detalle de película** | CU-04, CU-06 | Backdrop, ficha técnica, valoración propia, valoraciones de amigos |
| 5 | **Catálogo / Búsqueda** | CU-06 | Búsqueda, filtros, grilla de resultados |
| 6 | **Perfil y Preferencias** | CU-03 | Datos personales, biografía, géneros favoritos |
| 7 | **Amigos** | CU-07 | Solicitudes pendientes (aceptar/rechazar), lista de amigos |
| 8 | **Mis listas** | CU-08 | Listas curadas, visibilidad (pública/privada/compartida), crear lista |
| 9 | **Actividad de amigos** | CU-09 | Feed de valoraciones de amigos, popular entre amigos |
| 10 | **Admin · Dashboard de Métricas** | CU-12 | Tarjetas de métricas, gráfico de actividad, contenido más recomendado |
| 11 | **Admin · Gestión de Usuarios** | CU-10 | Tabla de usuarios, estados, acciones (editar/suspender), paginación |
| 12 | **Admin · Gestión de Contenido** | CU-11 | Tabla de catálogo, tipo, estado (publicado/retirado), acciones |

> Nota: el CU-12 aparece en la pantalla 10; las 11 pantallas cubren los 12 casos
> de uso (CU-04 y CU-06 comparten la pantalla de Detalle/Catálogo).

## 4. Cómo visualizar y exportar

1. Abre [`mockups/moviematch.pen`](../mockups/moviematch.pen) con la extensión
   **Pencil** en VSCode.
2. Usa **Zoom to fit** para ver todo el lienzo: la fila superior contiene los
   componentes reutilizables; debajo están las 11 pantallas etiquetadas
   "Pantalla · …".
3. Para el informe final, puedes exportar cada frame como **PNG** desde Pencil.

## 5. Consideraciones de calidad reflejadas en el diseño

- **Usabilidad (SUS ≥ 80):** navegación lateral consistente, jerarquía visual
  clara, una acción primaria por pantalla, estados visibles (badges, vacíos).
- **Consistencia / mantenibilidad:** todo se construye con tokens y componentes
  reutilizables; un cambio de marca se propaga globalmente.
- **GDPR:** la pantalla de Registro incluye consentimiento explícito de términos
  y política de datos.
- **Responsividad:** diseñado a 1440px (desktop); la estructura de columnas y la
  navegación lateral degradan a una sola columna en móvil/tablet (definido en
  los RNF).
