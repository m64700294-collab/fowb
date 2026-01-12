import streamlit as st
import pandas as pd
import plotly.express as px
import openpyxl

st.set_page_config(layout="wide", page_title="WB Дашборд")

@st.cache_data  # ← КЛЮЧЕВОЕ! Кеширует данные
def load_data(uploaded_file):
    return pd.read_excel(uploaded_file)

st.title("🏪 WB Финансовый дашборд 2025")

# Загрузка файла
uploaded_file = st.sidebar.file_uploader("📁 XLSX файл", type="xlsx")

if uploaded_file:
    with st.spinner("Загружаем данные..."):
        df = load_data(uploaded_file)
    
    # Быстрая обработка (только нужные колонки)
    df['Date'] = pd.to_datetime(df.iloc[:, 2], errors='coerce')  # 3-я колонка = Date
    df['Total_Price'] = pd.to_numeric(df.iloc[:, -1], errors='coerce')  # Последняя = цена
    
    # KPI (1 строка)
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Заказы", df.iloc[:, 1].nunique())
    with col2: st.metric("Оборот", f"₽{df['Total_Price'].sum():,.0f}")
    with col3: st.metric("Средний чек", f"₽{df['Total_Price'].mean():,.0f}")
    
    # 1 график (самый быстрый)
    monthly = df.groupby(df['Date'].dt.month)['Total_Price'].sum()
    fig = px.bar(x=monthly.index, y=monthly.values, title="Оборот по месяцам")
    st.plotly_chart(fig, use_container_width=True)
    
    # Топ-поставщики
    suppliers = df.groupby(df.iloc[:, 3])['Total_Price'].sum().nlargest(10)
    st.bar_chart(suppliers)
    
else:
    st.info("👈 Загрузите Novaia-tablitsa-12.xlsx")
