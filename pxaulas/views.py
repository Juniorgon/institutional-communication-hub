from django.shortcuts import render
from django.http import JsonResponse
from apps.dashboard.models  import HorarioAula, Aviso
from datetime import  datetime, date
import json
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from apps.core.decorators.ratelimit import upload_rate_limit, excluir_rate_limit


from django.shortcuts import render
from apps.dashboard.models import Aviso


def pxaulas_publico(request, curso):

    hoje = date.today()

    avisos = Aviso.objects.filter(
        status_aviso='ativo',
        data_publi__lte=hoje,
        data_expi__gte=hoje
    ).order_by('-data_publi')[:5]

    templates = {

        "ADM": "aulasadm.html",
        "ADS": "aulas_ads.html",
        "TII": "aulas_tii.html",
        "TPG": "aulas_tpg.html"

    }

    return render(

        request,

        templates[curso],

        {
            "curso": curso,
            "avisos": avisos
        }
    )


def proximas_aulas(request, curso):
    return JsonResponse(obter_proximas_aulas(curso))


def obter_proximas_aulas(curso):

    agora = datetime.now()

    hora_atual = agora.strftime("%H:%M")

    # Monday = 0 no Python
    # seu banco aparentemente utiliza 1 = segunda
    dia_semana = agora.weekday() + 1

    horarios_manha = [
        ("08:20", "09:10"),
        ("09:10", "10:00"),
        ("10:20", "11:10"),
    ]

    horarios_tarde = [
        ("13:00", "13:50"),
        ("13:50", "14:40"),
        ("14:40", "15:50"),
        ("15:50", "16:40"),
        ("16:40", "17:30"),
        ("17:30", "18:20"),
    ]

    horarios_noite = [
        ("19:00", "19:50"),
        ("19:50", "20:40"),
        ("20:55", "21:45"),
        ("21:45", "22:35"),
        ("22:35", "23:25"),
    ]

    todos_horarios = (
        horarios_manha
        + horarios_tarde
        + horarios_noite
    )

    proximo_inicio = None
    proximo_fim = None

    for i, (inicio, fim) in enumerate(todos_horarios):

        # Se ainda não começou
        if hora_atual < inicio:
            proximo_inicio = inicio
            proximo_fim = fim
            break

        # Se estamos durante uma aula,
        # mostra a próxima
        if inicio <= hora_atual < fim:

            if i + 1 < len(todos_horarios):
                proximo_inicio, proximo_fim = todos_horarios[i + 1]

            break

    if not proximo_inicio:

        return {
            "horario": None,
            "dados": []
        }


    aulas = HorarioAula.objects.filter(
        curso=curso,
        horario=proximo_inicio,
        dia=dia_semana
    ).order_by(
        "ano_semestre",
        "turma"
    )


    dados = []

    for aula in aulas:

        dados.append({
            "turma": f"{aula.ano_semestre}{aula.turma or ''}",
            "materia": aula.nome_aula,
            "sala": aula.sala
        })


    return {
        "horario": f"{proximo_inicio} - {proximo_fim}",
        "dados": dados
    }

def tela_horarios(request):
    return render(request, "aulasadm.html")

def anos_equivalentes(ano):
    """Inclui os valores gravados pelo antigo formulário de horários."""
    equivalencias = {
        f"{numero} {tipo}": (f"{numero} {tipo}", f"{numero} Ano/Semestre")
        for numero in range(1, 4)
        for tipo in ("Ano", "Semestre")
    }
    return equivalencias.get(ano, (ano,))


def listar_horarios(request):

    curso = request.GET.get("curso")
    ano = request.GET.get("ano")
    turma = request.GET.get("turma")
    turno = request.GET.get("turno")
    sala = request.GET.get("sala")

    horarios = HorarioAula.objects.filter(
        curso=curso,
        ano_semestre__in=anos_equivalentes(ano),
        turno=turno,
        sala=sala
    )

    # ADS e TPG não usam turma
    if turma and curso not in ["ADS", "TPG"]:

        horarios = horarios.filter(turma=turma)

    dados = {}

    for h in horarios:

        chave = f"{h.horario}-{h.dia}"

        dados[chave] = h.nome_aula

    return JsonResponse(dados)


@login_required
@permission_required('dashboard.add_horarioaula', raise_exception=True)
@upload_rate_limit
def criar_horario(request):

    if request.method == "POST":

        dados = json.loads(request.body)

        HorarioAula.objects.create(
            curso=dados["curso"],
            ano_semestre=dados["ano"],
            turma=dados["turma"],
            turno=dados["turno"],
            sala=dados["sala"],
            horario=dados["horario"],
            dia=dados["dia"],
            nome_aula=dados["texto"]
        )

        return JsonResponse({"status": "ok"})

@login_required
@permission_required('dashboard.change_horarioaula', raise_exception=True)
@upload_rate_limit
def editar_horario(request):

    if request.method == "POST":

        dados = json.loads(request.body)

        horario = HorarioAula.objects.filter(
            curso=dados["curso"],
            ano_semestre__in=anos_equivalentes(dados["ano"]),
            turma=dados["turma"],
            turno=dados["turno"],
            sala=dados["sala"],
            horario=dados["horario"],
            dia=dados["dia"]
        ).first()

        # se existir -> edita
        if horario:

            horario.nome_aula = dados["texto"]

            horario.save()

        # se NÃO existir -> cria
        else:

            HorarioAula.objects.create(

                curso=dados["curso"],
                ano_semestre=dados["ano"],
                turma=dados["turma"],
                turno=dados["turno"],
                sala=dados["sala"],
                horario=dados["horario"],
                dia=dados["dia"],
                nome_aula=dados["texto"]
            )

        return JsonResponse({"status":"ok"})


@login_required
@permission_required('dashboard.delete_horarioaula', raise_exception=True)
@require_POST
@excluir_rate_limit
def excluir_horario(request):

    if request.method == "POST":

        dados = json.loads(request.body)

        HorarioAula.objects.filter(
            curso=dados["curso"],
            ano_semestre__in=anos_equivalentes(dados["ano"]),
            turma=dados["turma"],
            turno=dados["turno"],
            sala=dados["sala"],
            horario=dados["horario"],
            dia=dados["dia"]
        ).delete()

        return JsonResponse({"status": "ok"})
