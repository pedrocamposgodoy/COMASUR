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
.stApp {
    background: linear-gradient(180deg,#eef3f9,#dbe7f3);
}

.card {
    background-color: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    border: 1px solid #e2e8f0;
    margin-bottom: 20px;
}

.title {
    font-size: 18px;
    font-weight: 700;
}
.subtitle {
    color: #64748b;
    font-size: 14px;
}

.stButton button {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- DB INIT ---
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS vehiculos (
        matricula TEXT PRIMARY KEY,
        modelo TEXT,
        ubicacion TEXT,
        fecha_itv TEXT,
        fecha_seguro TEXT,
        fecha_revision TEXT,
        observaciones TEXT
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

def run(q, p=()):
    with sqlite3.connect(DB) as conn:
        conn.execute(q, p)
        conn.commit()

def get_df(query):
    conn = sqlite3.connect(DB)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

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
# 📋 DASHBOARD
# =====================================================
if menu == "📋 Flota" and st.session_state.vehiculo_sel is None:

    st.title("🚛 Flota COMASUR")

    df = get_df("SELECT * FROM vehiculos")

    if df.empty:
        st.warning("No hay vehículos")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Vehículos", len(df))
        c2.metric("Críticos", sum(df["fecha_itv"].apply(lambda x: estado(x)=="🔴 Crítico")))
        c3.metric("OK", sum(df["fecha_itv"].apply(lambda x: estado(x)=="🟢 OK")))

        st.markdown("### Estado general")

        cols = st.columns(3)

        for i, (_, v) in enumerate(df.iterrows()):
            with cols[i % 3]:

                st.markdown('<div class="card">', unsafe_allow_html=True)

                st.markdown(f"<div class='title'>🚐 {v['matricula']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='subtitle'>{v['modelo']}</div>", unsafe_allow_html=True)

                st.write(f"📍 {v['ubicacion']}")
                st.write(f"ITV: {estado(v['fecha_itv'])}")
                st.write(f"Seguro: {estado(v['fecha_seguro'])}")

                if st.button("🚐 Ver ficha", key=v["matricula"]):
                    st.session_state.vehiculo_sel = v["matricula"]
                    st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 🚐 FICHA VEHÍCULO
# =====================================================
elif st.session_state.vehiculo_sel:

    mat = st.session_state.vehiculo_sel
    df = get_df(f"SELECT * FROM vehiculos WHERE matricula='{mat}'")
    v = df.iloc[0]

    st.title(f"🚐 Ficha {mat}")

    if st.button("⬅️ Volver"):
        st.session_state.vehiculo_sel = None
        st.rerun()

    st.markdown("### ✏️ Datos del vehículo")

    with st.form("editar"):
        modelo = st.text_input("Modelo", v["modelo"])
        ubicacion = st.selectbox("Ubicación", UBICACIONES, index=UBICACIONES.index(v["ubicacion"]))
        
        itv = st.date_input("ITV", datetime.fromisoformat(v["fecha_itv"]) if v["fecha_itv"] else date.today())
        seguro = st.date_input("Seguro", datetime.fromisoformat(v["fecha_seguro"]) if v["fecha_seguro"] else date.today())
        revision = st.date_input("Revisión", datetime.fromisoformat(v["fecha_revision"]) if v["fecha_revision"] else date.today())

        obs = st.text_area("Observaciones", v["observaciones"])

        if st.form_submit_button("Guardar cambios"):
            run("""
            UPDATE vehiculos SET modelo=?, ubicacion=?, fecha_itv=?, fecha_seguro=?, fecha_revision=?, observaciones=? 
            WHERE matricula=?""",
            (modelo, ubicacion, str(itv), str(seguro), str(revision), obs, mat))
            st.success("Guardado")
            st.rerun()

    # --- MANTENIMIENTO ---
    st.markdown("### 🔧 Añadir mantenimiento")

    with st.form("mant"):
        concepto = st.text_input("Concepto")
        coste = st.number_input("Coste", 0.0)
        file = st.file_uploader("Factura PDF")

        data = file.getvalue() if file else None
        name = file.name if file else None

        if st.form_submit_button("Guardar mantenimiento"):
            run(
                "INSERT INTO mantenimientos (matricula,fecha,concepto,coste,factura,nombre_factura) VALUES (?,?,?,?,?,?)",
                (mat, str(date.today()), concepto, coste, data, name)
            )
            st.success("Añadido")
            st.rerun()

    # --- HISTORIAL EDITABLE ---
    st.markdown("### 📋 Historial de mantenimiento")

    df_m = get_df(f"SELECT * FROM mantenimientos WHERE matricula='{mat}'")

    if not df_m.empty:
        for _, row in df_m.iterrows():

            with st.expander(f"🧾 {row['fecha']} - {row['concepto']}"):

                with st.form(f"edit_{row['id']}"):

                    concepto = st.text_input("Concepto", row["concepto"])
                    coste = st.number_input("Coste", value=float(row["coste"]))

                    if row["factura"]:
                        st.download_button("📄 Ver factura", row["factura"], row["nombre_factura"])

                    col1, col2 = st.columns(2)

                    if col1.form_submit_button("💾 Guardar"):
                        run("""
                        UPDATE mantenimientos 
                        SET concepto=?, coste=? 
                        WHERE id=?""",
                        (concepto, coste, row["id"]))
                        st.success("Actualizado")
                        st.rerun()

                    if col2.form_submit_button("🗑️ Borrar"):
                        run("DELETE FROM mantenimientos WHERE id=?", (row["id"],))
                        st.warning("Eliminado")
                        st.rerun()

        st.metric("💸 Total vehículo", f"{df_m['coste'].sum():.2f} €")

    else:
        st.info("Sin mantenimientos")

# =====================================================
# ➕ NUEVO VEHÍCULO
# =====================================================
elif menu == "➕ Vehículo":

    st.title("Nuevo vehículo")

    with st.form("alta"):
        mat = st.text_input("Matrícula")
        mod = st.text_input("Modelo")
        ubi = st.selectbox("Ubicación", UBICACIONES)
        itv = st.date_input("ITV")
        seg = st.date_input("Seguro")
        rev = st.date_input("Revisión")
        obs = st.text_area("Observaciones")

        if st.form_submit_button("Crear"):
            run("INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?)",
                (mat, mod, ubi, str(itv), str(seg), str(rev), obs))
            st.success("Vehículo creado")
            st.rerun()

# =====================================================
# 💾 BACKUP
# =====================================================
elif menu == "💾 Backup":

    st.title("Backup de datos")

    with open(DB,"rb") as f:
        st.download_button("⬇️ Descargar backup", f, "comasur_backup.db")

    st.markdown("### Restaurar")

    up = st.file_uploader("Subir backup", type=["db"])
    if up:
        with open(DB,"wb") as f:
            f.write(up.getbuffer())
        st.success("Base de datos restaurada")
        st.rerun()
