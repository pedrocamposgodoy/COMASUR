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

div[data-testid="stDataFrame"] {
    background-color: white;
    border-radius: 12px;
    padding: 10px;
    border: 1px solid #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

# --- DB ---
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

def get_df(q):
    return pd.read_sql(q, sqlite3.connect(DB))

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

    if not df.empty:
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

    # --- TABLA GASTOS ---
    st.markdown("---")
    st.markdown("## 💸 Gastos del año")

    year = datetime.today().year

    df_gastos = get_df(f"""
        SELECT m.fecha, m.matricula, v.marca, v.modelo, m.concepto, m.coste
        FROM mantenimientos m
        LEFT JOIN vehiculos v ON m.matricula = v.matricula
        WHERE substr(m.fecha,1,4) = '{year}'
        ORDER BY m.fecha DESC
    """)

    if not df_gastos.empty:
        st.metric("Total anual", f"{df_gastos['coste'].sum():.2f} €")

        df_gastos.columns = ["Fecha","Matrícula","Marca","Modelo","Concepto","Coste (€)"]

        st.dataframe(df_gastos, use_container_width=True, hide_index=True)
    else:
        st.info("Sin gastos este año")

# =====================================================
# FICHA VEHÍCULO
# =====================================================
elif st.session_state.vehiculo_sel:

    mat = st.session_state.vehiculo_sel
    df = get_df(f"SELECT * FROM vehiculos WHERE matricula='{mat}'")
    v = df.iloc[0]

    st.title(f"🚐 {mat}")

    if st.button("⬅️ Volver"):
        st.session_state.vehiculo_sel = None
        st.rerun()

    # --- DATOS ---
    with st.form("edit"):
        marca = st.text_input("Marca", v.get("marca",""))
        modelo = st.text_input("Modelo", v["modelo"])
        ubicacion = st.selectbox("Ubicación", UBICACIONES, index=UBICACIONES.index(v["ubicacion"]))

        itv = st.date_input("ITV", datetime.fromisoformat(v["fecha_itv"]) if v["fecha_itv"] else date.today())
        seguro = st.date_input("Seguro", datetime.fromisoformat(v["fecha_seguro"]) if v["fecha_seguro"] else date.today())
        revision = st.date_input("Revisión")

        obs = st.text_area("Observaciones", v["observaciones"])

        if st.form_submit_button("Guardar"):
            run("""
            UPDATE vehiculos SET marca=?, modelo=?, ubicacion=?, fecha_itv=?, fecha_seguro=?, fecha_revision=?, observaciones=? 
            WHERE matricula=?""",
            (marca, modelo, ubicacion, str(itv), str(seguro), str(revision), obs, mat))
            st.rerun()

    # =====================================================
    # 🔧 MANTENIMIENTO (AQUÍ ESTÁ LO QUE FALTABA)
    # =====================================================
    st.markdown("## 🔧 Añadir mantenimiento")

    with st.form("nuevo_mant"):
        fecha = st.date_input("Fecha", value=date.today())
        concepto = st.text_input("Concepto")
        coste = st.number_input("Coste", 0.0)
        file = st.file_uploader("Factura (PDF)")

        data = file.getvalue() if file else None
        name = file.name if file else None

        if st.form_submit_button("Añadir mantenimiento"):
            run(
                "INSERT INTO mantenimientos (matricula,fecha,concepto,coste,factura,nombre_factura) VALUES (?,?,?,?,?,?)",
                (mat, str(fecha), concepto, coste, data, name)
            )
            st.success("Mantenimiento añadido")
            st.rerun()

    # --- HISTORIAL ---
    st.markdown("## 📋 Historial")

    df_m = get_df(f"SELECT * FROM mantenimientos WHERE matricula='{mat}' ORDER BY fecha DESC")

    if not df_m.empty:
        for _, row in df_m.iterrows():

            with st.expander(f"{row['fecha']} - {row['concepto']}"):

                with st.form(f"edit_{row['id']}"):
                    concepto = st.text_input("Concepto", row["concepto"])
                    coste = st.number_input("Coste", value=float(row["coste"]))

                    if row["factura"]:
                        st.download_button("📄 Ver factura", row["factura"], row["nombre_factura"])

                    c1, c2 = st.columns(2)

                    if c1.form_submit_button("Guardar"):
                        run("UPDATE mantenimientos SET concepto=?, coste=? WHERE id=?",
                            (concepto, coste, row["id"]))
                        st.rerun()

                    if c2.form_submit_button("Borrar"):
                        run("DELETE FROM mantenimientos WHERE id=?", (row["id"],))
                        st.rerun()

        st.metric("Total vehículo", f"{df_m['coste'].sum():.2f} €")
    else:
        st.info("Sin mantenimientos")

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
