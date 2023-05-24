from django.shortcuts import render
from dashboard.forms import DateForm
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import mysql.connector
from menu.menu import GetGroup, GetMenu
from django.contrib.auth.decorators import permission_required
from dashboard.models import BiChamadosServiceUp
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import FactorRange


@permission_required('global_permissions.combio_dashboard_ti', login_url='erro_page')
def dashboard_ti(request):
    activegroup = 'Dashboard'
    activemenu = 'dashboard_ti'
    groups = GetGroup()
    menus = GetMenu()
    user_groups = request.user.groups.all()
    chamadosti = BiChamadosServiceUp.objects.raw(""" SELECT 1 as ticket_id,
    DATE(DATE_SUB(created, INTERVAL (DAYOFMONTH(created) - 1) DAY)) AS ANO_MES,
            COUNT(created) abertos, count(closed) fechados
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
    largura_barras = 0.35

    # Criação do gráfico de colunas com barras lado a lado usando o Bokeh
    plot = figure(x_range=FactorRange(factors=ano_mes), title='Chamados Abertos e Fechados',
                  x_axis_label='Período', y_axis_label='Quantidade')
    plot.vbar(x=ano_mes, top=abertos, width=largura_barras,
              color='blue', legend_label='Abertos')
    plot.vbar(x=ano_mes, top=fechados, width=largura_barras,
              color='red', legend_label='Fechados')

    plot.legend.location = 'top_right'
    plot.legend.title = 'Chamados por Mês'

    # Gera o código HTML e JavaScript para incorporar o gráfico no template
    script, div = components(plot)

    context = {'form': DateForm, 'script': script, 'div': div,
               'groups': groups,
               'menus': menus, 'activegroup': activegroup,
               'activemenu': activemenu, 'user_groups': user_groups}
    return render(request, 'dashboards/ti.html', context)


@permission_required('global_permissions.combio_dashboard_controladoria', login_url='erro_page')
def dashboard_controladoria(request):
    activegroup = 'Dashboard'
    activemenu = 'dashboard_controladoria'
    groups = GetGroup()
    menus = GetMenu()
    user_groups = request.user.groups.all()
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
                                     'descricaoCusto', 'conta',
                                     'descricaoConta'],
                              columns='primeiroDiaMes')

# Resetar o índice para converter em colunas
    pivot_df.reset_index(inplace=True)

# Renomear as colunas
    pivot_df.columns = ['REGIONAL', 'NOME_FANTASIA', 'CENTRO DE CUSTO',
                        'descricaoCusto', 'CONTA', 'DESCRICAO_CONTA'] + pivot_df.columns[6:].tolist()
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
        width=800,
        height=500,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2f2f2f'),
        xaxis=dict(showgrid=True, zeroline=False),
        yaxis=dict(showgrid=True, zeroline=False),
        hovermode='closest',
        showlegend=True,
        autosize=False,
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
        return render(request, 'dashboards/controladoria.html', {'table1_html': table1_html, 'table2_html': table2_html, 'groups': groups,
                                                                 'menus': menus, 'activegroup': activegroup,
                                                                 'activemenu': activemenu, 'user_groups': user_groups})

    # Renderizar o template inicial
    return render(request, 'dashboards/controladoria.html', {'table1_html': table1_html, 'groups': groups,
                                                             'menus': menus, 'activegroup': activegroup,
                                                             'activemenu': activemenu, 'user_groups': user_groups})


@permission_required('global_permissions.combio_dashboard_controladoria', login_url='erro_page')
def exemplo(request):
    # Dados para o gráfico
    categorias = ['A', 'B', 'C', 'D']
    valores = [10, 15, 7, 12]

    # Criação do gráfico de barras usando o Bokeh
    plot = figure(x_range=categorias, title='Gráfico de Barras',
                  x_axis_label='Categorias', y_axis_label='Valores')
    plot.vbar(x=categorias, top=valores, width=0.5)

    # Gera o código HTML e JavaScript para incorporar o gráfico no template
    script, div = components(plot)

    # Renderiza o template com os componentes do gráfico
    return render(request, 'dashboards/exemplo.html', {'script': script, 'div': div})
