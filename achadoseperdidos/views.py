from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from .models import ItemAchado
from apps.core.ciclos import obter_ciclo, paginar_por_ciclo
from apps.dashboard.models import Aviso
from datetime import date
from apps.core.decorators.ratelimit import upload_rate_limit, excluir_rate_limit




def achados_publico(request):

    itens = ItemAchado.objects.order_by('-criado_em', '-pk')
    por_ciclo = 'ciclo' in request.GET
    if por_ciclo:
        itens = paginar_por_ciclo(itens, obter_ciclo(request))

    hoje = date.today()

    avisos = Aviso.objects.filter(
        status_aviso='ativo',
        data_publi__lte=hoje,
        data_expi__gte=hoje
    ).order_by('-data_publi')[:5]
    
    contexto = {

        'itens': itens,
        'por_ciclo': por_ciclo,
        'avisos': avisos

    }

    return render(

        request,

        'achadospublic.html',

        contexto

    )


@login_required
def achados(request):

    itens = ItemAchado.objects.all()

    nome = request.GET.get('nome')
    if nome:

        itens = itens.filter(nome__icontains=nome)
    contexto = {

        'itens': itens

    }

    return render(
        request,
        'admin/achadoseperdidos.html',
        contexto
    )

@login_required
@permission_required('achadoseperdidos.add_itemachado', raise_exception=True)
@upload_rate_limit
def criar_item(request):

    if request.method == 'POST':

        nome = request.POST.get('nome')

        imagem = request.FILES.get('imagem')

        ItemAchado.objects.create(

            nome=nome,

            imagem=imagem

        )

        messages.success(
            request,
            'Item cadastrado com sucesso.'
        )

    return redirect('achados')

@login_required
@permission_required('achadoseperdidos.change_itemachado', raise_exception=True)
@upload_rate_limit
def editar_item(request, id):

    item = get_object_or_404(
        ItemAchado,
        id=id
    )

    if request.method == 'POST':

        item.nome = request.POST.get('nome')

        nova_imagem = request.FILES.get('imagem')

        if nova_imagem:

            item.imagem = nova_imagem

        item.save()

        messages.success(
            request,
            'Item atualizado com sucesso.'
        )

    return redirect('achados')

@login_required
@permission_required('achadoseperdidos.delete_itemachado', raise_exception=True)
@require_POST
@excluir_rate_limit
def excluir_item(request, id):

    item = get_object_or_404(
        ItemAchado,
        id=id
    )

    item.delete()

    messages.success(
        request,
        'Item excluído.'
    )

    return redirect('achados')