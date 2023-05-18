from django.shortcuts import render
import plotly.express as px
from dashboard.forms import DateForm
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear, TruncMonth, Concat, Cast, Extract
from django.db.models import Value, CharField
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import mysql.connector
from menu.menu import GetGroup, GetMenu
# Create your views here.

from dashboard.models import BiChamadosServiceUp


def chamadosti(request):
    activegroup = 'Dashboard'
    activemenu = 'TI'
    groups = GetGroup()
    menus = GetMenu()
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

    context = {'chart': chart, 'form': DateForm,
               'chart2': chart2, 'groups': groups,
               'menus': menus, 'activegroup': activegroup,
               'activemenu': activemenu}
    return render(request, 'dashboards/ti.html', context)


def OrcadoRealizado_dash(request):
    # Conectar ao banco de dados
    con = mysql.connector.connect(
        host='172.16.0.15', database='dw_combio', user='usr_combio',
        password='Cmb@Dw12.2020')

    # Definir a consulta SQL
    sql_query = '''
        SELECT
            be.Regional,
            be.NOME_FANTASIA,
            centroCusto,
            descricaoCusto,
            conta,
            descricaoConta,
            bec.estabelecimento,
            DATE_FORMAT(dataRealizado, '%Y-%m-01') AS primeiroDiaMes,
            IFNULL(ROUND(SUM(valorRealizado), 2),0) AS valorTotalRealizado
        FROM
            bi_efz1005_cep bec
        LEFT JOIN
            bi_estabelecimento be ON bec.estabelecimento = be.estabelecimento
        WHERE dataRealizado between '2023-01-01' and '2023-05-31'
        GROUP BY
            be.Regional,
            be.NOME_FANTASIA,
            conta,
            descricaoConta,
            bec.estabelecimento,
            centroCusto,
            descricaoCusto,
            primeiroDiaMes
    '''

    # Executar a consulta SQL e obter os resultados como um dataframe do Pandas
    df = pd.read_sql(sql_query, con)
    # Criar a primeira tabela usando Plotly
    pivot_df = df.pivot_table(values='valorTotalRealizado',
                              index=['Regional', 'NOME_FANTASIA', 'centroCusto',
                                     'descricaoCusto', 'conta', 'descricaoConta'],
                              columns='primeiroDiaMes')

# Resetar o índice para converter em colunas
    pivot_df.reset_index(inplace=True)

# Renomear as colunas
    pivot_df.columns = ['REGIONAL', 'NOME_FANTASIA', 'CENTRO DE CUSTO', 'descricaoCusto'
                        'CONTA', 'DESCRICAO_CONTA'] + pivot_df.columns[5:].tolist()
    pivot_df.fillna(0, inplace=True)
# Verificar as colunas presentes no pivot_df
    print(pivot_df.columns)

    fig1 = go.Figure(data=[go.Table(
        header=dict(values=list(pivot_df.columns)),
        cells=dict(values=[pivot_df[col] for col in pivot_df.columns]),
        # Ajustar o tamanho das colunas
        columnwidth=[50] + [100] * (len(pivot_df.columns) - 1),
    )])
# Definir o layout do gráfico
    fig1.update_layout(
        # Adicionar barra de rolagem horizontal
        width='800',
        height='500px',
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2f2f2f'),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
        hovermode='closest',
        showlegend=False,
        autosize=True,
    )

    # Converter a primeira tabela para HTML
    table1_html = fig1.to_html(full_html=False)
    # Filtrar a segunda tabela com base na seleção da primeira tabela
    selected_col = request.GET.get('selected_col')
    if selected_col:
        selected_estabelecimento = pivot_df.index.get_level_values('estabelecimento')[
            int(selected_col)]
        filtered_df = df[df['estabelecimento'] == selected_estabelecimento]

        # Criar a segunda tabela usando Plotly
        pivot_filtered_df = filtered_df.pivot_table(values='valorTotalRealizado',
                                                    index=['Regional', 'NOME_FANTASIA', 'centroCusto',
                                                           'descricaoCusto', 'conta', 'descricaoConta'],
                                                    columns='primeiroDiaMes')

        fig2 = go.Figure(data=[go.Table(
            header=dict(values=list(pivot_filtered_df.columns)),
            cells=dict(values=[pivot_filtered_df[col] for col in pivot_filtered_df.columns]))
        ])

        # Converter a segunda tabela para HTML
        table2_html = fig2.to_html(full_html=False)

        # Renderizar o template com as tabelas em HTML
        return render(request, 'dashboards/controladoria.html', {'table1_html': table1_html, 'table2_html': table2_html})

    # Renderizar o template inicial
    return render(request, 'dashboards/controladoria.html', {'table1_html': table1_html})
