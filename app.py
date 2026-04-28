import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime

# --- CONFIG ---
st.set_page_config(page_title="COMASUR Fleet", layout="wide")

DB = "comasur_flota.db"
UBICACIONES = ["NAVE ALBOLOTE", "ZAIDIN", "MOTRIL", "MALAGA"]

# --- ESTILO ---
st.markdown("""
<style>
.stApp { background: linear-gradient(180deg,#eef3f9,#dbe7f3); }
.card {
    background-color: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    border: 1px solid #e2e8f0;
    margin-bottom: 20px;
}
.title { font-size: 18px; font-weight: 700; }
.subtitle { color: #64748b; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- DB INIT ---
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS vehiculos (
        matricula TEXT PRIMARY KEY,
        marca TEXT,
        modelo TEXT,
        ubicacion TEXT,
        fecha_itv TEXT,
        fecha_seguro TEXT,
        fecha_revision TEXT,
        observaciones TEXT
    )''')

    # 🔥 MIGRACIÓN automática
    try:
        c.execute("ALTER TABLE vehiculos ADD COLUMN marca TEXT")
    except:
        pass

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

def run(q, p=()):
    with sqlite3.connect(DB) as conn:
        conn.execute(q, p)
        conn.commit()

def get_df(query):
    return pd.read_sql(query, sqlite3.connect(DB))

# --- ESTADO ---
def estado(fecha):
    if not fecha:
        return "🟢 OK"
    diff = (datetime.fromisoformat(str(fecha)) - datetime.today()).days
    if diff < 0:
        return "🔴 Crítico"
    elif diff < 30:
        return "🔴 Urgente"
    elif diff < 120:
        return "🟡 Revisar"
    else:
        return "🟢 OK"

# --- SESSION ---
if "vehiculo_sel" not in st.session_state:
    st.session_state.vehiculo_sel = None

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("LOGO.png", use_container_width=True)
    except:
        st.write("Sube LOGO.png")

    menu = st.radio("", ["📋 Flota", "➕ Vehículo", "💾 Backup"])

# =====================================================
# DASHBOARD
# =====================================================
if menu == "📋 Flota" and st.session_state.vehiculo_sel is None:

    st.title("🚛 Flota COMASUR")
    df = get_df("SELECT * FROM vehiculos")

    if df.empty:
        st.warning("No hay vehículos")
    else:
        cols = st.columns(3)

        for i, (_, v) in enumerate(df.iterrows()):
            with cols[i % 3]:

                st.markdown('<div class="card">', unsafe_allow_html=True)

                st.markdown(f"<div class='title'>🚐 {v['matricula']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='subtitle'>{v.get('marca','')} {v['modelo']}</div>", unsafe_allow_html=True)

                st.write(f"📍 {v['ubicacion']}")
                st.write(f"ITV: {estado(v['fecha_itv'])}")
                st.write(f"Seguro: {estado(v['fecha_seguro'])}")

                if st.button("🚐 Ver ficha", key=v["matricula"]):
                    st.session_state.vehiculo_sel = v["matricula"]
                    st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# FICHA
# =====================================================
elif st.session_state.vehiculo_sel:

    old_mat = st.session_state.vehiculo_sel
    df = get_df(f"SELECT * FROM vehiculos WHERE matricula='{old_mat}'")
    v = df.iloc[0]

    st.title(f"🚐 {old_mat}")

    if st.button("⬅️ Volver"):
        st.session_state.vehiculo_sel = None
        st.rerun()

    with st.form("edit"):

        nueva_mat = st.text_input("Matrícula", v["matricula"])
        marca = st.text_input("Marca", v.get("marca",""))
        modelo = st.text_input("Modelo", v["modelo"])

        ubicacion = st.selectbox("Ubicación", UBICACIONES, index=UBICACIONES.index(v["ubicacion"]))

        itv = st.date_input("ITV", datetime.fromisoformat(v["fecha_itv"]) if v["fecha_itv"] else date.today())
        seguro = st.date_input("Seguro", datetime.fromisoformat(v["fecha_seguro"]) if v["fecha_seguro"] else date.today())
        revision = st.date_input("Revisión", datetime.fromisoformat(v["fecha_revision"]) if v["fecha_revision"] else date.today())

        obs = st.text_area("Observaciones", v["observaciones"])

        if st.form_submit_button("Guardar"):

            run("""
            UPDATE vehiculos SET matricula=?, marca=?, modelo=?, ubicacion=?, fecha_itv=?, fecha_seguro=?, fecha_revision=?, observaciones=?
            WHERE matricula=?""",
            (nueva_mat, marca, modelo, ubicacion, str(itv), str(seguro), str(revision), obs, old_mat))

            run("UPDATE mantenimientos SET matricula=? WHERE matricula=?", (nueva_mat, old_mat))

            st.session_state.vehiculo_sel = nueva_mat
            st.success("Guardado")
            st.rerun()

    # --- MANTENIMIENTO ---
    st.markdown("### 🔧 Mantenimiento")

    with st.form("mant"):
        concepto = st.text_input("Concepto")
        coste = st.number_input("Coste", 0.0)
        file = st.file_uploader("Factura")

        data = file.getvalue() if file else None
        name = file.name if file else None

        if st.form_submit_button("Añadir"):
            run("INSERT INTO mantenimientos (matricula,fecha,concepto,coste,factura,nombre_factura) VALUES (?,?,?,?,?,?)",
                (st.session_state.vehiculo_sel, str(date.today()), concepto, coste, data, name))
            st.rerun()

    df_m = get_df(f"SELECT * FROM mantenimientos WHERE matricula='{st.session_state.vehiculo_sel}'")

    for _, row in df_m.iterrows():
        with st.expander(f"{row['fecha']} - {row['concepto']}"):
            with st.form(f"edit_{row['id']}"):
                concepto = st.text_input("Concepto", row["concepto"])
                coste = st.number_input("Coste", value=float(row["coste"]))

                if row["factura"]:
                    st.download_button("Factura", row["factura"], row["nombre_factura"])

                c1, c2 = st.columns(2)

                if c1.form_submit_button("Guardar"):
                    run("UPDATE mantenimientos SET concepto=?, coste=? WHERE id=?",
                        (concepto, coste, row["id"]))
                    st.rerun()

                if c2.form_submit_button("Borrar"):
                    run("DELETE FROM mantenimientos WHERE id=?", (row["id"],))
                    st.rerun()

# =====================================================
# NUEVO VEHÍCULO
# =====================================================
elif menu == "➕ Vehículo":

    st.title("Nuevo vehículo")

    with st.form("alta"):
        mat = st.text_input("Matrícula")
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        ubi = st.selectbox("Ubicación", UBICACIONES)

        itv = st.date_input("ITV")
        seg = st.date_input("Seguro")
        rev = st.date_input("Revisión")

        obs = st.text_area("Observaciones")

        if st.form_submit_button("Crear"):
            run("INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?)",
                (mat, marca, modelo, ubi, str(itv), str(seg), str(rev), obs))
            st.success("Vehículo creado")
            st.rerun()

# =====================================================
# BACKUP
# =====================================================
elif menu == "💾 Backup":

    st.title("Backup")

    with open(DB,"rb") as f:
        st.download_button("Descargar", f, "backup.db")

    up = st.file_uploader("Subir backup", type=["db"])
    if up:
        with open(DB,"wb") as f:
            f.write(up.getbuffer())
        st.success("Restaurado")
        st.rerun()
