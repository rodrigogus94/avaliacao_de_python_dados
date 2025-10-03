# -*- coding: utf-8 -*-
# STREAMLIT COM MAPA INTERATIVO FOLIUM - VERSÃO CORRIGIDA E OTIMIZADA

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import io
from docx import Document
from docx.shared import Inches
import warnings
import folium
from folium import plugins
from streamlit_folium import folium_static

warnings.filterwarnings("ignore")

# Configuração de estilo
plt.style.use("default")
sns.set_palette("husl")


# ==============================================================================
# ⚠️ FUNÇÃO ESSENCIAL: CARREGAMENTO E PRÉ-PROCESSAMENTO DOS DADOS
# ==============================================================================
@st.cache_data
def load_data():
    """
    Simula o carregamento e pré-processamento dos dados de acidentes rodoviários.
    """
    st.info("⚠️ Usando dados simulados para demonstração.")

    np.random.seed(42)
    N_ROWS = 5000

    # Lista de estados brasileiros e suas coordenadas
    estados_coords = {
        "SP": [-23.5489, -46.6388],
        "MG": [-19.9167, -43.9345],
        "PR": [-25.4284, -49.2733],
        "RS": [-30.0346, -51.2177],
        "SC": [-27.5954, -48.5480],
        "RJ": [-22.9068, -43.1729],
        "BA": [-12.9714, -38.5014],
        "GO": [-16.6809, -49.2533],
        "PE": [-8.0476, -34.8770],
        "CE": [-3.7172, -38.5434],
        "PA": [-1.4554, -48.4902],
        "MA": [-2.5387, -44.2823],
        "MT": [-15.6014, -56.0979],
        "MS": [-20.4428, -54.6464],
        "PI": [-5.0920, -42.8038],
        "RN": [-5.7945, -35.2110],
        "AL": [-9.6658, -35.7350],
        "SE": [-10.9472, -37.0731],
        "RO": [-8.7612, -63.9005],
        "TO": [-10.2491, -48.3243],
        "AC": [-9.9740, -67.8076],
        "AM": [-3.1190, -60.0217],
        "RR": [2.8235, -60.6758],
        "AP": [0.0349, -51.0664],
        "DF": [-15.7797, -47.9297],
    }

    # Criar DataFrame
    df = pd.DataFrame(
        {
            "id": range(1, N_ROWS + 1),
            "uf": np.random.choice(list(estados_coords.keys()), N_ROWS),
            "tipo_acidente": np.random.choice(
                [
                    "Colisão Traseira",
                    "Saída de Pista",
                    "Colisão Frontal",
                    "Tombamento",
                    "Atropelamento",
                ],
                N_ROWS,
            ),
            "mortos": np.random.poisson(0.3, N_ROWS),
            "feridos_graves": np.random.poisson(0.8, N_ROWS),
            "feridos_leves": np.random.poisson(1.5, N_ROWS),
            "ilesos": np.random.poisson(2.0, N_ROWS),
        }
    )

    # Adicionar datas
    dates = pd.date_range("2018-01-01", "2023-12-31", periods=N_ROWS)
    df["data_inversa"] = np.random.choice(dates, N_ROWS)
    df["ano"] = df["data_inversa"].dt.year
    df["mes"] = df["data_inversa"].dt.month

    # Dias da semana em português
    dias_map = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo",
    }
    df["dia_semana"] = df["data_inversa"].dt.dayofweek.map(dias_map)

    # Adicionar coordenadas
    def get_coordinates(uf):
        lat, lon = estados_coords[uf]
        return lat + np.random.normal(0, 0.3), lon + np.random.normal(0, 0.3)

    coords = df["uf"].apply(get_coordinates)
    df["latitude"] = coords.apply(lambda x: x[0])
    df["longitude"] = coords.apply(lambda x: x[1])

    return df


# ==============================================================================
# CLASSES DE ANÁLISE E GERAÇÃO DE RELATÓRIOS
# ==============================================================================
class ReportGenerator:
    def __init__(self):
        self.document = Document()
        self.figures = []
        self.tables = []

    def add_heading(self, text, level=1):
        self.document.add_heading(text, level=level)

    def add_paragraph(self, text):
        self.document.add_paragraph(text)

    def add_figure(self, fig, caption=None):
        self.figures.append((fig, caption))

    def add_table(self, df, caption=None):
        self.tables.append((df, caption))

    def generate_docx(self):
        for fig, caption in self.figures:
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            self.document.add_picture(img_buffer, width=Inches(6))
            if caption:
                self.document.add_paragraph(f"Figura: {caption}")
            self.document.add_paragraph("")

        for df, caption in self.tables:
            if caption:
                self.document.add_paragraph(caption)
            table = self.document.add_table(rows=len(df) + 1, cols=len(df.columns))

            # Cabeçalho
            for j, col in enumerate(df.columns):
                table.cell(0, j).text = str(col)

            # Dados
            for i, row in df.iterrows():
                for j, value in enumerate(row):
                    table.cell(i + 1, j).text = str(value)
            self.document.add_paragraph("")

        doc_buffer = io.BytesIO()
        self.document.save(doc_buffer)
        doc_buffer.seek(0)
        return doc_buffer

    def build_report(self, analyzer, selections, author):
        """Constrói o documento Word com base nas seleções do usuário."""
        # Cabeçalho
        self.add_heading("Relatório de Análise de Acidentes Rodoviários", 1)
        self.add_paragraph(f"Autor: {author}")
        self.add_paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        self.add_paragraph("-" * 50)

        # Conteúdo baseado nas seleções
        if selections.get("include_evolution"):
            self.add_heading("Evolução Anual", level=2)
            fig = analyzer.create_evolution_chart()
            self.add_figure(fig, "Evolução anual de acidentes e vítimas.")
            plt.close(fig)  # Liberar memória

        if selections.get("include_states"):
            self.add_heading("Análise por Estado", level=2)
            fig = analyzer.create_states_chart()
            self.add_figure(
                fig, "Comparativo de acidentes e taxa de mortalidade por estado."
            )
            plt.close(fig)

        if selections.get("include_types"):
            self.add_heading("Tipos de Acidente", level=2)
            fig = analyzer.create_accident_types_chart()
            self.add_figure(fig, "Distribuição percentual dos tipos de acidente.")
            plt.close(fig)

        if selections.get("include_weekday"):
            self.add_heading("Análise por Dia da Semana", level=2)
            fig = analyzer.create_weekday_chart()
            self.add_figure(fig, "Volume de acidentes e mortes ao longo da semana.")
            plt.close(fig)

        if selections.get("include_metrics"):
            self.add_heading("Métricas Gerais", level=2)
            tabela = analyzer.create_metrics_table()
            self.add_table(tabela, "Tabela consolidada com as principais métricas.")

        if selections.get("include_highways"):
            self.add_heading("Análise de Rodovias", level=2)
            tabela = analyzer.create_highways_table()
            self.add_table(tabela, "Ranking simulado das rodovias mais perigosas.")


class DataAnalyzer:
    def __init__(self, df):
        self.df = df

    # ==================== GRÁFICOS ====================
    @st.cache_data
    def create_evolution_chart(_self):
        """Cria gráfico de evolução anual. O decorator _self garante que o cache seja por instância."""
        df_copy = _self.df.copy()
        anual = (
            df_copy.groupby("ano")
            .agg({"id": "count", "mortos": "sum", "feridos_graves": "sum"})
            .reset_index()
        )

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        ax1.plot(anual["ano"], anual["id"], marker="o", linewidth=2, color="#1f77b4")
        ax1.set_title("Evolução Anual de Acidentes", fontweight="bold")
        ax1.grid(True, alpha=0.3)

        ax2.bar(
            anual["ano"] - 0.2, anual["mortos"], width=0.4, label="Mortos", alpha=0.7
        )
        ax2.bar(
            anual["ano"] + 0.2,
            anual["feridos_graves"],
            width=0.4,
            label="Feridos Graves",
            alpha=0.7,
        )
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    @st.cache_data
    def create_states_chart(_self):
        df_copy = _self.df.copy()
        estados = (
            df_copy.groupby("uf").agg({"id": "count", "mortos": "sum"}).reset_index()
        )
        estados["taxa_mortalidade"] = (estados["mortos"] / estados["id"]) * 100

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        top10 = estados.nlargest(10, "id")
        ax1.barh(top10["uf"], top10["id"], color="skyblue")
        ax1.set_title("Top 10 Estados - Acidentes")

        top_mortalidade = estados.nlargest(10, "taxa_mortalidade")
        ax2.barh(
            top_mortalidade["uf"],
            top_mortalidade["taxa_mortalidade"],
            color="lightcoral",
        )
        ax2.set_title("Top 10 Estados - Taxa Mortalidade (%)")

        plt.tight_layout()
        return fig

    @st.cache_data
    def create_accident_types_chart(_self):
        df_copy = _self.df.copy()
        tipos = df_copy["tipo_acidente"].value_counts()

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.pie(tipos.values, labels=tipos.index, autopct="%1.1f%%", startangle=90)
        ax.set_title("Distribuição por Tipo de Acidente")
        return fig

    @st.cache_data
    def create_weekday_chart(_self):
        df_copy = _self.df.copy()
        dias = (
            df_copy.groupby("dia_semana")
            .agg({"id": "count", "mortos": "sum"})
            .reset_index()
        )

        ordem = [
            "Segunda-feira",
            "Terça-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sábado",
            "Domingo",
        ]
        dias["dia_semana"] = pd.Categorical(
            dias["dia_semana"], categories=ordem, ordered=True
        )
        dias = dias.sort_values("dia_semana")

        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax2 = ax1.twinx()

        ax1.plot(
            dias["dia_semana"], dias["id"], color="blue", marker="o", label="Acidentes"
        )
        ax2.bar(
            dias["dia_semana"], dias["mortos"], alpha=0.3, color="red", label="Mortos"
        )

        ax1.set_ylabel("Acidentes", color="blue")
        ax2.set_ylabel("Mortos", color="red")
        ax1.tick_params(axis="x", rotation=45)
        plt.title("Acidentes e Mortes por Dia da Semana")
        plt.tight_layout()
        return fig

    # ==================== MAPA INTERATIVO ====================
    @st.cache_data
    def create_interactive_map(_self, sample_size=1000):
        # Agrupar dados por estado
        df_copy = _self.df.copy()
        estados_data = (
            _self.df.groupby("uf")
            .agg({"id": "count", "mortos": "sum", "feridos_graves": "sum"})
            .reset_index()
        )
        estados_data["taxa_mortalidade"] = (
            estados_data["mortos"] / estados_data["id"]
        ) * 100

        # Coordenadas dos estados
        coordenadas = {
            "SP": [-23.5489, -46.6388],
            "MG": [-19.9167, -43.9345],
            "RJ": [-22.9068, -43.1729],
            "RS": [-30.0346, -51.2177],
            "PR": [-25.4284, -49.2733],
            "SC": [-27.5954, -48.5480],
            "BA": [-12.9714, -38.5014],
            "GO": [-16.6809, -49.2533],
            "PE": [-8.0476, -34.8770],
            "CE": [-3.7172, -38.5434],
            "PA": [-1.4554, -48.4902],
            "MA": [-2.5387, -44.2823],
            "MT": [-15.6014, -56.0979],
            "MS": [-20.4428, -54.6464],
            "PI": [-5.0920, -42.8038],
            "RN": [-5.7945, -35.2110],
            "AL": [-9.6658, -35.7350],
            "SE": [-10.9472, -37.0731],
            "RO": [-8.7612, -63.9005],
            "TO": [-10.2491, -48.3243],
            "AC": [-9.9740, -67.8076],
            "AM": [-3.1190, -60.0217],
            "RR": [2.8235, -60.6758],
            "AP": [0.0349, -51.0664],
            "DF": [-15.7797, -47.9297],
        }

        # Criar mapa
        m = folium.Map(location=[-15.77972, -47.92972], zoom_start=4)

        # Adicionar marcadores
        for _, estado in estados_data.iterrows():
            uf = estado["uf"]
            if uf in coordenadas:
                lat, lon = coordenadas[uf]

                # Cor baseada na taxa de mortalidade
                if estado["taxa_mortalidade"] > 2:
                    cor = "red"
                elif estado["taxa_mortalidade"] > 1:
                    cor = "orange"
                else:
                    cor = "green"

                popup_text = f"""
                <b>{uf}</b><br>
                Acidentes: {estado['id']:,}<br>
                Mortos: {estado['mortos']:,}<br>
                Taxa: {estado['taxa_mortalidade']:.1f}%
                """

                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_text, max_width=250),
                    tooltip=f"{uf}: {estado['id']} acidentes",
                    icon=folium.Icon(color=cor, icon="info-sign"),
                ).add_to(m)

        # Adicionar heatmap
        locais = df_copy[["latitude", "longitude"]].dropna()
        if len(locais) > 0:
            heat_data = [
                [row["latitude"], row["longitude"]]
                for _, row in locais.head(sample_size).iterrows()
            ]
            plugins.HeatMap(heat_data, radius=15, blur=10, max_zoom=1).add_to(m)

        # Controles
        folium.LayerControl().add_to(m)
        plugins.Fullscreen().add_to(m)

        return m

    # ==================== TABELAS ====================
    @st.cache_data
    def create_metrics_table(_self):
        df_copy = _self.df.copy()
        metrics = {
            "Total de Acidentes": f"{len(df_copy):,}",
            "Total de Mortos": f"{df_copy['mortos'].sum():,}",
            "Total de Feridos Graves": f"{df_copy['feridos_graves'].sum():,}",
            "Período Analisado": f"{df_copy['ano'].min()} - {df_copy['ano'].max()}",
            "Estados com Dados": f"{df_copy['uf'].nunique()}",
        }
        return pd.DataFrame(list(metrics.items()), columns=["Métrica", "Valor"])

    @st.cache_data
    def create_highways_table(_self):
        # Simular dados de rodovias
        np.random.seed(42)  # Para consistência
        rodovias = ["BR-101", "BR-116", "BR-040", "BR-381", "BR-153"]
        dados = []
        for br in rodovias:
            dados.append(
                {
                    "Rodovia": br,
                    "Acidentes": np.random.randint(100, 500),
                    "Mortos": np.random.randint(10, 50),
                    "Taxa Mortalidade (%)": np.random.uniform(1, 5),
                }
            )
        df_rodovias = (
            pd.DataFrame(dados)
            .sort_values("Acidentes", ascending=False)
            .reset_index(drop=True)
        )
        df_rodovias["Taxa Mortalidade (%)"] = df_rodovias["Taxa Mortalidade (%)"].round(
            2
        )
        return df_rodovias


# ==============================================================================
# FUNÇÃO PRINCIPAL STREAMLIT
# ==============================================================================
def main():
    st.set_page_config(
        page_title="Análise de Acidentes Rodoviários", page_icon="🚗", layout="wide"
    )

    # CSS personalizado
    st.markdown(
        """
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin: 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #2e86ab;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<h1 class="main-header">🚗 Análise de Acidentes Rodoviários</h1>',
        unsafe_allow_html=True,
    )

    # Carregar dados
    df = load_data()
    analyzer = DataAnalyzer(df)

    # Sidebar
    st.sidebar.title("Configurações")

    st.sidebar.markdown("### 📋 Informações")
    autor = st.sidebar.text_input("Autor:", "Equipe de Análise")

    st.sidebar.markdown("### 📊 Conteúdo do Relatório")

    opcoes_graficos = {
        "Evolução Anual": "include_evolution",
        "Análise por Estado": "include_states",
        "Tipos de Acidente": "include_types",
        "Dias da Semana": "include_weekday",
    }

    selecoes = {}
    for nome, key in opcoes_graficos.items():
        selecoes[key] = st.sidebar.checkbox(nome, value=True)

    selecoes["include_map"] = st.sidebar.checkbox("Mapa Interativo", value=True)
    selecoes["include_metrics"] = st.sidebar.checkbox("Métricas Gerais", value=True)
    selecoes["include_highways"] = st.sidebar.checkbox(
        "Análise de Rodovias", value=True
    )

    # Visualizações
    col1, col2 = st.columns(2)

    with col1:
        if selecoes["include_evolution"]:
            st.markdown("### 📈 Evolução Anual")
            fig = analyzer.create_evolution_chart()
            st.pyplot(fig)

        if selecoes["include_states"]:
            st.markdown("### 🏛️ Análise por Estado")
            fig = analyzer.create_states_chart()
            st.pyplot(fig)

    with col2:
        if selecoes["include_types"]:
            st.markdown("### 🚨 Tipos de Acidente")
            fig = analyzer.create_accident_types_chart()
            st.pyplot(fig)

        if selecoes["include_weekday"]:
            st.markdown("### 📅 Dias da Semana")
            fig = analyzer.create_weekday_chart()
            st.pyplot(fig)

    # Mapa Interativo
    if selecoes["include_map"]:
        st.markdown("### 🗺️ Mapa Interativo")
        with st.spinner("Gerando mapa..."):
            mapa = analyzer.create_interactive_map(sample_size=1000)
            folium_static(mapa, width=1000, height=500)

        st.info(
            """
        **Como usar o mapa:**
        - Clique nos marcadores para ver detalhes
        - Cores: 🔴 Alta mortalidade | 🟠 Média | 🟢 Baixa
        - Heatmap mostra densidade de acidentes
        """
        )

    # Tabelas
    if selecoes["include_metrics"]:
        st.markdown("### 📊 Métricas Gerais")
        tabela = analyzer.create_metrics_table()
        st.dataframe(tabela, use_container_width=True)

    if selecoes["include_highways"]:
        st.markdown("### 🛣️ Rodovias Mais Perigosas")
        tabela = analyzer.create_highways_table()
        st.dataframe(tabela, use_container_width=True)

    # Gerar Relatório
    st.markdown("---")
    st.markdown("### 📄 Gerar Relatório Completo")

    if st.button("📥 Gerar Relatório Word", type="primary"):
        with st.spinner("Gerando relatório..."):
            report = ReportGenerator()
            # Usar o novo método para construir o relatório
            report.build_report(analyzer, selecoes, autor)

            # Gerar documento
            buffer = report.generate_docx()

            # Download
            st.download_button(
                label="📥 Download do Relatório",
                data=buffer,
                file_name=f"relatorio_acidentes_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

            st.success("Relatório gerado com sucesso!")


if __name__ == "__main__":
    main()
