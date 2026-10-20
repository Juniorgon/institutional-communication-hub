from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from datetime import date
from apps.core.decorators.ratelimit import upload_rate_limit, excluir_rate_limit
from apps.dashboard.models import Aviso

@login_required
def avisos(request):

    avisos = Aviso.objects.all()

    titulo = request.GET.get('titulo')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if titulo:
        avisos = avisos.filter(
            titulo_aviso__icontains=titulo
        )

    if data_inicio:
        avisos = avisos.filter(
            data_publi__gte=data_inicio
        )

    if data_fim:
        avisos = avisos.filter(
            data_expi__lte=data_fim
        )

    avisos = avisos.order_by('-data_publi')

    return render(
        request,
        'admin/avisoinstadm.html',
        {
            'avisos': avisos,
            'titulo': titulo,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    )

@login_required
@permission_required('dashboard.add_aviso', raise_exception=True)
@upload_rate_limit
def criar_aviso(request):

    if request.method == 'POST':

        titulo = request.POST.get(
            'titulo'
        )

        data_publi = request.POST.get(
            'data_publi'
        )

        data_expi = request.POST.get(
            'data_expi'
        )

        Aviso.objects.create(

            titulo_aviso=titulo,


            data_publi=data_publi,

            data_expi=data_expi,

            status_aviso='ativo'

        )

    return redirect('avisosinst')

@login_required
@permission_required('dashboard.change_aviso', raise_exception=True)
@upload_rate_limit
def editar_aviso(request, id):

    aviso = get_object_or_404(
        Aviso,
        pk=id
    )

    if request.method == 'POST':

        aviso.titulo_aviso = request.POST.get(
            'titulo'
        )


        aviso.data_publi = request.POST.get(
            'data_publi'
        )

        aviso.data_expi = request.POST.get(
            'data_expi'
        )

        aviso.save()

    return redirect('avisosinst')

@login_required
@permission_required('dashboard.delete_aviso', raise_exception=True)
@require_POST
@excluir_rate_limit
def excluir_aviso(request, id):

    aviso = get_object_or_404(
        Aviso,
        pk=id
    )

    aviso.delete()

    return redirect('avisosinst')

