"""Panel de métricas de uso (CU-12)."""

from datetime import timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.views import es_administrador
from apps.catalog.models import ContenidoAudiovisual
from apps.ratings.models import Valoracion
from apps.recommendations.models import Recomendacion

PERIODOS = {"7": 7, "30": 30, "90": 90, "365": 365}


@login_required
@user_passes_test(es_administrador)
def panel(request):
    """CU-12: Consultar métricas de uso.

    RN-14: los indicadores se calculan de forma agregada, sin exponer datos
    personales individuales.
    """
    periodo = request.GET.get("periodo", "30")
    dias = PERIODOS.get(periodo, 30)
    desde = timezone.now() - timedelta(days=dias)

    valoraciones_periodo = Valoracion.objects.filter(fecha__gte=desde)

    metricas = [
        {
            "clave": "Usuarios activos",
            "valor": User.objects.filter(perfil__estado="ACTIVO").count(),
            "detalle": f"{User.objects.count()} registrados en total",
            "icono": "👥",
        },
        {
            "clave": "Recomendaciones",
            "valor": Recomendacion.objects.count(),
            "detalle": "vigentes en el sistema",
            "icono": "✨",
        },
        {
            "clave": "Valoraciones",
            "valor": Valoracion.objects.count(),
            "detalle": f"{valoraciones_periodo.count()} en el periodo",
            "icono": "⭐",
        },
        {
            "clave": "Contenidos",
            "valor": ContenidoAudiovisual.objects.filter(estado="PUBLICADO").count(),
            "detalle": f"{ContenidoAudiovisual.objects.filter(estado='RETIRADO').count()} retirados",
            "icono": "🎬",
        },
        {
            "clave": "Puntuación media",
            "valor": round(Valoracion.objects.aggregate(m=Avg("puntuacion"))["m"] or 0, 2),
            "detalle": "sobre 5 estrellas",
            "icono": "📈",
        },
    ]

    # Actividad por mes, para el gráfico de barras.
    por_mes = (
        Valoracion.objects.annotate(mes=TruncMonth("fecha"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )
    maximo = max([fila["total"] for fila in por_mes], default=1)
    grafico = [
        {
            "etiqueta": fila["mes"].strftime("%b %y") if fila["mes"] else "",
            "total": fila["total"],
            "altura": round(fila["total"] * 100 / maximo),
        }
        for fila in por_mes
    ]

    top_contenido = (
        ContenidoAudiovisual.objects.annotate(
            cuantas=Count("valoraciones"), promedio=Avg("valoraciones__puntuacion")
        )
        .filter(cuantas__gt=0)
        .order_by("-cuantas", "-promedio")[:5]
    )

    contexto = {
        "seccion": "admin_metricas",
        "es_admin": True,
        "metricas": metricas,
        "grafico": grafico,
        "top_contenido": top_contenido,
        "periodo": periodo,
        "periodos": [("7", "Últimos 7 días"), ("30", "Últimos 30 días"),
                     ("90", "Últimos 90 días"), ("365", "Último año")],
    }
    return render(request, "analytics/panel.html", contexto)
