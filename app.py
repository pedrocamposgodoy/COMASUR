import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
import matplotlib.pyplot as plt

# --- CONFIG ---
st.set_page_config(page_title="COMASUR Fleet Manager", layout="wide")

DB_NAME = "comasur_flota.db"
UBICACIONES = ["NAVE ALBOLOTE", "ZAIDIN", "MOTRIL", "MALAGA"]

# --- CSS ---
st.markdown("""
<style>
.stApp {background: linear-gradient(180deg,#e6edf5,#dbe7f3);}
</style>
""", unsafe_allow_html=True)

# --- DB ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS vehiculos (
        matricula TEXT PRIMARY KEY,
        modelo TEXT,
        ubicacion TEXT,
        fecha_itv TEXT,
        fecha_seguro TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS mantenimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula TEXT,
        fecha TEXT,
        concepto TEXT,
        coste REAL,
        factura TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

def execute(q, p=()):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(q, p)
        conn.commit()

# --- ALERTAS ---
def get_estado(fecha):
    if not fecha:
        return "🟢 OK"
    f = datetime.fromisoformat(fecha)
    diff = (f - datetime.today()).days
    if diff < 0:
        return "🔴 Crítico"
    elif diff < 30:
        return "🟡 Revisar"
    return "🟢 OK"

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚛 COMASUR")
    menu = st.radio("", ["📋 Flota","➕ Vehículo","🔧 Mantenimiento","💾 Backup"])

# --- HEADER ---
st.title("🚛 Fleet Manager")

# --- FLOTA ---
if menu == "📋 Flota":

    df = pd.read_sql("SELECT * FROM vehiculos", sqlite3.connect(DB_NAME))

    alertas = []
    for _, v in df.iterrows():
        if get_estado(v["fecha_itv"]) != "🟢 OK":
            alertas.append(f"ITV {v['matricula']}")
        if get_estado(v["fecha_seguro"]) != "🟢 OK":
            alertas.append(f"Seguro {v['matricula']}")

    if alertas:
        st.warning("🔔 Alertas: " + ", ".join(alertas))

    if not df.empty:

        df["Estado ITV"] = df["fecha_itv"].apply(get_estado)
        df["Estado Seguro"] = df["fecha_seguro"].apply(get_estado)

        st.dataframe(df)

        # COSTES
        df_m = pd.read_sql("SELECT * FROM mantenimientos", sqlite3.connect(DB_NAME))
        df_m["fecha"] = pd.to_datetime(df_m["fecha"])
        df_year = df_m[df_m["fecha"].dt.year == datetime.today().year]

        st.metric("💸 Total año", f"{df_year['coste'].sum():.2f} €")

        # GRAFICO
        if not df_year.empty:
            grp = df_year.groupby("matricula")["coste"].sum()
            fig, ax = plt.subplots()
            grp.plot(kind="bar", ax=ax)
            st.pyplot(fig)

        # DETALLE VEHICULO
        sel = st.selectbox("Vehículo", df["matricula"])
        hist = df_m[df_m["matricula"] == sel]

        st.markdown("### Historial")
        st.dataframe(hist)

        st.metric("Total vehículo", f"{hist['coste'].sum():.2f} €")

    else:
        st.warning("No hay vehículos")

# --- NUEVO ---
elif menu == "➕ Vehículo":

    with st.form("alta"):
        mat = st.text_input("Matrícula")
        mod = st.text_input("Modelo")
        ubi = st.selectbox("Ubicación", UBICACIONES)
        itv = st.date_input("ITV")
        seg = st.date_input("Seguro")

        if st.form_submit_button("Crear"):
            execute("INSERT INTO vehiculos VALUES (?,?,?,?,?)",
                    (mat, mod, ubi, str(itv), str(seg)))
            st.success("Creado")

# --- MANTENIMIENTO ---
elif menu == "🔧 Mantenimiento":

    mats = pd.read_sql("SELECT matricula FROM vehiculos", sqlite3.connect(DB_NAME))["matricula"]

    if len(mats)>0:

        with st.form("mant"):
            v = st.selectbox("Vehículo", mats)
            concepto = st.text_input("Concepto")
            coste = st.number_input("Coste", 0.0)
            file = st.file_uploader("Factura PDF")

            ruta = ""
            if file:
                os.makedirs("facturas", exist_ok=True)
                ruta = f"facturas/{file.name}"
                with open(ruta,"wb") as f:
                    f.write(file.getbuffer())

            if st.form_submit_button("Guardar"):
                execute("INSERT INTO mantenimientos (matricula,fecha,concepto,coste,factura) VALUES (?,?,?,?,?)",
                        (v, str(date.today()), concepto, coste, ruta))
                st.success("Guardado")

# --- BACKUP ---
elif menu == "💾 Backup":

    with open(DB_NAME,"rb") as f:
        st.download_button("Descargar DB", f, "backup.db")
