import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from PIL import Image
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="COMASUR - Gestión de Flota", page_icon="🚚", layout="wide")

# --- ESTILOS CORPORATIVOS (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    h1, h2, h3 { color: #003399 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stButton>button { 
        background-color: #003399; color: white !important; border-radius: 6px; 
        height: 3em; border: 2px solid #003399; font-weight: bold; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #FFCC00; color: #003399 !important; }
    div[data-testid="stAlert"] { border-left: 5px solid #003399; background-color: #E6F0FF; color: #003399; }
    [data-testid="stMetricValue"] { color: #D32F2F; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
DB_NAME = "comasur_flota.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabla de Vehículos actualizada con Tipo de Mantenimiento
    c.execute('''
        CREATE TABLE IF NOT EXISTS vehiculos (
            matricula TEXT PRIMARY KEY,
            modelo TEXT,
            fecha_compra TEXT,
            vida_util INTEGER,
            fecha_retirada TEXT,
            ubicacion TEXT,
            tipo_mantenimiento TEXT,
            caracteristicas TEXT,
            prov_recambios TEXT
        )
    ''')
    # Tabla de Mantenimientos actualizada
    c.execute('''
        CREATE TABLE IF NOT EXISTS mantenimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT,
            fecha TEXT,
            operacion TEXT,
            responsable TEXT,
            seguro_ok BOOLEAN,
            impuestos_ok BOOLEAN,
            observaciones TEXT,
            resp_calidad TEXT,
            FOREIGN KEY(matricula) REFERENCES vehiculos(matricula)
        )
    ''')
    
    # Insertar el vehículo de la plantilla si no existe
    c.execute("SELECT COUNT(*) FROM vehiculos WHERE matricula = '4076 HMS'")
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?,?)
        ''', (
            '4076 HMS', 
            'CITROEN JUMPER FGN 35 LTA', 
            '2012-10-02', 
            20, 
            '2032-11-02', 
            'NAVE', 
            'Interno/Externo',
            'V.Carga (m3)-4’5/2 (carga uhl kg)=1065 p.max 5500, Diesel. Potencia 100/2900 largo nl, alto mm2254, ancho ml2050. Consumo medio (1/100km)=7’3, volumen cargo 4’5/2', 
            '1166-Citroen Rondamovil / 70-Talleres GOE'
        ))
        conn.commit()
    conn.close()

init_db()

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
        logo = Image.open("LOGO.png")
        st.image(logo, use_container_width=True)
    except Exception:
        st.error("Archivo 'LOGO.png' no detectado.")
    
    st.title("Gestión de Flota")
    menu = st.radio("Menú Principal", ["Estado de Flota", "Nuevo Vehículo", "Registrar Mantenimiento"])
    st.divider()
    st.caption("COMASUR - Control de Calidad")

# --- MÓDULO 1: ESTADO DE FLOTA ---
if menu == "Estado de Flota":
    st.header("📊 Panel de Control Vehículos")
    
    df_v = query_db("SELECT * FROM vehiculos")
    if not df_v.empty:
        col_sel, col_descarga = st.columns([3, 1])
        with col_sel:
            sel_mat = st.selectbox("Seleccione matrícula para ver detalle:", ["Ver todos"] + df_v['matricula'].tolist())
        with col_descarga:
            st.write("") # Espaciador
            st.write("")
            # BOTÓN DE EXPORTACIÓN A CSV
            csv = df_v.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Descargar Inventario (CSV)", data=csv, file_name='flota_comasur.csv', mime='text/csv')
        
        if sel_mat == "Ver todos":
            st.dataframe(df_v[['matricula', 'modelo', 'ubicacion', 'tipo_mantenimiento']], use_container_width=True, hide_index=True)
        else:
            v_data = df_v[df_v['matricula'] == sel_mat].iloc[0]
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Matrícula", v_data['matricula'])
            c2.metric("Ubicación", v_data['ubicacion'])
            c3.metric("Vida Útil", f"Hasta {v_data['fecha_retirada']}")
            
            st.write(f"**Tipo de Mantenimiento:** {v_data['tipo_mantenimiento']}")
            st.info(f"**Características Técnicas:** {v_data['caracteristicas']}")
            st.write(f"**Proveedores:** {v_data['prov_recambios']}")

        st.divider()
        st.subheader("🛠️ Historial de Operaciones")
        q_m = "SELECT fecha, operacion, responsable, seguro_ok, impuestos_ok, observaciones, resp_calidad FROM mantenimientos"
        if sel_mat != "Ver todos":
            q_m += f" WHERE matricula = '{sel_mat}'"
        df_m = query_db(q_m + " ORDER BY fecha DESC")
        
        # Mostrar historial y botón de descarga del historial
        st.dataframe(df_m, use_container_width=True, hide_index=True)
        csv_m = df_m.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Descargar Historial Mantenimiento (CSV)", data=csv_m, file_name='historial_mantenimiento.csv', mime='text/csv')

    else:
        st.warning("No hay vehículos registrados en la flota.")

# --- MÓDULO 2: REGISTRO DE VEHÍCULO ---
elif menu == "Nuevo Vehículo":
    st.header("🚚 Alta de Ficha de Equipo/Instalación")
    with st.form("form_v"):
        col1, col2 = st.columns(2)
        with col1:
            mat = st.text_input("Código / Matrícula")
            mod = st.text_input("Denominación del Equipo (Ej: CITROEN JUMPER)")
            f_c = st.date_input("Fecha de Compra", value=date.today())
            tipo_m = st.selectbox("Tipo de Mantenimiento", ["Interno", "Externo", "Interno/Externo"])
        with col2:
            v_u = st.number_input("Vida útil (años)", value=20)
            f_r = st.date_input("Fecha Retirada prevista", value=date(2032, 11, 2))
            ubi = st.selectbox("Ubicación", ["NAVE", "OBRA", "EXTERIOR"])
            prv = st.text_input("Prov. Recambios")
        
        car = st.text_area("Características (V.Carga, Potencia, Consumo, etc.)")
        
        if st.form_submit_button("Guardar Ficha"):
            if mat and mod:
                execute_db("INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?,?)", 
                           (mat, mod, str(f_c), v_u, str(f_r), ubi, tipo_m, car, prv))
                st.success(f"Ficha del equipo {mat} registrada correctamente.")
            else:
                st.error("El Código/Matrícula y la Denominación son obligatorios.")

# --- MÓDULO 3: REGISTRAR MANTENIMIENTO ---
elif menu == "Registrar Mantenimiento":
    st.header("🔧 Operaciones de Mantenimiento a Realizar")
    mats = query_db("SELECT matricula FROM vehiculos")['matricula'].tolist()
    
    if not mats:
        st.error("Registre un vehículo primero.")
    else:
        with st.form("form_m"):
            v_sel = st.selectbox("Código del Equipo", mats)
            
            c1, c2 = st.columns(2)
            with c1:
                op = st.selectbox("Operación", ["Revisión anual (aceite, filtro, niveles..)", "ITV", "Otra Reparación"])
                f_m = st.date_input("Fecha de Operación", value=date.today())
            with c2:
                resp = st.text_input("Responsable Encargado (Ej: Antonio)")
                resp_cal = st.text_input("Responsable Calidad / Medio")
            
            st.subheader("Precauciones y Controles de Seguridad")
            seguro_ok = st.checkbox("Seguro actualizado")
            impuestos_ok = st.checkbox("Imp. Vehículos industriales pagado")
            
            obs = st.text_area("Observaciones Adicionales")
            
            if st.form_submit_button("Firmar y Guardar Operación"):
                if resp:
                    execute_db("""
                        INSERT INTO mantenimientos 
                        (matricula, fecha, operacion, responsable, seguro_ok, impuestos_ok, observaciones, resp_calidad) 
                        VALUES (?,?,?,?,?,?,?,?)
                        """, (v_sel, str(f_m), op, resp, seguro_ok, impuestos_ok, obs, resp_cal))
                    st.success("Operación registrada en el historial correctamente.")
                else:
                    st.error("Debe indicar el nombre del Responsable Encargado.")
