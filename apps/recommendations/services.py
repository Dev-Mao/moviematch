"""Motor de recomendaciones (CU-05).

Implementa un algoritmo híbrido que combina cuatro señales:

1. Preferencias declaradas: los géneros que el usuario marcó como favoritos,
   ponderados por su nivel de interés (RN-04).
2. Historial: los géneros de los contenidos que el usuario valoró alto.
3. Amigos: las valoraciones de sus amistades aceptadas (RN-07).
4. Popularidad: la valoración promedio global, usada como respaldo y para
   resolver el arranque en frío (FA-01 del CU-05).

El resultado se persiste como objetos Recomendacion (RN-D5: las recomendaciones
siempre las genera el motor, nunca se crean a mano).
"""

from django.db import transaction
from django.db.models import Avg, Count

from apps.accounts.models import Amistad
from apps.catalog.models import ContenidoAudiovisual
from apps.ratings.models import Valoracion

from .models import Recomendacion

# Pesos de cada señal. Suman 1.0.
PESO_PREFERENCIAS = 0.35
PESO_AMIGOS = 0.30
PESO_HISTORIAL = 0.25
PESO_POPULARIDAD = 0.10

# A partir de esta puntuación se considera que un contenido "le gustó" al usuario.
PUNTUACION_POSITIVA = 4

VERSION = "1.0"
ALGORITMO = "híbrido: preferencias + historial + amigos + popularidad"


class MotorDeRecomendaciones:
    """Genera recomendaciones personalizadas para un usuario."""

    def __init__(self, usuario):
        self.usuario = usuario

    # ------------------------------------------------------------- Interfaz

    @transaction.atomic
    def generar(self, limite=24):
        """Recalcula y persiste las recomendaciones del usuario.

        Devuelve la lista de Recomendacion creadas, ordenadas de mayor a menor
        puntuación.
        """
        candidatos = self._candidatos()
        if not candidatos:
            Recomendacion.objects.filter(usuario=self.usuario).delete()
            return []

        preferencias = self._preferencias()
        historial = self._afinidad_por_historial()
        amigos = self._valoraciones_de_amigos()
        popularidad = self._popularidad()

        calculadas = []
        for contenido in candidatos:
            generos = [g.id for g in contenido.generos.all()]
            señales = {
                "preferencias": self._puntuar_generos(generos, preferencias),
                "historial": self._puntuar_generos(generos, historial),
                "amigos": amigos.get(contenido.id, {}).get("score", 0.0),
                "popularidad": popularidad.get(contenido.id, 0.0),
            }
            score = (
                señales["preferencias"] * PESO_PREFERENCIAS
                + señales["amigos"] * PESO_AMIGOS
                + señales["historial"] * PESO_HISTORIAL
                + señales["popularidad"] * PESO_POPULARIDAD
            )
            if score <= 0:
                continue
            origen, motivo = self._explicar(señales, contenido, amigos, preferencias)
            calculadas.append((score, contenido, origen, motivo))

        calculadas.sort(key=lambda item: item[0], reverse=True)
        calculadas = calculadas[:limite]

        Recomendacion.objects.filter(usuario=self.usuario).delete()
        recomendaciones = Recomendacion.objects.bulk_create(
            [
                Recomendacion(
                    usuario=self.usuario,
                    contenido=contenido,
                    score=round(score, 4),
                    origen=origen,
                    motivo=motivo,
                )
                for score, contenido, origen, motivo in calculadas
            ]
        )
        return recomendaciones

    # ------------------------------------------------------------- Candidatos

    def _candidatos(self):
        """Contenido publicado que el usuario todavía no ha valorado.

        RN-08 y RN-13: el contenido retirado no se recomienda.
        """
        ya_valorados = Valoracion.objects.filter(usuario=self.usuario).values_list(
            "contenido_id", flat=True
        )
        return list(
            ContenidoAudiovisual.objects.filter(
                estado=ContenidoAudiovisual.Estado.PUBLICADO
            )
            .exclude(id__in=ya_valorados)
            .prefetch_related("generos")
        )

    # --------------------------------------------------------------- Señales

    def _preferencias(self):
        """Devuelve {genero_id: peso normalizado} según el nivel de interés."""
        preferencias = self.usuario.perfil.preferencias.all() if hasattr(self.usuario, "perfil") else []
        return {p.genero_id: p.nivel_interes / 5 for p in preferencias}

    def _afinidad_por_historial(self):
        """Devuelve {genero_id: peso} según los géneros que el usuario valoró alto."""
        positivas = Valoracion.objects.filter(
            usuario=self.usuario, puntuacion__gte=PUNTUACION_POSITIVA
        ).prefetch_related("contenido__generos")

        conteo = {}
        for valoracion in positivas:
            for genero in valoracion.contenido.generos.all():
                conteo[genero.id] = conteo.get(genero.id, 0) + 1

        if not conteo:
            return {}
        maximo = max(conteo.values())
        return {genero_id: veces / maximo for genero_id, veces in conteo.items()}

    def _valoraciones_de_amigos(self):
        """Devuelve {contenido_id: {score, promedio, cantidad}} de los amigos aceptados.

        RN-07: solo cuentan las amistades en estado aceptado.
        """
        amistades = Amistad.objects.de_usuario(self.usuario).aceptadas()
        ids_amigos = [
            amistad.otro_usuario(self.usuario).id for amistad in amistades
        ]
        if not ids_amigos:
            return {}

        agregados = (
            Valoracion.objects.filter(usuario_id__in=ids_amigos)
            .values("contenido_id")
            .annotate(promedio=Avg("puntuacion"), cantidad=Count("id"))
        )

        resultado = {}
        for fila in agregados:
            # Normaliza el promedio de 1..5 al rango 0..1.
            calidad = (fila["promedio"] - 1) / 4
            # La confianza crece con el número de amigos que lo valoraron.
            confianza = min(fila["cantidad"] / 3, 1.0)
            resultado[fila["contenido_id"]] = {
                "score": calidad * confianza,
                "promedio": fila["promedio"],
                "cantidad": fila["cantidad"],
            }
        return resultado

    def _popularidad(self):
        """Devuelve {contenido_id: score} según la valoración promedio global."""
        agregados = (
            Valoracion.objects.values("contenido_id")
            .annotate(promedio=Avg("puntuacion"), cantidad=Count("id"))
            .filter(cantidad__gte=2)
        )
        return {fila["contenido_id"]: (fila["promedio"] - 1) / 4 for fila in agregados}

    # ----------------------------------------------------------- Utilidades

    @staticmethod
    def _puntuar_generos(generos, pesos):
        """Promedia el peso de los géneros del contenido que le interesan al usuario."""
        if not generos or not pesos:
            return 0.0
        coincidencias = [pesos.get(genero_id, 0.0) for genero_id in generos]
        return sum(coincidencias) / len(coincidencias)

    def _explicar(self, señales, contenido, amigos, preferencias):
        """Determina el origen dominante y redacta el motivo mostrado al usuario."""
        aportes = {
            Recomendacion.Origen.PREFERENCIAS: señales["preferencias"] * PESO_PREFERENCIAS,
            Recomendacion.Origen.AMIGOS: señales["amigos"] * PESO_AMIGOS,
            Recomendacion.Origen.HISTORIAL: señales["historial"] * PESO_HISTORIAL,
            Recomendacion.Origen.POPULARIDAD: señales["popularidad"] * PESO_POPULARIDAD,
        }
        origen = max(aportes, key=aportes.get)

        if origen == Recomendacion.Origen.AMIGOS:
            datos = amigos.get(contenido.id, {})
            cantidad = datos.get("cantidad", 0)
            plural = "amigos" if cantidad != 1 else "amigo"
            return origen, f"A {cantidad} de tus {plural} les gustó"

        if origen == Recomendacion.Origen.PREFERENCIAS:
            nombres = [g.nombre for g in contenido.generos.all() if g.id in preferencias]
            if nombres:
                return origen, f"Porque te gusta {nombres[0]}"
            return origen, "Por tus géneros preferidos"

        if origen == Recomendacion.Origen.HISTORIAL:
            nombres = [g.nombre for g in contenido.generos.all()]
            if nombres:
                return origen, f"Porque valoraste bien otras de {nombres[0]}"
            return origen, "Por tu historial de valoraciones"

        return origen, "Popular en MovieMatch"
