import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from PIL import Image

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="COMASUR - Gestión de Flota", page_icon="🚚", layout="wide")
UBICACIONES = ["NAVE ALBOLOTE", "ZAIDIN", "MOTRIL", "MALAGA"]

# --- ESTILOS CORPORATIVOS ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    h1, h2, h3 { color: #003399 !important; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { 
        background-color: #003399; color: white !important; border-radius: 6px; 
        font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background-color: #FFCC00; color: #003399 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #f0f2f6;
        border-radius: 5px 5px 0px 0px; gap: 1px; padding: 10px;
    }
    .stTabs [aria-selected="true"] { background-color: #003399; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
DB_NAME = "comasur_flota.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vehiculos (
        matricula TEXT PRIMARY KEY, modelo TEXT, fecha_compra TEXT, vida_util INTEGER, 
        fecha_retirada TEXT, ubicacion TEXT, tipo_mantenimiento TEXT, 
        caracteristicas TEXT, prov_recambios TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mantenimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, matricula TEXT, fecha TEXT, operacion TEXT, 
        responsable TEXT, seguro_ok BOOLEAN, impuestos_ok BOOLEAN, observaciones TEXT, resp_calidad TEXT)''')
    
    # Carga inicial del vehículo 4076 HMS si la tabla está vacía
    c.execute("SELECT COUNT(*) FROM vehiculos WHERE matricula = '4076 HMS'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?,?)", 
                 ('4076 HMS', 'CITROEN JUMPER FGN 35 LTA', '2012-10-02', 20, '2032-11-02', 
                  'NAVE ALBOLOTE', 'Interno/Externo', 'V.Carga (m3)-4’5/2 (carga uhl kg)=1065 p.max 5500, Diesel. Potencia 100/2900', 'Citroen Rondamovil'))
    conn.commit()
    conn.close()

init_db()

def execute_db(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor(); c.execute(query, params); conn.commit()

# --- BARRA LATERAL ---
with st.sidebar:
    try:
        st.image(Image.open("LOGO.png"), use_container_width=True)
    except: st.error("Error: Sube 'LOGO.png' a GitHub")
    st.title("Sistema COMASUR")
    menu = st.radio("Secciones:", ["📋 Estado de Flota", "➕ Alta de Vehículo", "🔧 Registro Mantenimiento"])

# --- LÓGICA PRINCIPAL ---
if menu == "📋 Estado de Flota":
    st.header("📊 Inventario de Vehículos")
    with sqlite3.connect(DB_NAME) as conn:
        df_v = pd.read_sql_query("SELECT * FROM vehiculos", conn)

    if not df_v.empty:
        # Selección de Vehículo
        sel_mat = st.selectbox("👉 Selecciona un vehículo para Gestionar/Editar:", ["-- Selecciona Matrícula --"] + df_v['matricula'].tolist())
        
        if sel_mat == "-- Selecciona Matrícula --":
            st.write("### Resumen Global")
            st.dataframe(df_v[['matricula', 'modelo', 'ubicacion', 'fecha_retirada']], use_container_width=True, hide_index=True)
        else:
            v = df_v[df_v['matricula'] == sel_mat].iloc[0]
            
            # PESTAÑAS PARA ORGANIZAR LA FICHA
            tab_ver, tab_editar, tab_historial = st.tabs(["👁️ Ver Ficha", "✏️ EDITAR FICHA", "📜 Historial Mantenimiento"])
            
            with tab_ver:
                st.subheader(f"Ficha Técnica: {v['matricula']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Modelo", v['modelo'])
                c2.metric("Ubicación", v['ubicacion'])
                c3.metric("Fecha Retirada", v['fecha_retirada'])
                st.info(f"**Características Técnicas:**\n{v['caracteristicas']}")
                st.write(f"**Proveedores:** {v['prov_recambios']}")

            with tab_editar:
                st.subheader(f"Modificar datos de {sel_mat}")
                with st.form(f"form_edit_{sel_mat}"):
                    col_a, col_b = st.columns(2)
                    edit_mod = col_a.text_input("Denominación / Modelo", v['modelo'])
                    edit_ubi = col_a.selectbox("Ubicación Actual", UBICACIONES, index=UBICACIONES.index(v['ubicacion']) if v['ubicacion'] in UBICACIONES else 0)
                    edit_f_r = col_b.text_input("Fecha Retirada (AAAA-MM-DD)", v['fecha_retirada'])
                    edit_manten = col_b.selectbox("Tipo Mantenimiento", ["Interno", "Externo", "Interno/Externo"], index=0)
                    
                    edit_car = st.text_area("Características (Motor, Carga, etc.)", v['caracteristicas'])
                    edit_prv = st.text_input("Proveedores Recambios", v['prov_recambios'])
                    
                    if st.form_submit_button("💾 GUARDAR CAMBIOS EN LA FICHA"):
                        execute_db("""UPDATE vehiculos SET modelo=?, ubicacion=?, fecha_retirada=?, tipo_mantenimiento=?, caracteristicas=?, prov_recambios=? 
                                   WHERE matricula=?""", (edit_mod, edit_ubi, edit_f_r, edit_manten, edit_car, edit_prv, sel_mat))
                        st.success("✅ Datos actualizados. La página se recargará.")
                        st.rerun()

            with tab_historial:
                st.subheader(f"Intervenciones realizadas en {sel_mat}")
                df_h = pd.read_sql_query(f"SELECT fecha, operacion, responsable, observaciones FROM mantenimientos WHERE matricula='{sel_mat}' ORDER BY fecha DESC", sqlite3.connect(DB_NAME))
                st.table(df_h)
    else:
        st.warning("No hay vehículos registrados. Ve a 'Alta de Vehículo'.")

elif menu == "➕ Alta de Vehículo":
    st.header("🚚 Nueva Ficha de Equipo")
    with st.form("alta_vehiculo"):
        c1, c2 = st.columns(2)
        new_mat = c1.text_input("Matrícula (Obligatorio)")
        new_mod = c1.text_input("Denominación / Modelo")
        new_f_c = c1.date_input("Fecha de Compra")
        
        new_ubi = c2.selectbox("Ubicación", UBICACIONES)
        new_f_r = c2.date_input("Fecha Retirada prevista", value=date(2032, 11, 2))
        new_v_u = c2.number_input("Vida útil (años)", value=20)
        
        new_car = st.text_area("Características técnicas (según Word)")
        new_prv = st.text_input("Proveedores (Rondamovil, GOE...)")
        
        if st.form_submit_button("📥 REGISTRAR NUEVA FICHA"):
            if new_mat and new_mod:
                execute_db("INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?,?)", 
                           (new_mat, new_mod, str(new_f_c), new_v_u, str(new_f_r), new_ubi, "Interno/Externo", new_car, new_prv))
                st.success(f"Vehículo {new_mat} registrado con éxito.")
            else:
                st.error("Por favor, rellena Matrícula y Modelo.")

elif menu == "🔧 Registro Mantenimiento":
    st.header("🔧 Anotar Nueva Operación")
    with sqlite3.connect(DB_NAME) as conn:
        mats = pd.read_sql_query("SELECT matricula FROM vehiculos", conn)['matricula'].tolist()
    
    if mats:
        with st.form("registro_mant"):
            v_sel = st.selectbox("Seleccionar Vehículo", mats)
            f_op = st.date_input("Fecha hoy", value=date.today())
            tipo = st.selectbox("Tipo de Operación", ["Revisión anual", "ITV", "Reparación Extraordinaria"])
            resp = st.text_input("Responsable Encargado (Antonio...)")
            
            st.markdown("### 🛡️ Controles de Seguridad")
            c_seg = st.checkbox("Seguro actualizado")
            c_imp = st.checkbox("Impuestos pagados")
            obs = st.text_area("Observaciones técnicas")
            
            if st.form_submit_button("📝 FIRMAR Y GUARDAR"):
                execute_db("""INSERT INTO mantenimientos (matricula, fecha, operacion, responsable, seguro_ok, impuestos_ok, observaciones) 
                           VALUES (?,?,?,?,?,?,?)""", (v_sel, str(f_op), tipo, resp, c_seg, c_imp, obs))
                st.success("Operación guardada en el historial.")
    else:
        st.error("Primero debes dar de alta un vehículo en la sección 'Alta de Vehículo'.")
