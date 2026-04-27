import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# --- CONFIG ---
st.set_page_config(
    page_title="COMASUR Fleet Manager",
    page_icon="🚚",
    layout="wide"
)

# --- 🎨 CSS (GRIS AZULADO PRO) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Fondo */
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

/* Botones */
div.stButton > button {
    background: linear-gradient(135deg, #64748b, #94a3b8);
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: 600;
}

/* Tabs */
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
</style>
""", unsafe_allow_html=True)

# --- CONFIG APP ---
UBICACIONES = ["NAVE ALBOLOTE", "ZAIDIN", "MOTRIL", "MALAGA"]
DB_NAME = "comasur_flota.db"

# --- DB ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS vehiculos (
        matricula TEXT PRIMARY KEY,
        modelo TEXT,
        fecha_compra TEXT,
        vida_util INTEGER,
        fecha_retirada TEXT,
        ubicacion TEXT,
        tipo_mantenimiento TEXT,
        caracteristicas TEXT,
        prov_recambios TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS mantenimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula TEXT,
        fecha TEXT,
        operacion TEXT,
        responsable TEXT,
        seguro_ok BOOLEAN,
        impuestos_ok BOOLEAN,
        observaciones TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

def execute_db(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(query, params)
        conn.commit()

# --- SIDEBAR ---
with st.sidebar:
    st.image("LOGO.png", use_container_width=True)
    st.markdown("### COMASUR")
    st.caption("Gestión de flota")

    menu = st.radio("", [
        "📋 Flota",
        "➕ Nuevo Vehículo",
        "🔧 Mantenimiento",
        "💾 Backup"
    ])

# --- HEADER ---
st.markdown("""
<div class="header">
<h2>🚛 COMASUR Fleet Manager</h2>
<p style="color:#64748b;">Control de vehículos y mantenimiento</p>
</div>
""", unsafe_allow_html=True)

# --- FLOTAS ---
if menu == "📋 Flota":

    df = pd.read_sql("SELECT * FROM vehiculos", sqlite3.connect(DB_NAME))

    c1, c2, c3 = st.columns(3)
    c1.metric("Vehículos", len(df))
    c2.metric("Ubicaciones", df["ubicacion"].nunique() if not df.empty else 0)
    c3.metric("Estado", "Operativo")

    if not df.empty:
        st.dataframe(df, use_container_width=True)

        sel = st.selectbox("Seleccionar vehículo", df["matricula"])
        v = df[df["matricula"] == sel].iloc[0]

        tab1, tab2 = st.tabs(["Ficha", "Editar"])

        with tab1:
            st.metric("Modelo", v["modelo"])
            st.metric("Ubicación", v["ubicacion"])
            st.info(v["caracteristicas"])

        with tab2:
            with st.form("edit"):
                mod = st.text_input("Modelo", v["modelo"])
                ubi = st.selectbox("Ubicación", UBICACIONES, index=UBICACIONES.index(v["ubicacion"]) if v["ubicacion"] in UBICACIONES else 0)
                car = st.text_area("Características", v["caracteristicas"])

                if st.form_submit_button("Guardar"):
                    execute_db(
                        "UPDATE vehiculos SET modelo=?, ubicacion=?, caracteristicas=? WHERE matricula=?",
                        (mod, ubi, car, sel)
                    )
                    st.success("Actualizado")
                    st.rerun()
    else:
        st.warning("No hay vehículos")

# --- ALTA ---
elif menu == "➕ Nuevo Vehículo":

    with st.form("alta"):
        mat = st.text_input("Matrícula")
        mod = st.text_input("Modelo")
        ubi = st.selectbox("Ubicación", UBICACIONES)

        if st.form_submit_button("Crear"):
            if mat and mod:
                execute_db(
                    "INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?,?)",
                    (mat, mod, str(date.today()), 10, str(date.today()), ubi, "", "", "")
                )
                st.success("Vehículo creado")
            else:
                st.error("Faltan datos")

# --- MANTENIMIENTO ---
elif menu == "🔧 Mantenimiento":

    mats = pd.read_sql("SELECT matricula FROM vehiculos", sqlite3.connect(DB_NAME))["matricula"].tolist()

    if mats:
        with st.form("mant"):
            v = st.selectbox("Vehículo", mats)
            op = st.text_input("Operación")

            if st.form_submit_button("Guardar"):
                execute_db(
                    "INSERT INTO mantenimientos (matricula, fecha, operacion) VALUES (?,?,?)",
                    (v, str(date.today()), op)
                )
                st.success("Guardado")
    else:
        st.warning("No hay vehículos")

# --- BACKUP ---
elif menu == "💾 Backup":

    with open(DB_NAME, "rb") as f:
        st.download_button("Descargar copia", f, "backup.db")
