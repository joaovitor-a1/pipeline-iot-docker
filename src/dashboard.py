# Importação das bibliotecas
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Dashboard Temperaturas IoT", page_icon="🌡️", layout="wide"
)
# Definição das credenciais de acesso ao banco de dados PostgreSQL
DB_USER = "postgres"
DB_PASS = "123456"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "iot_db"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)


engine = get_engine()

# Função para consultar as Views SQL e retornar os dados
def load_data(view_name):
    with engine.connect() as conn:
        return pd.read_sql(text(f"SELECT * FROM {view_name}"), conn)


st.title("🌡️ Dashboard de Monitoramento de Temperaturas IoT")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.header("Média de Temperatura por Dispositivo")
    try:
        df_avg = load_data("avg_temp_por_dispositivo")
        # Geração do gráfico de barras com Plotly Express
        fig1 = px.bar(
            df_avg,
            x="device_id",
            y="avg_temp",
            labels={"device_id": "Dispositivo", "avg_temp": "Média (°C)"},
            text_auto=True,
            color="device_id",
        )
        st.plotly_chart(fig1, width="stretch")
    except Exception as e:
        st.error(f"Erro ao carregar View: {e}")

with col2:
    st.header("Leituras por Hora do Dia")
    try:
        df_hora = load_data("leituras_por_hora")
        # Geração do gráfico de linha temporal
        fig2 = px.line(
            df_hora,
            x="hora",
            y="contagem",
            markers=True,
            labels={"hora": "Hora do Dia", "contagem": "Total de Leituras"},
        )
        st.plotly_chart(fig2, width="stretch")
    except Exception as e:
        st.error(f"Erro ao carregar View: {e}")

st.markdown("---")
# Gráfico de Temperaturas  
st.header("Temperaturas Máximas e Mínimas por Dia")
try:
    df_dia = load_data("temp_max_min_por_dia")
    # Geração do gráfico de duas linhas
    fig3 = px.line(
        df_dia,
        x="data",
        y=["temp_max", "temp_min"],
        labels={
            "data": "Data",
            "value": "Temperatura (°C)",
            "variable": "Métrica",
        },
    )
    # Renderização do gráfico na tela
    st.plotly_chart(fig3, width="stretch")
except Exception as e:
    st.error(f"Erro ao carregar View: {e}")