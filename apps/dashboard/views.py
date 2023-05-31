from django.shortcuts import render
from dashboard.forms import DateForm
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import mysql.connector
from menu.menu import GetGroup, GetMenu
from django.contrib.auth.decorators import permission_required
from dashboard.models import BiChamadosServiceUp
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import FactorRange
from bokeh.resources import CDN
from plotly.offline import plot


def view_padrao(request):
    activegroup = 'Dashboard'
    context = {'activegroup': activegroup}
    return render(request, 'dashboards/ti.html', context)


@permission_required('global_permissions.combio_dashboard_ti', login_url='erro_page')
def dashboard_ti(request):
    activegroup = 'Dashboard'
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

    context = {'form': DateForm, 'script': script,
               'div': div, 'activegroup': activegroup}
    return render(request, 'dashboards/ti.html', context)


@permission_required('global_permissions.combio_dashboard_controladoria', login_url='erro_page')
def dashboard_controladoria(request):
    activegroup = 'Dashboard'
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
        return render(request, 'dashboards/controladoria.html', {'table1_html': table1_html, 'table2_html': table2_html})

    # Renderizar o template inicial
    return render(request, 'dashboards/controladoria.html', {'table1_html': table1_html, 'activegroup': activegroup})


@permission_required('global_permissions.combio_dashboard_controladoria', login_url='erro_page')
def exemplo(request):
    activegroup = 'Dashboard'
    activemenu = 'dashboard_exemplo'
    groups = GetGroup()
    menus = GetMenu()
    user_groups = request.user.groups.all()
    # Dados para os gráficos
    x = [1, 2, 3, 4, 5]
    y = [6, 7, 2, 4, 5]

    # Criação dos gráficos
    line_plot = figure(title="Gráfico de Linha",
                       x_axis_label='X', y_axis_label='Y')
    line_plot.line(x, y, legend_label='Linha', line_width=2)

    bar_plot = figure(title="Gráfico de Barras",
                      x_axis_label='Categoria', y_axis_label='Valores')
    bar_plot.vbar(x=['A', 'B', 'C', 'D'], top=[4, 6, 8, 2], width=0.5)

    bar_plot = figure(title="Gráfico de Barras",
                      x_axis_label='Categoria', y_axis_label='Valores')
    bar_plot.vbar(x=x, top=y, width=0.5)

    scatter_plot = figure(title="Gráfico de Dispersão",
                          x_axis_label='X', y_axis_label='Y')
    scatter_plot.circle(x, y, size=10, color='navy', alpha=0.5)
    # Criação do gráfico de barras clusterizadas
    clustered_bar_plot = figure(title="Gráfico de Barras Clusterizadas", x_range=[
                                'Grupo 1', 'Grupo 2', 'Grupo 3'], x_axis_label='Grupos', y_axis_label='Valores')
    clustered_bar_plot.vbar(x=['Grupo 1', 'Grupo 2', 'Grupo 3'], top=[
                            4, 5, 2], width=0.2, color='red', legend_label='Série 1')
    clustered_bar_plot.vbar(x=['Grupo 1', 'Grupo 2', 'Grupo 3'], top=[
                            2, 3, 4], width=0.2, color='blue', legend_label='Série 2')
    clustered_bar_plot.vbar(x=['Grupo 1', 'Grupo 2', 'Grupo 3'], top=[
                            1, 6, 5], width=0.2, color='green', legend_label='Série 3')

    # Criação do gráfico de linhas clusterizadas
    clustered_line_plot = figure(
        title="Gráfico de Linhas Clusterizadas", x_axis_label='X', y_axis_label='Y')
    clustered_line_plot.line(
        x, y, legend_label='Linha 1', line_width=2, color='red')
    clustered_line_plot.line(
        x, [5, 2, 3, 4, 1], legend_label='Linha 2', line_width=2, color='blue')
    clustered_line_plot.line(
        x, [2, 5, 1, 4, 2], legend_label='Linha 3', line_width=2, color='green')

    # Renderiza os gráficos para HTML
    script, div = components(line_plot, CDN)
    script2, div2 = components(bar_plot, CDN)
    script3, div3 = components(scatter_plot, CDN)
    script4, div4 = components(clustered_bar_plot, CDN)
    script5, div5 = components(clustered_line_plot, CDN)
    # Renderiza os gráficos para HTML

    return render(request, 'dashboards/exemplo.html', {'activegroup': activegroup, 'script': script, 'div': div, 'script2': script2, 'div2': div2, 'script3': script3, 'div3': div3, 'script4': script4, 'div4': div4, 'script5': script5, 'div5': div5})


def exemplo2(request):
    activegroup = 'Dashboard'
    activemenu = 'dashboard_exemplo2'
    groups = GetGroup()
    menus = GetMenu()
    user_groups = request.user.groups.all()
    # Dados para os gráficos
    x_data = [1, 2, 3, 4, 5]
    y_data = [2, 4, 1, 5, 3]
    categories = ['A', 'B', 'C', 'D']
    values1 = [3, 2, 4, 6]
    values2 = [5, 1, 2, 3]

    # Gráfico de Linhas
    line_trace = go.Scatter(
        x=x_data,
        y=y_data,
        mode='lines',
        name='Gráfico de Linhas'
    )
    line_layout = go.Layout(
        title='Gráfico de Linhas',
        xaxis=dict(title='Eixo X'),
        yaxis=dict(title='Eixo Y')
    )
    line_fig = go.Figure(data=[line_trace], layout=line_layout)
    line_plot_div = plot(line_fig, output_type='div')

    # Gráfico de Barras
    bar_trace = go.Bar(
        x=categories,
        y=values1,
        name='Gráfico de Barras'
    )
    bar_layout = go.Layout(
        title='Gráfico de Barras',
        xaxis=dict(title='Categorias'),
        yaxis=dict(title='Valores')
    )
    bar_fig = go.Figure(data=[bar_trace], layout=bar_layout)
    bar_plot_div = plot(bar_fig, output_type='div')

    # Gráfico de Linhas Clusterizadas
    clustered_line_trace1 = go.Scatter(
        x=x_data,
        y=y_data,
        mode='lines',
        name='Linha 1'
    )
    clustered_line_trace2 = go.Scatter(
        x=x_data,
        y=[y+1 for y in y_data],
        mode='lines',
        name='Linha 2'
    )
    clustered_line_data = [clustered_line_trace1, clustered_line_trace2]
    clustered_line_layout = go.Layout(
        title='Gráfico de Linhas Clusterizadas',
        xaxis=dict(title='Eixo X'),
        yaxis=dict(title='Eixo Y')
    )
    clustered_line_fig = go.Figure(
        data=clustered_line_data, layout=clustered_line_layout)
    clustered_line_plot_div = plot(clustered_line_fig, output_type='div')

    # Gráfico de Barras Clusterizadas
    clustered_bar_trace1 = go.Bar(
        x=categories,
        y=values1,
        name='Barra 1'
    )
    clustered_bar_trace2 = go.Bar(
        x=categories,
        y=values2,
        name='Barra 2'
    )
    clustered_bar_data = [clustered_bar_trace1, clustered_bar_trace2]
    clustered_bar_layout = go.Layout(
        title='Gráfico de Barras Clusterizadas',
        xaxis=dict(title='Categorias'),
        yaxis=dict(title='Valores')
    )
    clustered_bar_fig = go.Figure(
        data=clustered_bar_data, layout=clustered_bar_layout)
    clustered_bar_plot_div = plot(clustered_bar_fig, output_type='div')

    return render(request, 'dashboards/exemplo2.html', {'groups': groups,
                                                        'menus': menus, 'activegroup': activegroup,
                                                        'activemenu': activemenu, 'user_groups': user_groups,
                                                        'line_plot_div': line_plot_div,
                                                        'bar_plot_div': bar_plot_div,
                                                        'clustered_line_plot_div': clustered_line_plot_div,
                                                        'clustered_bar_plot_div': clustered_bar_plot_div
                                                        })
