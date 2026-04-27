import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="COMASUR - Gestión de Flota", page_icon="🚚", layout="wide")

# --- ESTILOS CORPORATIVOS (CSS) ---
st.markdown("""
    <style>
    /* Fondo general de la aplicación limpio y profesional */
    .stApp { 
        background-color: #F8F9FA; 
    }
    
    /* Títulos en Azul Corporativo COMASUR */
    h1, h2, h3 { 
        color: #003399 !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Diseño de los Botones: Azul corporativo que cambia a Amarillo al pasar el ratón */
    .stButton>button { 
        background-color: #003399; 
        color: white !important; 
        border-radius: 6px; 
        height: 3em; 
        border: 2px solid #003399;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #FFCC00; /* Amarillo COMASUR */
        color: #003399 !important;
        border: 2px solid #003399;
    }
    
    /* Cajas de Información (st.info y st.warning) */
    div[data-testid="stAlert"] {
        border-left: 5px solid #003399;
        background-color: #E6F0FF;
        color: #003399;
    }
    
    /* Valores numéricos y Métricas en Rojo Acento (del símbolo $ del logo) */
    [data-testid="stMetricValue"] {
        color: #D32F2F; 
    }
    
    /* Tarjetas de Dataframes con bordes suaves */
    .stDataFrame { 
        background-color: white; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
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
        # Se carga LOGO.png
        logo = Image.open("LOGO.png")
        st.image(logo, use_container_width=True)
    except Exception as e:
        st.error("Archivo 'LOGO.png' no detectado.")
    
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
            
            # Uso de columnas para mostrar métricas destacadas
            c1, c2, c3 = st.columns(3)
            c1.metric("Matrícula", v_data['matricula'])
            c2.metric("Ubicación", v_data['ubicacion'])
            c3.metric("Vida Útil hasta", v_data['fecha_retirada'][:4])
            
            st.info(f"**Detalles Técnicos:** {v_data['caracteristicas']}")
            st.write(f"**Proveedores:** {v_data['prov_recambios']}")

        st.divider()
        st.subheader("🛠️ Historial de Intervenciones")
        q_m = "SELECT fecha, operacion, responsable, observaciones FROM mantenimientos"
        if sel_mat != "Ver todos":
            q_m += f" WHERE matricula = '{sel_mat}'"
        df_m = query_db(q_m + " ORDER BY fecha DESC")
        st.table(df_m)
    else:
        st.warning("No hay vehículos registrados en la flota.")

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
        
        car = st.text_area("Características Técnicas (Carga, Motor, Consumo)")
        prv = st.text_input("Proveedores habituales")
        
        if st.form_submit_button("Guardar Vehículo"):
            if mat and mod:
                execute_db("INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?)", 
                           (mat, mod, str(f_c), v_u, str(f_r), ubi, car, prv))
                st.success(f"Vehículo {mat} registrado correctamente.")
                st.rerun()
            else:
                st.error("La Matrícula y el Modelo son campos obligatorios.")

# --- MÓDULO 3: REGISTRAR MANTENIMIENTO ---
elif menu == "Registrar Mantenimiento":
    st.header("🔧 Registro de Mantenimiento / ITV")
    mats = query_db("SELECT matricula FROM vehiculos")['matricula'].tolist()
    
    if not mats:
        st.error("Registre un vehículo primero en el módulo 'Nuevo Vehículo'.")
    else:
        with st.form("form_m"):
            v_sel = st.selectbox("Matrícula de la Unidad", mats)
            f_m = st.date_input("Fecha de la Intervención", value=date.today())
            op = st.selectbox("Operación Realizada", ["Revisión anual", "ITV", "Reparación", "Control de Seguridad"])
            resp = st.text_input("Responsable (Ej: Antonio)")
            obs = st.text_area("Observaciones (Ej: Seguro actualizado, Imp. Vehículos pagado, filtros...)")
            
            if st.form_submit_button("Anotar Intervención"):
                if resp:
                    execute_db("INSERT INTO mantenimientos (matricula, fecha, operacion, responsable, observaciones) VALUES (?,?,?,?,?)",
                               (v_sel, str(f_m), op, resp, obs))
                    st.success("Registro de mantenimiento guardado con éxito.")
                else:
                    st.error("Debe indicar el nombre del Responsable de la operación.")
