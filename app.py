import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Mis Medicamentos", layout="centered")

# Estilos CSS personalizados para maximizar legibilidad y tamaño de botones
st.markdown("""
    <style>
    /* Tamaño de fuente global y botones */
    html, body, [class*="st-"] {
        font-size: 24px !important;
    }
    
    .stButton button {
        height: 4em !important;
        width: 100% !important;
        font-size: 26px !important;
        font-weight: bold !important;
        border-radius: 15px !important;
        margin-top: 10px !important;
        margin-bottom: 10px !important;
        border: 2px solid #2e2e2e !important;
    }

    /* Títulos grandes */
    h1 {
        font-size: 50px !important;
        text-align: center;
        color: #1a1a1a;
    }

    /* Estilo de las tarjetas de medicamentos */
    .med-card {
        padding: 25px;
        border-radius: 20px;
        background-color: #f9f9f9;
        border: 1px solid #ddd;
        margin-bottom: 10px;
    }
    
    /* Input más grande */
    input {
        font-size: 22px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar el estado de la aplicación
if 'medicamentos' not in st.session_state:
    st.session_state.medicamentos = [
        {'nombre': 'Paracetamol', 'dosis': 'Mañana', 'cantidad': 12},
        {'nombre': 'Aspirina', 'dosis': 'Noche', 'cantidad': 5}
    ]

if 'mostrar_formulario' not in st.session_state:
    st.session_state.mostrar_formulario = False

# TÍTULO PRINCIPAL
st.write("# 💊 Mis medicamentos")

# BOTÓN AÑADIR (Alterna la visibilidad del formulario)
if st.button("➕ Añadir medicamento"):
    st.session_state.mostrar_formulario = not st.session_state.mostrar_formulario

# Formulario simple para añadir (solo aparece al pulsar el botón)
if st.session_state.mostrar_formulario:
    with st.container():
        nuevo_nombre = st.text_input("Nombre del medicamento:", placeholder="Ej: Ibuprofeno")
        nueva_dosis = st.selectbox("¿Cuándo se toma?", ["Mañana", "Tarde", "Noche", "Cada 8 horas"])
        nueva_cant = st.number_input("¿Cuántas pastillas tiene?", min_value=1, value=10)
        
        if st.button("💾 GUARDAR"):
            if nuevo_nombre:
                st.session_state.medicamentos.append({
                    'nombre': nuevo_nombre,
                    'dosis': nueva_dosis,
                    'cantidad': nueva_cant
                })
                st.session_state.mostrar_formulario = False
                st.rerun()

st.markdown("---")

# LISTA DE MEDICAMENTOS
if not st.session_state.medicamentos:
    st.write("No hay medicamentos en la lista.")
else:
    for i, med in enumerate(st.session_state.medicamentos):
        # Contenedor visual tipo tarjeta
        with st.container():
            # Título y detalles
            st.markdown(f"## **{med['nombre']}**")
            st.write(f"🕒 Dosis: **{med['dosis']}**")
            st.write(f"📦 Quedan: **{med['cantidad']}** pastillas")
            
            # Botones de acción
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"✔️ Tomado", key=f"tomar_{i}"):
                    if st.session_state.medicamentos[i]['cantidad'] > 0:
                        st.session_state.medicamentos[i]['cantidad'] -= 1
                        st.rerun()
            
            with col2:
                if st.button(f"🛒 Comprar", key=f"comprar_{i}"):
                    # Añade un paquete estándar de 10 o 20
                    st.session_state.medicamentos[i]['cantidad'] += 20
                    st.rerun()
            
            # Separador visual entre tarjetas
            st.markdown("---")

# Botón extra al final para limpiar todo (opcional para pruebas)
if st.checkbox("Mostrar opciones de borrado"):
    if st.button("🗑️ Borrar toda la lista"):
        st.session_state.medicamentos = []
        st.rerun()
