import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime

# --- CONFIG ---
st.set_page_config(page_title="COMASUR Fleet Manager", layout="wide")

DB_NAME = "comasur_flota.db"
UBICACIONES = ["NAVE ALBOLOTE", "ZAIDIN", "MOTRIL", "MALAGA"]

# --- ESTILO ---
st.markdown("""
<style>
.stApp {background: linear-gradient(180deg,#e6edf5,#dbe7f3);}
div[data-testid="stDataEditor"] {
    border-radius: 10px;
    border: 1px solid #cbd5e1;
}
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

def execute(q, p=()):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(q, p)
        conn.commit()

# --- ESTADO ---
def estado(fecha):
    if not fecha:
        return "🟢 OK"
    diff = (datetime.fromisoformat(str(fecha)) - datetime.today()).days
    if diff < 0: return "🔴 Crítico"
    if diff < 30: return "🟡 Revisar"
    return "🟢 OK"

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("LOGO.png", use_container_width=True)
    except:
        st.write("Sube LOGO.png")

    menu = st.radio("", ["📋 Flota","➕ Vehículo","🔧 Mantenimiento","💾 Backup"])

# --- HEADER ---
st.title("🚛 COMASUR Fleet Manager")

# --- FLOTA ---
if menu == "📋 Flota":

    df = pd.read_sql("SELECT * FROM vehiculos", sqlite3.connect(DB_NAME))

    # ALERTAS
    alertas = []
    for _, v in df.iterrows():
        for campo in ["fecha_itv","fecha_seguro","fecha_revision"]:
            if estado(v[campo]) != "🟢 OK":
                alertas.append(f"{campo.replace('fecha_','').upper()} {v['matricula']}")

    if alertas:
        st.warning("🔔 " + " | ".join(alertas))

    if not df.empty:

        # --- TABLA EDITABLE ---
        st.markdown("### ✏️ Editar flota")

        df_edit = df[[
            "matricula",
            "modelo",
            "ubicacion",
            "fecha_itv",
            "fecha_seguro",
            "fecha_revision",
            "observaciones"
        ]].copy()

        edited_df = st.data_editor(
            df_edit,
            use_container_width=True,
            num_rows="dynamic",
            key="editor"
        )

        if st.button("💾 Guardar cambios"):
            for _, row in edited_df.iterrows():
                execute("""
                UPDATE vehiculos SET 
                modelo=?, ubicacion=?, fecha_itv=?, fecha_seguro=?, fecha_revision=?, observaciones=? 
                WHERE matricula=?""",
                (
                    row["modelo"],
                    row["ubicacion"],
                    str(row["fecha_itv"]),
                    str(row["fecha_seguro"]),
                    str(row["fecha_revision"]),
                    row["observaciones"],
                    row["matricula"]
                ))

            st.success("Cambios guardados")
            st.rerun()

        # --- ESTADO VISUAL ---
        st.markdown("### 🚦 Estado de la flota")

        df_estado = pd.DataFrame({
            "Matrícula": df["matricula"],
            "ITV": df["fecha_itv"].apply(estado),
            "Seguro": df["fecha_seguro"].apply(estado),
            "Revisión": df["fecha_revision"].apply(estado)
        })

        st.dataframe(df_estado, use_container_width=True)

        # --- HISTORIAL ---
        sel = st.selectbox("Seleccionar vehículo", df["matricula"])

        df_m = pd.read_sql(
            f"SELECT * FROM mantenimientos WHERE matricula='{sel}'",
            sqlite3.connect(DB_NAME)
        )

        st.markdown("### 📋 Historial")

        if not df_m.empty:
            for _, row in df_m.iterrows():
                c1,c2,c3,c4 = st.columns([2,3,2,2])
                c1.write(row["fecha"])
                c2.write(row["concepto"])
                c3.write(f"{row['coste']} €")

                if row["factura"]:
                    c4.download_button("📄 Factura", row["factura"], row["nombre_factura"])
                else:
                    c4.write("—")

            st.metric("💸 Total vehículo", f"{df_m['coste'].sum():.2f} €")

        else:
            st.info("Sin mantenimientos")

    else:
        st.warning("No hay vehículos")

# --- NUEVO VEHÍCULO ---
elif menu == "➕ Vehículo":

    with st.form("alta"):
        mat = st.text_input("Matrícula")
        mod = st.text_input("Modelo")
        ubi = st.selectbox("Ubicación", UBICACIONES)
        itv = st.date_input("ITV")
        seg = st.date_input("Seguro")
        rev = st.date_input("Próxima revisión")
        obs = st.text_area("Observaciones")

        if st.form_submit_button("Crear"):
            execute(
                "INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?)",
                (mat, mod, ubi, str(itv), str(seg), str(rev), obs)
            )
            st.success("Vehículo creado")
            st.rerun()

# --- MANTENIMIENTO ---
elif menu == "🔧 Mantenimiento":

    mats = pd.read_sql("SELECT matricula FROM vehiculos", sqlite3.connect(DB_NAME))["matricula"]

    if len(mats) > 0:

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
                execute(
                    "INSERT INTO mantenimientos (matricula,fecha,concepto,coste,factura,nombre_factura) VALUES (?,?,?,?,?,?)",
                    (v, str(date.today()), concepto, coste, data, name)
                )
                st.success("Guardado")
                st.rerun()

    else:
        st.warning("Primero crea un vehículo")

# --- BACKUP ---
elif menu == "💾 Backup":

    with open(DB_NAME,"rb") as f:
        st.download_button("⬇️ Descargar backup", f, "comasur_backup.db")
