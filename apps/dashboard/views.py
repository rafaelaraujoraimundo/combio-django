from django.shortcuts import render
import plotly.express as px
from dashboard.forms import DateForm
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear, TruncMonth, Concat, Cast, Extract
from django.db.models import Value, CharField
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
# Create your views here.

from dashboard.models import BiChamadosServiceUp


def chamadosti(request):
    chamadosti = BiChamadosServiceUp.objects.raw(""" SELECT 1 as ticket_id, DATE(DATE_SUB(created, INTERVAL (DAYOFMONTH(created) - 1) DAY)) AS ANO_MES, COUNT(created) abertos, count(closed) fechados
    FROM bi_chamados_service_up
    group by CONCAT(SUBSTR(created, 1, 4), '-', SUBSTR(created, 6, 2))""")
    start = request.GET.get('start')
    end = request.GET.get('end')

    if start:
        start = datetime.strptime(start, '%Y-%m-%d').date()
    if end:
        end = datetime.strptime(end, '%Y-%m-%d').date()

    if start:
        chamadosti = [c for c in chamadosti if c.ANO_MES >= start]
    if end:
        chamadosti = [c for c in chamadosti if c.ANO_MES <= end]
    ano_mes = []
    abertos = []
    fechados = []
    for chamado in chamadosti:
        # Acessar os atributos do objeto e adicionar os valores às listas
        ano_mes.append(chamado.ANO_MES.strftime('%Y-%m'))
        abertos.append(chamado.abertos)
        fechados.append(chamado.fechados)

    # Criar um DataFrame com os dados
    data = {
        'Ano/Mês': ano_mes, 'Abertos': abertos, 'Fechados': fechados}
    df = pd.DataFrame(data)
    # Criar o gráfico de histograma
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Ano/Mês'], y=df['Abertos'], name='Abertos'))
    fig.add_trace(go.Bar(x=df['Ano/Mês'], y=df['Fechados'], name='Fechados'))

    # Personalizar o layout do gráfico
    fig.update_layout(
        title='Chamados por Mês',
        xaxis_title='Ano / Mês',
        yaxis_title='Quantidade de Chamados',
        barmode='group',
        bargap=0.4,  # gap between bars of adjacent location coordinates.

    )

    # Converter o gráfico em HTML
    chart = fig.to_html(full_html=False, default_height=500)

    # Gerar o gráfico em formato HTML
    chart = fig.to_html()

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df['Ano/Mês'], y=df['Abertos'], name='Abertos', mode='lines+markers', xperiodalignment="middle"))
    fig2.add_trace(go.Scatter(
        x=df['Ano/Mês'], y=df['Fechados'], name='Fechados', mode='lines+markers', xperiodalignment="middle"))

    # Personalizar o layout do gráfico
    fig2.update_layout(
        title='Chamados por Mês',
        xaxis_title='Ano / Mês',
        yaxis_title='Quantidade de Chamados'
    )

    # Converter o gráfico em HTML
    chart2 = fig2.to_html(full_html=False, default_height=500)

    context = {'chart': chart, 'form': DateForm, 'chart2': chart2}
    return render(request, 'dashboards/ti.html', context)
