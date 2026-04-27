st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* 🌫️ Fondo gris azulado elegante */
.stApp {
    background: linear-gradient(180deg, #e6edf5 0%, #dbe7f3 100%);
    color: #0f172a;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #f1f5f9;
    border-right: 1px solid #cbd5e1;
}

/* Header */
.header {
    background: #ffffff;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

/* Tarjetas */
div[data-testid="stForm"], div[data-testid="stExpander"] {
    background: #ffffff;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 6px 25px rgba(15, 23, 42, 0.08);
}

/* Títulos */
h1, h2, h3 {
    color: #0f172a !important;
}

/* Botones suaves */
div.stButton > button {
    background: linear-gradient(135deg, #64748b, #94a3b8);
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: 600;
    padding: 0.6rem;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #475569, #64748b);
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    color: #64748b;
}

.stTabs [aria-selected="true"] {
    color: #334155 !important;
    border-bottom: 2px solid #334155;
}

/* Inputs */
input, textarea, select {
    background-color: #f8fafc !important;
    color: #0f172a !important;
    border: 1px solid #cbd5e1 !important;
}

/* Métricas */
[data-testid="stMetricValue"] {
    color: #1e293b;
    font-size: 1.8rem;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    background-color: #ffffff;
    border-radius: 10px;
}

/* Alertas */
div[data-testid="stAlert"] {
    background-color: #f8fafc;
    color: #0f172a;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
}
</style>
""", unsafe_allow_html=True)
