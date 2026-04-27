import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from PIL import Image
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="COMASUR - Gestión de Flota", page_icon="🚚", layout="wide")
UBICACIONES = ["NAVE ALBOLOTE", "ZAIDIN", "MOTRIL", "MALAGA"]

# --- DISEÑO AVANZADO (CSS CUSTOM) ---
st.markdown("""
    <style>
    /* Importar fuente de Google Fonts (Poppins) para un toque de diseño moderno */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    /* Aplicar la fuente a toda la aplicación */
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif !important;
    }

    /* Fondo principal: Un gris-azulado muy claro y elegante */
    .stApp {
        background-color: #f0f4f8;
    }

    /* Menú lateral (Sidebar): Blanco puro con sombra sutil para separar espacios */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        box-shadow: 4px 0 15px rgba(0, 0, 0, 0.03);
        border-right: 1px solid #e2e8f0;
    }

    /* Títulos de la aplicación */
    h1, h2, h3 {
        color: #0f172a !important; /* Azul marino casi negro */
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    /* Estilo de Tarjetas para Formularios y Cajas de Datos */
    div[data-testid="stForm"], div[data-testid="stExpander"] {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.04);
        border: 1px solid #f1f5f9;
    }

    /* Botones: Diseño Premium con Gradiente y efecto Hover */
    div.stButton > button {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white !important;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        width: 100%;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
    }

    /* Diseño de Pestañas (Tabs) moderno */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        border-bottom: 2px solid #cbd5e1;
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #64748b;
        padding-bottom: 10px;
        height: auto;
    }
    .stTabs [aria-selected="true"] {
        color: #2563eb !important;
        border-bottom: 3px solid #2563eb !important;
    }

    /* Estilo de los indicadores/métricas */
    [data-testid="stMetricValue"] {
        color: #1e3a8a;
        font-weight: 700;
        font-size: 1.8rem;
    }
    [data-testid="stMetricLabel"] {
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.85rem;
    }
    
    /* Alertas y Mensajes de Información */
    div[data-testid="stAlert"] {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
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
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

# --- BARRA LATERAL ---
with st.sidebar:
    try:
        st.image(Image.open("LOGO.png"), use_container_width=True)
    except: 
        st.error("Error: Sube 'LOGO.png' a GitHub")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Menú de Gestión")
    menu = st.radio("", [
        "📋 Estado de la Flota", 
        "➕ Alta de Vehículo", 
        "🔧 Registro Mantenimiento", 
        "💾 Copia de Seguridad"
    ])

# --- MÓDULO 1: ESTADO DE FLOTA ---
if menu == "📋 Estado de la Flota":
    st.title("Inventario de Vehículos")
    st.markdown("Consulta y edita las fichas técnicas de la flota COMASUR.")
    
    with sqlite3.connect(DB_NAME) as conn:
        df_v = pd.read_sql_query("SELECT * FROM vehiculos", conn)

    if not df_v.empty:
        sel_mat = st.selectbox("Selecciona un vehículo para Gestionar/Editar:", ["-- Selecciona Matrícula --"] + df_v['matricula'].tolist())
        st.markdown("<br>", unsafe_allow_html=True)
        
        if sel_mat == "-- Selecciona Matrícula --":
            st.dataframe(df_v[['matricula', 'modelo', 'ubicacion', 'fecha_retirada']], use_container_width=True, hide_index=True)
        else:
            v = df_v[df_v['matricula'] == sel_mat].iloc[0]
            
            tab_ver, tab_editar, tab_historial = st.tabs(["📄 Ficha Técnica", "✏️ Editar Datos", "⏱️ Historial"])
            
            with tab_ver:
                st.markdown(f"### Detalle: {v['matricula']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Modelo", v['modelo'])
                c2.metric("Ubicación", v['ubicacion'])
                c3.metric("Fecha Retirada", v['fecha_retirada'])
                st.info(f"**Características Técnicas:**\n\n{v['caracteristicas']}")
                st.write(f"**Proveedores:** {v['prov_recambios']}")

            with tab_editar:
                with st.form(f"form_edit_{sel_mat}"):
                    st.markdown("### ✏️ Actualizar Información")
                    col_a, col_b = st.columns(2)
                    edit_mod = col_a.text_input("Denominación / Modelo", v['modelo'])
                    edit_ubi = col_a.selectbox("Ubicación Actual", UBICACIONES, index=UBICACIONES.index(v['ubicacion']) if v['ubicacion'] in UBICACIONES else 0)
                    edit_f_r = col_b.text_input("Fecha Retirada (AAAA-MM-DD)", v['fecha_retirada'])
                    edit_manten = col_b.selectbox("Tipo Mantenimiento", ["Interno", "Externo", "Interno/Externo"], index=0)
                    
                    edit_car = st.text_area("Características (Motor, Carga, etc.)", v['caracteristicas'])
                    edit_prv = st.text_input("Proveedores Recambios", v['prov_recambios'])
                    
                    if st.form_submit_button("Guardar Cambios"):
                        execute_db("""UPDATE vehiculos SET modelo=?, ubicacion=?, fecha_retirada=?, tipo_mantenimiento=?, caracteristicas=?, prov_recambios=? 
                                   WHERE matricula=?""", (edit_mod, edit_ubi, edit_f_r, edit_manten, edit_car, edit_prv, sel_mat))
                        st.success("✅ Datos actualizados correctamente.")
                        st.rerun()

            with tab_historial:
                st.markdown(f"### Historial de Intervenciones")
                df_h = pd.read_sql_query(f"SELECT fecha, operacion, responsable, observaciones FROM mantenimientos WHERE matricula='{sel_mat}' ORDER BY fecha DESC", sqlite3.connect(DB_NAME))
                st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.warning("No hay vehículos registrados. Ve a 'Alta de Vehículo'.")

# --- MÓDULO 2: ALTA DE VEHÍCULO ---
elif menu == "➕ Alta de Vehículo":
    st.title("Nueva Ficha de Equipo")
    st.markdown("Rellena los datos para incorporar una nueva unidad a la flota.")
    
    with st.form("alta_vehiculo"):
        c1, c2 = st.columns(2)
        new_mat = c1.text_input("Matrícula (Obligatorio)")
        new_mod = c1.text_input("Denominación / Modelo")
        new_f_c = c1.date_input("Fecha de Compra")
        
        new_ubi = c2.selectbox("Ubicación", UBICACIONES)
        new_f_r = c2.date_input("Fecha Retirada prevista", value=date(2032, 11, 2))
        new_v_u = c2.number_input("Vida útil (años)", value=20)
        
        new_car = st.text_area("Características técnicas")
        new_prv = st.text_input("Proveedores")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Registrar Vehículo"):
            if new_mat and new_mod:
                execute_db("INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?,?)", 
                           (new_mat, new_mod, str(new_f_c), new_v_u, str(new_f_r), new_ubi, "Interno/Externo", new_car, new_prv))
                st.success(f"🎉 Vehículo {new_mat} registrado con éxito.")
            else:
                st.error("Por favor, rellena Matrícula y Modelo.")

# --- MÓDULO 3: REGISTRO MANTENIMIENTO ---
elif menu == "🔧 Registro Mantenimiento":
    st.title("Anotar Nueva Operación")
    st.markdown("Registra las revisiones, ITV y reparaciones de los vehículos.")
    
    with sqlite3.connect(DB_NAME) as conn:
        mats = pd.read_sql_query("SELECT matricula FROM vehiculos", conn)['matricula'].tolist()
    
    if mats:
        with st.form("registro_mant"):
            v_sel = st.selectbox("Seleccionar Vehículo", mats)
            
            c1, c2 = st.columns(2)
            f_op = c1.date_input("Fecha de Operación", value=date.today())
            tipo = c1.selectbox("Tipo de Operación", ["Revisión anual", "ITV", "Reparación Extraordinaria"])
            resp = c2.text_input("Responsable Encargado")
            
            st.markdown("---")
            st.markdown("#### Controles de Seguridad")
            c_seg = st.checkbox("Seguro actualizado")
            c_imp = st.checkbox("Impuestos pagados")
            obs = st.text_area("Observaciones técnicas adicionales")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Guardar Operación"):
                execute_db("""INSERT INTO mantenimientos (matricula, fecha, operacion, responsable, seguro_ok, impuestos_ok, observaciones) 
                           VALUES (?,?,?,?,?,?,?)""", (v_sel, str(f_op), tipo, resp, c_seg, c_imp, obs))
                st.success("✅ Operación guardada correctamente en el historial.")
    else:
        st.error("Primero debes dar de alta un vehículo.")

# --- MÓDULO 4: COPIA DE SEGURIDAD ---
elif menu == "💾 Copia de Seguridad":
    st.title("Gestión de Datos")
    st.info("💡 **Recomendación:** Descarga periódicamente la base de datos a tu ordenador. Si el servidor se reinicia, podrás restaurar todo tu trabajo subiendo el archivo aquí.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 1. Exportar Datos")
        st.write("Guarda una copia de seguridad en tu equipo local.")
        try:
            with open(DB_NAME, "rb") as f:
                db_bytes = f.read()
            st.download_button(
                label="⬇️ Descargar Copia (.db)",
                data=db_bytes,
                file_name=f"comasur_backup_{date.today()}.db",
                mime="application/octet-stream",
                use_container_width=True
            )
        except Exception as e:
            st.error("No se pudo leer la base de datos actual.")

    with col2:
        st.markdown("### 2. Restaurar Datos")
        st.write("Sube una copia anterior para recuperar la información.")
        uploaded_file = st.file_uploader("Selecciona el archivo .db", type=["db"], label_visibility="collapsed")
        
        if uploaded_file is not None:
            st.warning("⚠️ Atención: Esto sobrescribirá todos los datos actuales por los del archivo subido.")
            if st.button("🔄 Ejecutar Restauración", use_container_width=True):
                try:
                    with open(DB_NAME, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success("✅ Base de datos restaurada. Ve a 'Estado de la Flota' para comprobarlo.")
                except Exception as e:
                    st.error("Error al restaurar la base de datos.")
