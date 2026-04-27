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
    .stDataFrame { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
DB_NAME = "comasur_flota.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabla de Vehículos con campos de la ficha técnica
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
    
    # Insertar vehículo inicial (Citroen Jumper 4076 HMS) si no existe
    c.execute("SELECT COUNT(*) FROM vehiculos WHERE matricula = '4076 HMS'")
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO vehiculos (matricula, modelo, fecha_compra, vida_util, fecha_retirada, ubicacion, caracteristicas, prov_recambios)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

# --- FUNCIONES DE AYUDA ---
def query_db(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_db(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    try:
        # Buscamos el archivo LOGO.png que subiste
        logo = Image.open("LOGO.png")
        st.image(logo, use_container_width=True)
    except:
        st.error("Archivo 'LOGO.png' no encontrado.")
    
    st.title("Gestión de Flota")
    menu = st.radio("Navegación", ["Panel de Control", "Registro de Vehículo", "Anotar Mantenimiento"])
    st.info("Empresa: VEHICULOS COMASUR\nResponsable de Calidad: Antonio")

# --- MÓDULO 1: PANEL DE CONTROL ---
if menu == "Panel de Control":
    st.header("📊 Estado General de la Flota")
    
    # Filtro por matrícula
    vehiculos_list = query_db("SELECT matricula FROM vehiculos")['matricula'].tolist()
    sel_vehiculo = st.selectbox("Seleccione un vehículo para ver detalles:", ["Todos"] + vehiculos_list)
    
    if sel_vehiculo == "Todos":
        df_v = query_db("SELECT matricula, modelo, ubicacion, fecha_retirada FROM vehiculos")
        st.subheader("Listado de Unidades")
        st.dataframe(df_v, use_container_width=True, hide_index=True)
    else:
        # Ficha detallada del vehículo
        detalles = query_db("SELECT * FROM vehiculos WHERE matricula = ?", (sel_vehiculo,)).iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Matrícula", detalles['matricula'])
            st.write(f"**Modelo:** {detalles['modelo']}")
            st.write(f"**Ubicación:** {detalles['ubicacion']}")
        with col2:
            st.write(f"**Vida útil:** {detalles['vida_util']} años")
            st.write(f"**Fecha Retirada:** {detalles['fecha_retirada']}")
            st.write(f"**Recambios:** {detalles['prov_recambios']}")
        
        st.info(f"**Características Técnicas:** {detalles['caracteristicas']}")

    st.divider()
    st.subheader("🛠️ Historial Reciente de Mantenimiento e ITV")
    query_m = "SELECT matricula, fecha, operacion, responsable, observaciones FROM mantenimientos"
    if sel_vehiculo != "Todos":
        query_m += f" WHERE matricula = '{sel_vehiculo}'"
    df_m = query_db(query_m + " ORDER BY fecha DESC")
    st.dataframe(df_m, use_container_width=True, hide_index=True)

# --- MÓDULO 2: REGISTRO DE VEHÍCULO ---
elif menu == "Registro de Vehículo":
    st.header("📝 Alta de nueva unidad en COMASUR")
    with st.form("nuevo_v"):
        c1, c2 = st.columns(2)
        with c1:
            mat = st.text_input("Matrícula / Código")
            mod = st.text_input("Denominación (Ej: CITROEN JUMPER)")
            f_compra = st.date_input("Fecha de Compra")
        with c2:
            v_util = st.number_input("Vida útil (Años)", value=20)
            f_ret = st.date_input("Fecha prevista de retirada")
            ubica = st.selectbox("Ubicación", ["NAVE", "EXTERIOR", "CLIENTE"])
        
        caract = st.text_area("Características (Motor, Carga, Consumo)")
        provs = st.text_input("Proveedores de Recambios habituales")
        
        if st.form_submit_button("Guardar Vehículo"):
            execute_db('''
                INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?)
            ''', (mat, mod, str(f_compra), v_util, str(f_ret), ubica, caract, provs))
            st.success("Vehículo registrado correctamente.")

# --- MÓDULO 3: ANOTAR MANTENIMIENTO ---
elif menu == "Anotar Mantenimiento":
    st.header("🔧 Registro de Intervenciones Técnicas")
    v_list = query_db("SELECT matricula FROM vehiculos")['matricula'].tolist()
    
    if not v_list:
        st.warning("Debe registrar un vehículo primero.")
    else:
        with st.form("nuevo_m"):
            v_sel = st.selectbox("Vehículo", v_list)
            f_op = st.date_input("Fecha de operación")
            tipo_op = st.selectbox("Tipo de Operación", ["Revisión anual", "ITV", "Reparación", "Seguro/Impuestos"])
            resp = st.text_input("Responsable (Ej: Antonio)")
            obs = st.text_area("Observaciones (Ej: Seguro pagado, filtros cambiados)")
            
            if st.form_submit_button("Registrar Operación"):
                execute_db('''
                    INSERT INTO mantenimientos (matricula, fecha, operacion, responsable, observaciones)
                    VALUES (?,?,?,?,?)
                ''', (v_sel, str(f_op), tipo_op, resp, obs))
                st.success("Operación guardada en el historial.")
