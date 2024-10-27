import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Configuração do layout da página para wide
st.set_page_config(page_title="Simulador de estratégias com opções", layout="wide")

def obter_dados(acao):
    ticker = yf.Ticker(acao)
    dados = ticker.history(period='3mo', interval='1d')  # Dados diários dos últimos 3 meses
    return dados

def calcular_progresso(preco_atual, alvos):
    progresso = [(preco_atual / alvo) * 100 for alvo in alvos]
    return progresso

def calcular_volatilidade(dados):
    # Calcula os retornos diários
    retornos_diarios = dados['Close'].pct_change().dropna()
    # Calcula o desvio padrão dos retornos diários como medida de volatilidade
    volatilidade = retornos_diarios.std()
    return volatilidade

def calcular_previsao(dados, dias=10, window=5, volatilidade=0):
    # Calcula a média móvel com a janela especificada
    if len(dados) >= window:
        media_movel = dados['Close'].rolling(window=window).mean().iloc[-1]
    else:
        media_movel = dados['Close'].mean()  # Fallback para média simples se não houver dados suficientes
    
    # Ajusta a previsão com base na volatilidade
    previsao = [media_movel] * dias
    faixa_superior = [media_movel * (1 + volatilidade)] * dias
    faixa_inferior = [media_movel * (1 - volatilidade)] * dias
    
    return previsao, faixa_superior, faixa_inferior

def calcular_fibonacci(dados):
    max_price = dados['Close'].max()
    min_price = dados['Close'].min()
    diff = max_price - min_price
    levels = {
        "0%": min_price,
        "23.6%": min_price + 0.236 * diff,
        "38.2%": min_price + 0.382 * diff,
        "50%": min_price + 0.5 * diff,
        "61.8%": min_price + 0.618 * diff,
        "100%": max_price
    }
    return levels

def plot_grafico_com_fibonacci(acao, dados, preco_atual, alvos, progresso, previsao_7, faixa_7_sup, faixa_7_inf, previsao_30, faixa_30_sup, faixa_30_inf):
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

    # Adiciona linhas para os alvos
    for i, alvo in enumerate(alvos):
        perc_progresso = ((preco_atual / alvo) * 100) -100
        fig.add_hline(y=alvo, line=dict(color='blue' if i == 0 else 'green', width=2, dash='dash'),
                      annotation_text=f'Alvo {i+1}: {alvo} ({perc_progresso:.2f}%)', 
                      annotation_position='top right')

    # Adiciona níveis de Fibonacci
    fibonacci_levels = calcular_fibonacci(dados)
    for level, value in fibonacci_levels.items():
        fig.add_hline(y=value, line=dict(color='gray', width=1, dash='dash'), annotation_text=f'Nível Fibonacci {level}', annotation_position='top right')

    # Adiciona previsão de preço para 7 dias
    previsao_indices_7 = pd.date_range(start=dados.index[-1] + pd.Timedelta(days=1), periods=len(previsao_7))
    fig.add_trace(go.Scatter(x=previsao_indices_7, y=previsao_7, mode='lines', name='Previsão com Média Móvel de 7 Dias', line=dict(color='red', dash='dash')))
    fig.add_trace(go.Scatter(x=previsao_indices_7, y=faixa_7_sup, mode='lines', name='Faixa Superior 7 Dias', line=dict(color='red', dash='dot'), showlegend=False))
    fig.add_trace(go.Scatter(x=previsao_indices_7, y=faixa_7_inf, mode='lines', name='Faixa Inferior 7 Dias', line=dict(color='red', dash='dot'), fill='tonexty', fillcolor='rgba(255, 0, 0, 0.1)', showlegend=False))

    # Adiciona previsão de preço para 30 dias
    previsao_indices_30 = pd.date_range(start=dados.index[-1] + pd.Timedelta(days=1), periods=len(previsao_30))
    fig.add_trace(go.Scatter(x=previsao_indices_30, y=previsao_30, mode='lines', name='Previsão com Média Móvel de 30 Dias', line=dict(color='purple', dash='dot')))
    fig.add_trace(go.Scatter(x=previsao_indices_30, y=faixa_30_sup, mode='lines', name='Faixa Superior 30 Dias', line=dict(color='purple', dash='dot'), showlegend=False))
    fig.add_trace(go.Scatter(x=previsao_indices_30, y=faixa_30_inf, mode='lines', name='Faixa Inferior 30 Dias', line=dict(color='purple', dash='dot'), fill='tonexty', fillcolor='rgba(128, 0, 128, 0.1)', showlegend=False))

    fig.update_layout(title=f'{acao} - Preço Atual: R${preco_atual:.2f}',
                      yaxis_title='Preço',
                      xaxis_title='Data',
                      xaxis_rangeslider_visible=False)  # Oculta o range slider

    st.plotly_chart(fig)

def app():
    st.title('Monitoramento de Ações')

    # Inicializa a lista de ações no estado da sessão
    if 'acoes' not in st.session_state:
        st.session_state.acoes = []

    # Entrada do usuário para o ticker e os alvos
    acao = st.text_input('Digite o ticker da ação (ex: BBAS3.SA):')
    alvo1 = st.number_input('Digite o valor do Alvo 1:', min_value=0.0)
    alvo2 = st.number_input('Digite o valor do Alvo 2:', min_value=0.0)

    if st.button('Monitorar Ação'):
        if acao and alvo1 > 0 and alvo2 > 0:
            dados = obter_dados(acao)
            preco_atual = dados['Close'][-1]
            progresso = calcular_progresso(preco_atual, [alvo1, alvo2])
            volatilidade = calcular_volatilidade(dados)
            previsao_7, faixa_7_sup, faixa_7_inf = calcular_previsao(dados, window=7, volatilidade=volatilidade)
            previsao_30, faixa_30_sup, faixa_30_inf = calcular_previsao(dados, window=30, volatilidade=volatilidade)
            
            # Armazena os dados da ação no estado da sessão
            st.session_state.acoes.append({
                'acao': acao,
                'dados': dados,
                'preco_atual': preco_atual,
                'alvos': [alvo1, alvo2],
                'progresso': progresso,
                'previsao_7': previsao_7,
                'faixa_7_sup': faixa_7_sup,
                'faixa_7_inf': faixa_7_inf,
                'previsao_30': previsao_30,
                'faixa_30_sup': faixa_30_sup,
                'faixa_30_inf': faixa_30_inf
            })
        else:
            st.error("Por favor, insira um ticker e valores válidos para os alvos.")

    # Exibe todos os gráficos armazenados
    for acao_info in st.session_state.acoes:
        plot_grafico_com_fibonacci(
            acao_info['acao'], acao_info['dados'], acao_info['preco_atual'],
            acao_info['alvos'], acao_info['progresso'], acao_info['previsao_7'],
            acao_info['faixa_7_sup'], acao_info['faixa_7_inf'], acao_info['previsao_30'],
            acao_info['faixa_30_sup'], acao_info['faixa_30_inf']
        )

if __name__ == '__main__':
    app()