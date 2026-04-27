import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="COMASUR - Gestión de Flota", page_icon="🚚", layout="wide")

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #003399; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
DB_NAME = "comasur_flota.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabla de Vehículos
    c.execute('''
        CREATE TABLE IF NOT EXISTS vehiculos (
            matricula TEXT PRIMARY KEY,
            modelo TEXT,
            fecha_compra TEXT,
            vida_util INTEGER,
            fecha_retirada TEXT,
            ubicacion TEXT,
            caracteristicas TEXT,
            prov_recambios TEXT
        )
    ''')
    # Tabla de Mantenimientos
    c.execute('''
        CREATE TABLE IF NOT EXISTS mantenimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT,
            fecha TEXT,
            operacion TEXT,
            responsable TEXT,
            observaciones TEXT,
            FOREIGN KEY(matricula) REFERENCES vehiculos(matricula)
        )
    ''')
    
    # Datos iniciales según ficha técnica (4076 HMS)
    c.execute("SELECT COUNT(*) FROM vehiculos WHERE matricula = '4076 HMS'")
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?)
        ''', (
            '4076 HMS', 
            'CITROEN JUMPER FGN 35 LTA', 
            '2012-10-02', 
            20, 
            '2032-11-02', 
            'NAVE', 
            'Diesel. Potencia 100/2900. Carga 1065kg. Consumo 7.3L/100km', 
            '1166-Citroen Rondamovil / 70-Talleres GOE'
        ))
        conn.commit()
    conn.close()

init_db()

# --- FUNCIONES DE BASE DE DATOS ---
def query_db(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(query, conn, params=params)

def execute_db(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    try:
        # Se intenta cargar LOGO.png con el nuevo parámetro de compatibilidad
        logo = Image.open("LOGO.png")
        st.image(logo, use_container_width=True)
    except Exception as e:
        st.error("Archivo 'LOGO.png' no detectado en el repositorio.")
    
    st.title("Gestión de Flota")
    menu = st.radio("Menú Principal", ["Estado de Flota", "Nuevo Vehículo", "Registrar Mantenimiento"])
    st.divider()
    st.caption("COMASUR - Control de Calidad y Mantenimiento")

# --- MÓDULO 1: ESTADO DE FLOTA ---
if menu == "Estado de Flota":
    st.header("📊 Panel de Control Vehículos")
    
    df_v = query_db("SELECT * FROM vehiculos")
    if not df_v.empty:
        sel_mat = st.selectbox("Seleccione matrícula para ver detalle:", ["Ver todos"] + df_v['matricula'].tolist())
        
        if sel_mat == "Ver todos":
            st.dataframe(df_v[['matricula', 'modelo', 'ubicacion', 'fecha_retirada']], use_container_width=True, hide_index=True)
        else:
            v_data = df_v[df_v['matricula'] == sel_mat].iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Matrícula", v_data['matricula'])
            c2.metric("Ubicación", v_data['ubicacion'])
            c3.metric("Vida Útil hasta", v_data['fecha_retirada'][:4])
            
            st.info(f"**Detalles Técnicos:** {v_data['caracteristicas']}")
            st.write(f"**Proveedores:** {v_data['prov_recambios']}")

        st.subheader("🛠️ Historial de Intervenciones")
        q_m = "SELECT fecha, operacion, responsable, observaciones FROM mantenimientos"
        if sel_mat != "Ver todos":
            q_m += f" WHERE matricula = '{sel_mat}'"
        df_m = query_db(q_m + " ORDER BY fecha DESC")
        st.table(df_m)
    else:
        st.warning("No hay vehículos registrados.")

# --- MÓDULO 2: REGISTRO DE VEHÍCULO ---
elif menu == "Nuevo Vehículo":
    st.header("🚚 Alta de Unidad")
    with st.form("form_v"):
        col1, col2 = st.columns(2)
        with col1:
            mat = st.text_input("Matrícula")
            mod = st.text_input("Modelo (Ej: Citroen Jumper)")
            f_c = st.date_input("Fecha de Compra", value=date.today())
        with col2:
            v_u = st.number_input("Vida útil (años)", value=20)
            f_r = st.date_input("Fecha Retirada", value=date(2032, 11, 2))
            ubi = st.selectbox("Ubicación", ["NAVE", "OBRA", "EXTERIOR"])
        
        car = st.text_area("Características (Carga, Motor, Consumo)")
        prv = st.text_input("Proveedores habituales")
        
        if st.form_submit_button("Guardar Vehículo"):
            if mat and mod:
                execute_db("INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?)", 
                           (mat, mod, str(f_c), v_u, str(f_r), ubi, car, prv))
                st.success("Vehículo registrado.")
                st.rerun()

# --- MÓDULO 3: REGISTRAR MANTENIMIENTO ---
elif menu == "Registrar Mantenimiento":
    st.header("🔧 Registro de Mantenimiento / ITV")
    mats = query_db("SELECT matricula FROM vehiculos")['matricula'].tolist()
    
    if not mats:
        st.error("Registre un vehículo primero.")
    else:
        with st.form("form_m"):
            v_sel = st.selectbox("Matrícula", mats)
            f_m = st.date_input("Fecha", value=date.today())
            op = st.selectbox("Operación", ["Revisión anual", "ITV", "Reparación", "Control de Seguridad"])
            resp = st.text_input("Responsable (Ej: Antonio)")
            obs = st.text_area("Observaciones (Seguro, Impuestos, filtros...)")
            
            if st.form_submit_button("Anotar"):
                execute_db("INSERT INTO mantenimientos (matricula, fecha, operacion, responsable, observaciones) VALUES (?,?,?,?,?)",
                           (v_sel, str(f_m), op, resp, obs))
                st.success("Registro guardado.")
