import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# Configuração do layout da página para wide
st.set_page_config(page_title="Simulador de Estratégias com Opções", layout="wide")

def obter_dados(acao):
    ticker = yf.Ticker(acao)
    dados = ticker.history(period='3mo', interval='1d')  # Dados diários dos últimos 3 meses
    return dados

def calcular_payoff(preco_acao, preco_exercicio_put, premio_put, preco_exercicio_call, premio_call):
    # Calcula o payoff das opções
    payoff_put = np.maximum(preco_exercicio_put - preco_acao, 0) - premio_put
    payoff_call = np.maximum(preco_acao - preco_exercicio_call, 0) - premio_call
    return payoff_put + payoff_call

def plot_grafico_com_precos_exercicio(acao, dados, preco_atual, preco_exercicio_put, preco_exercicio_call, key):
    # Calcula a média móvel de 30 dias
    dados['Média Móvel 30 Dias'] = dados['Close'].rolling(window=30).mean()

    # Previsão de preço para 10 dias com base na média móvel atual
    previsao_10_dias = dados['Média Móvel 30 Dias'].iloc[-1]

    fig = go.Figure()

    # Adiciona candlesticks
    fig.add_trace(go.Candlestick(
        x=dados.index,
        open=dados['Open'],
        high=dados['High'],
        low=dados['Low'],
        close=dados['Close'],
        name='Candlesticks'
    ))

    # Adiciona a média móvel de 30 dias
    fig.add_trace(go.Scatter(
        x=dados.index,
        y=dados['Média Móvel 30 Dias'],
        mode='lines',
        name='Média Móvel 30 Dias',
        line=dict(color='orange', width=2)
    ))

    # Adiciona linhas para os preços de exercício
    fig.add_hline(y=preco_exercicio_put, line=dict(color='blue', width=2, dash='dash'),
                  annotation_text=f'Preço Exercício Put: {preco_exercicio_put}', annotation_position='top right')
    fig.add_hline(y=preco_exercicio_call, line=dict(color='green', width=2, dash='dash'),
                  annotation_text=f'Preço Exercício Call: {preco_exercicio_call}', annotation_position='top right')

    fig.update_layout(title=f'{acao} - Preço Atual: R${preco_atual:.2f} | Previsão 10 Dias: R${previsao_10_dias:.2f}',
                      yaxis_title='Preço',
                      xaxis_title='Data',
                      xaxis_rangeslider_visible=False)

    st.plotly_chart(fig, key=key)

def plot_grafico_payoff(preco_exercicio_put, premio_put, preco_exercicio_call, premio_call, preco_atual, key):
    precos_acao = np.linspace(preco_atual * 0.5, preco_atual * 1.5, 100)
    payoff_total = calcular_payoff(precos_acao, preco_exercicio_put, premio_put, preco_exercicio_call, premio_call)

    # Calcula os pontos de equilíbrio (break-even)
    breakeven_put = preco_exercicio_put - premio_put - premio_call
    breakeven_call = preco_exercicio_call + premio_put + premio_call

    fig = go.Figure()

    # Região de prejuízo antes do break-even da put
    fig.add_trace(go.Scatter(
        x=precos_acao[precos_acao < breakeven_put],
        y=payoff_total[precos_acao < breakeven_put],
        mode='lines',
        name='Prejuízo (Put)',
        line=dict(color='red')
    ))

    # Região de lucro entre os break-evens
    fig.add_trace(go.Scatter(
        x=precos_acao[(precos_acao >= breakeven_put) & (precos_acao <= breakeven_call)],
        y=payoff_total[(precos_acao >= breakeven_put) & (precos_acao <= breakeven_call)],
        mode='lines',
        name='Lucro',
        line=dict(color='blue')
    ))

    # Região de prejuízo após o break-even da call
    fig.add_trace(go.Scatter(
        x=precos_acao[precos_acao > breakeven_call],
        y=payoff_total[precos_acao > breakeven_call],
        mode='lines',
        name='Prejuízo (Call)',
        line=dict(color='red')
    ))

    # Adiciona uma linha vertical para o preço atual da ação
    fig.add_vline(x=preco_atual, line=dict(color='black', width=2, dash='dash'),
                  annotation_text=f'Preço Atual: {preco_atual:.2f}', annotation_position='bottom right')

    fig.add_hline(y=0, line=dict(color='black', width=1, dash='dash'))

    fig.update_layout(
        title='Gráfico de Payoff das Estratégias de Venda de Opções',
        xaxis_title='Preço da Ação na Data de Vencimento',
        yaxis_title='Payoff',
        xaxis=dict(title='Preço da Ação'),
        yaxis=dict(title='Payoff'),
        showlegend=True
    )

    st.plotly_chart(fig, key=key)

    # Exibe os pontos de break-even abaixo do gráfico
    st.write(f"**Pontos de Break-even:**")
    st.write(f"- **Put:** R${breakeven_put:.2f}")
    st.write(f"- **Call:** R${breakeven_call:.2f}")

def app():
    st.title('Monitoramento de Ações e Payoff de Opções')

    # Inicializa a lista de ações no estado da sessão
    if 'acoes' not in st.session_state:
        st.session_state.acoes = []

    # Entrada do usuário para o ticker e os preços de exercício das opções
    acao = st.text_input('Digite o ticker da ação (ex: BBAS3.SA):')
    preco_exercicio_put = st.number_input('Digite o preço de exercício da Put:', min_value=0.0)
    premio_put = st.number_input('Digite o prêmio recebido pela Put:', min_value=0.0)
    preco_exercicio_call = st.number_input('Digite o preço de exercício da Call:', min_value=0.0)
    premio_call = st.number_input('Digite o prêmio recebido pela Call:', min_value=0.0)
 

    if st.button('Monitorar Ação'):
        if acao and preco_exercicio_put > 0 and preco_exercicio_call > 0:
            dados = obter_dados(acao)
            preco_atual = dados['Close'][-1]
            
            # Armazena os dados da ação no estado da sessão
            st.session_state.acoes.append({
                'acao': acao,
                'dados': dados,
                'preco_atual': preco_atual,
                'preco_exercicio_put': preco_exercicio_put,
                'premio_put': premio_put,
                'preco_exercicio_call': preco_exercicio_call,
                'premio_call': premio_call
            })
            
            # Plota o gráfico de payoff
            plot_grafico_payoff(preco_exercicio_put, premio_put, preco_exercicio_call, premio_call, preco_atual, key=f"payoff_{acao}")
        else:
            st.error("Por favor, insira um ticker e valores válidos para os preços de exercício.")

    # Exibe todos os gráficos armazenados
    for i, acao_info in enumerate(st.session_state.acoes):
        plot_grafico_com_precos_exercicio(
            acao_info['acao'], acao_info['dados'], acao_info['preco_atual'],
            acao_info['preco_exercicio_put'], acao_info['preco_exercicio_call'],
            key=f"chart_{acao_info['acao']}_{i}"
        )

if __name__ == '__main__':
    app()
