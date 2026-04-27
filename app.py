st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Fondo general */
.stApp {
    background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
    color: #e5e7eb;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #020617;
    border-right: 1px solid #1e293b;
}

/* Header */
.header {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 20px;
}

/* Tarjetas */
div[data-testid="stForm"], div[data-testid="stExpander"] {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 20px;
}

/* Texto */
h1, h2, h3 {
    color: #f1f5f9 !important;
}

/* Botones elegantes */
div.stButton > button {
    background: #1d4ed8;
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: 500;
    padding: 0.6rem;
}

div.stButton > button:hover {
    background: #2563eb;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    color: #94a3b8;
}

.stTabs [aria-selected="true"] {
    color: #3b82f6 !important;
    border-bottom: 2px solid #3b82f6;
}

/* Inputs */
input, textarea, select {
    background-color: #020617 !important;
    color: #e5e7eb !important;
    border: 1px solid #1e293b !important;
}

/* Métricas */
[data-testid="stMetricValue"] {
    color: #f8fafc;
    font-size: 1.8rem;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    background-color: #020617;
    border-radius: 10px;
}

/* Alertas */
div[data-testid="stAlert"] {
    background-color: #020617;
    border: 1px solid #1e293b;
    color: #e5e7eb;
}
</style>
""", unsafe_allow_html=True)
