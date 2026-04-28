import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

# --- CONFIG ---
st.set_page_config(page_title="COMASUR Fleet Manager", layout="wide")
DB_NAME = "comasur_flota.db"
UBICACIONES = ["NAVE ALBOLOTE", "ZAIDIN", "MOTRIL", "MALAGA"]

# --- ESTILO ---
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
        factura BLOB,
        nombre_factura TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

def execute(q, p=()):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(q, p)
        conn.commit()

# --- ESTADO ---
def estado(fecha):
    if not fecha:
        return "🟢 OK"
    diff = (datetime.fromisoformat(fecha) - datetime.today()).days
    if diff < 0: return "🔴 Crítico"
    if diff < 30: return "🟡 Revisar"
    return "🟢 OK"

# --- PDF ---
def generar_pdf(df, matricula):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elements = []
    elements.append(Paragraph(f"Informe Vehículo: {matricula}", styles["Title"]))
    elements.append(Spacer(1, 10))

    data = [["Fecha","Concepto","Coste (€)"]]
    for _, row in df.iterrows():
        data.append([row["fecha"], row["concepto"], f"{row['coste']} €"])

    table = Table(data)
    table.setStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white)
    ])

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return buffer

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚛 COMASUR")
    menu = st.radio("", ["📊 Dashboard","📋 Flota","➕ Vehículo","🔧 Mantenimiento","💾 Backup"])

# --- DASHBOARD ---
if menu == "📊 Dashboard":

    df_v = pd.read_sql("SELECT * FROM vehiculos", sqlite3.connect(DB_NAME))
    df_m = pd.read_sql("SELECT * FROM mantenimientos", sqlite3.connect(DB_NAME))

    col1,col2,col3 = st.columns(3)

    total = df_m["coste"].sum() if not df_m.empty else 0
    col1.metric("💸 Coste total", f"{total:.2f} €")
    col2.metric("🚚 Vehículos", len(df_v))
    col3.metric("🔧 Intervenciones", len(df_m))

    if not df_m.empty:
        grp = df_m.groupby("matricula")["coste"].sum()
        if len(grp) > 1:
            fig, ax = plt.subplots(figsize=(4,3))
            grp.plot(kind="bar", ax=ax)
            st.pyplot(fig)

# --- FLOTA ---
elif menu == "📋 Flota":

    df = pd.read_sql("SELECT * FROM vehiculos", sqlite3.connect(DB_NAME))

    if not df.empty:

        df["ITV"] = df["fecha_itv"].apply(estado)
        df["Seguro"] = df["fecha_seguro"].apply(estado)

        # FILTROS
        ubic = st.selectbox("Filtrar ubicación", ["Todas"] + UBICACIONES)
        if ubic != "Todas":
            df = df[df["ubicacion"] == ubic]

        st.dataframe(df, use_container_width=True)

        # DETALLE
        sel = st.selectbox("Vehículo", df["matricula"])
        df_m = pd.read_sql(f"SELECT * FROM mantenimientos WHERE matricula='{sel}'", sqlite3.connect(DB_NAME))

        st.markdown("### Historial")

        if not df_m.empty:
            for _, r in df_m.iterrows():
                c1,c2,c3,c4 = st.columns(4)
                c1.write(r["fecha"])
                c2.write(r["concepto"])
                c3.write(f"{r['coste']} €")

                if r["factura"]:
                    c4.download_button("📄 Factura", r["factura"], r["nombre_factura"])

            st.metric("Total vehículo", f"{df_m['coste'].sum():.2f} €")

            # PDF
            pdf = generar_pdf(df_m, sel)
            st.download_button("🧾 Descargar informe PDF", pdf, f"{sel}.pdf")

        else:
            st.info("Sin mantenimientos")

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

            data = None
            name = ""

            if file:
                data = file.getvalue()
                name = file.name

            if st.form_submit_button("Guardar"):
                execute("INSERT INTO mantenimientos (matricula,fecha,concepto,coste,factura,nombre_factura) VALUES (?,?,?,?,?,?)",
                        (v, str(date.today()), concepto, coste, data, name))
                st.success("Guardado")

# --- BACKUP ---
elif menu == "💾 Backup":

    with open(DB_NAME,"rb") as f:
        st.download_button("⬇️ Backup BD", f, "backup.db")
