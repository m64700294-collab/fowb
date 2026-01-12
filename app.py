import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import io

st.set_page_config(
    layout="wide", 
    page_title="WB Финансовый дашборд 2025",
    page_icon="🏪",
    initial_sidebar_state="expanded"
)

# Кастомный CSS для стиля медицинского дашборда
st.markdown("""
<style>
    .main-header {font-size: 3rem; color: #1f77b4; text-align: center; margin-bottom: 2rem;}
    .kpi-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1rem; border-radius: 10px; color: white; text-align: center;}
    .metric-value {font-size: 2.5rem; font-weight: bold;}
    .metric-label {font-size: 1rem; opacity: 0.9;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🏪 Финансовый отчёт Wildberries 2025</h1>', unsafe_allow_html=True)

# Sidebar для загрузки файла
st.sidebar.header("📁 Загрузка данных")
uploaded_file = st.sidebar.file_uploader("Выберите Excel файл", type="xlsx")

if uploaded_file is not None:
    # Чтение данных с учетом структуры вашей таблицы
    df = pd.read_excel(uploaded_file)
    
    # Очистка и подготовка данных (ориентируясь на вашу структуру)
    df.columns = ['Article', 'Order_ID', 'Date', 'Supplier', 'Col5', 'Col6', 'Quantity', 'Total_Price']
    
    # Преобразование типов
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Order_ID'] = df['Order_ID'].astype(str)
    df['Total_Price'] = pd.to_numeric(df['Total_Price'], errors='coerce')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    
    # Удаление пустых строк
    df = df.dropna(subset=['Total_Price'])
    df = df[df['Total_Price'] > 0]
    
    st.sidebar.success(f"✅ Загружено {len(df):,} строк данных")
    st.sidebar.metric("Период данных", f"{df['Date'].min().strftime('%d.%m')}-{df['Date'].max().strftime('%d.%m.%Y')}")
    
    # Основные KPI (как в медицинском дашборде - 4 карточки)
    col1, col2, col3, col4 = st.columns(4)
    
    total_orders = df['Order_ID'].nunique()
    total_revenue = df['Total_Price'].sum()
    avg_check = total_revenue / total_orders if total_orders > 0 else 0
    profit_margin = 0.25  # Предполагаемая маржа 25%
    total_profit = total_revenue * profit_margin
    
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <div class="metric-label">Заказы</div>
            <div class="metric-value">{:,}</div>
        </div>
        """.format(total_orders), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <div class="metric-label">Оборот</div>
            <div class="metric-value">₽{:,.0f}</div>
        </div>
        """.format(total_revenue), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="kpi-card">
            <div class="metric-label">Средний чек</div>
            <div class="metric-value">₽{:,.0f}</div>
        </div>
        """.format(avg_check), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="kpi-card">
            <div class="metric-label">Прибыль (25%)</div>
            <div class="metric-value">₽{:,.0f}</div>
        </div>
        """.format(total_profit), unsafe_allow_html=True)
    
    # 2 ряда графиков (как в мед. дашборде)
    st.subheader("📊 Аналитика продаж")
    
    # Первый ряд: Оборот по месяцам + Топ поставщики
    col1, col2 = st.columns(2)
    
    with col1:
        # Оборот по месяцам (комбинированный график)
        monthly_data = df.groupby(df['Date'].dt.to_period('M'))['Total_Price'].agg(['sum', 'count']).reset_index()
        monthly_data['Month'] = monthly_data['Date'].astype(str).str[:7]
        
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(
            go.Bar(name="Оборот", x=monthly_data['Month'], y=monthly_data['sum'], 
                   marker_color='#1f77b4'), secondary_y=False
        )
        fig1.add_trace(
            go.Scatter(name="Заказы", x=monthly_data['Month'], y=monthly_data['count'],
                      mode='lines+markers', line=dict(color='#ff7f0e')), secondary_y=True
        )
        fig1.update_layout(title="Оборот и заказы по месяцам", height=400)
        fig1.update_yaxes(title_text="Оборот, ₽", secondary_y=False)
        fig1.update_yaxes(title_text="Заказы, шт", secondary_y=True)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Топ-10 поставщиков
        top_suppliers = df.groupby('Supplier')['Total_Price'].sum().nlargest(10)
        fig2 = px.bar(x=top_suppliers.values, y=top_suppliers.index, 
                     title="Топ-10 поставщиков по обороту",
                     orientation='h', color=top_suppliers.values,
                     color_continuous_scale='Viridis')
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Второй ряд: Топ товары + Распределение по чеку
    col1, col2 = st.columns(2)
    
    with col1:
        # Топ-20 артикулов
        top_articles = df.groupby('Article')['Total_Price'].sum().nlargest(20)
        fig3 = px.treemap(top_articles.reset_index(), path=[px.Constant('Топ товары'), 'Article'], 
                         values='Total_Price', title="Топ-20 артикулов",
                         color='Total_Price', color_continuous_scale='Plasma')
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # Распределение по размеру чека
        df['Check_Size'] = pd.cut(df['Total_Price'], 
                                 bins=[0, 100, 500, 1000, float('inf')], 
                                 labels=['<100₽', '100-500₽', '500-1000₽', '>1000₽'])
        check_dist = df.groupby('Check_Size').agg({
            'Order_ID': 'nunique',
            'Total_Price': 'sum'
        }).round(0)
        
        fig4 = px.bar(check_dist, x=check_dist.index, y=['Order_ID', 'Total_Price'],
                     title="Заказы и оборот по размеру чека",
                     barmode='group')
        st.plotly_chart(fig4, use_container_width=True)
    
    # Таблица лидеров (как в мед. дашборде)
    st.subheader("🏆 Рейтинг поставщиков")
    
    leaders_table = df.groupby('Supplier').agg({
        'Order_ID': 'nunique',
        'Total_Price': 'sum',
        'Quantity': 'sum'
    }).round(0)
    leaders_table['Avg_Check'] = leaders_table['Total_Price'] / leaders_table['Order_ID']
    leaders_table = leaders_table.nlargest(15, 'Total_Price').reset_index()
    leaders_table.columns = ['Поставщик', 'Заказы', 'Оборот, ₽', 'Количество', 'Средний чек, ₽']
    
    st.dataframe(
        leaders_table.style.format({
            'Оборот, ₽': '{:,.0f}',
            'Средний чек, ₽': '{:,.0f}'
        }).background_gradient(subset=['Оборот, ₽'], cmap='Greens'),
        use_container_width=True
    )
    
    # Динамика средних чеков
    st.subheader("📈 Динамика показателей")
    col1, col2 = st.columns(2)
    
    with col1:
        daily_avg = df.groupby(df['Date'].dt.date).agg({
            'Total_Price': ['sum', 'count']
        }).reset_index()
        daily_avg.columns = ['Date', 'Revenue', 'Orders']
        daily_avg['Avg_Check'] = daily_avg['Revenue'] / daily_avg['Orders']
        
        fig5 = px.line(daily_avg, x='Date', y='Avg_Check', 
                      title="Средний чек по дням")
        st.plotly_chart(fig5, use_container_width=True)
    
    # Детальная таблица (скрытая по умолчанию)
    with st.expander("📋 Полная таблица транзакций (первые 1000)"):
        st.dataframe(df[['Article', 'Supplier', 'Date', 'Quantity', 'Total_Price']].head(1000).style.format({
            'Total_Price': '{:,.0f}₽'
        }), use_container_width=True)

else:
    st.info("👆 Пожалуйста, загрузите файл **Novaia-tablitsa-12.xlsx** через боковую панель")
    st.markdown("""
    ### Структура ожидаемых данных:
    ```
    Article    | Order_ID   | Date      | Supplier   | Quantity | Total_Price
    din1010252 | 293818328  | 2025-01-02| AtlasWeld  | 1        | 70.85
    atlks25    | 293818328  | 2025-01-02| AtlasWeld  | 5        | 1361.25
    ```
    """)

# Футер
st.markdown("---")
st.markdown("*Дашборд создан для анализа продаж Wildberries | Данные: 2025 год*")
