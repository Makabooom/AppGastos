import streamlit as st
import pandas as pd
import datetime
from google_sheets import connect_to_sheet, read_sheet_as_df, write_df_to_sheet

# === Banner ===
st.image("banner_makaboom.png", use_container_width=True)

# === Mostrar mes/año actual y botón para avanzar ===
today = datetime.date.today()
mes = st.session_state.get("mes_actual", today.month)
año = st.session_state.get("año_actual", today.year)

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    st.markdown(f"### Mes actual: {mes}")
with col2:
    st.markdown(f"### Año actual: {año}")
with col3:
    if st.button("📅 Ir a nuevo mes"):
        nuevo_mes = 1 if mes == 12 else mes + 1
        nuevo_año = año + 1 if mes == 12 else año

        hojas_a_copiar = ["Ingresos", "Provisiones", "Gastos Fijos", "Ahorros", "Deudas"]

        for hoja in hojas_a_copiar:
            try:
                df = read_sheet_as_df(sheet, hoja)
                if "mes" in df.columns and "año" in df.columns:
                    df_actual = df[(df["mes"] == mes) & (df["año"] == año)].copy()
                    if df_actual.empty:
                        continue
                    df_actual["mes"] = nuevo_mes
                    df_actual["año"] = nuevo_año

                    if hoja == "Provisiones" and "se_usó" in df_actual.columns:
                        df_actual["se_usó"] = "No"
                    if hoja == "Gastos Fijos" and "estado" in df_actual.columns:
                        df_actual["estado"] = "Pendiente"
                    if hoja == "Deudas" and "cuota_mes" in df_actual.columns:
                        df_actual["cuota_mes"] = 0

                    df_final = pd.concat([df, df_actual], ignore_index=True)
                    write_df_to_sheet(sheet, hoja, df_final)
            except Exception as e:
                st.warning(f"No se pudo copiar {hoja}: {e}")

        st.session_state["mes_actual"] = nuevo_mes
        st.session_state["año_actual"] = nuevo_año
        st.success(f"Datos copiados para {nuevo_mes}/{nuevo_año}.")

# === Validación de acceso ===
def validar_clave():
    if st.session_state.pin_clave == st.secrets["security"]["pin"]:
        st.session_state.acceso_autorizado = True
    else:
        st.error("PIN incorrecto.")

if "acceso_autorizado" not in st.session_state:
    st.session_state.acceso_autorizado = False

if not st.session_state.acceso_autorizado:
    st.text_input("Ingresa tu PIN:", type="password", key="pin_clave", on_change=validar_clave)
    st.stop()

# === Conexión con Google Sheets ===
SHEET_KEY = "1OPCAwKXoEHBmagpvkhntywqkAit7178pZv3ptXd9d9w"
sheet = connect_to_sheet(st.secrets["credentials"], SHEET_KEY)

# === Selección de mes y año ===
today = datetime.date.today()
col1, col2 = st.columns(2)
with col1:
    mes = st.selectbox("Mes", list(range(1, 13)), index=today.month - 1, key="mes_selector")
with col2:
    año = st.selectbox("Año", list(range(2024, 2031)), index=1, key="año_selector")

# === Leer cuentas ===
try:
    df_cuentas = read_sheet_as_df(sheet, "Cuentas")
    lista_cuentas = df_cuentas["nombre_cuenta"].dropna().unique().tolist()
except:
    lista_cuentas = []

# === Función para mostrar y guardar editor ===
def mostrar_editor(nombre_hoja, columnas_dropdown=None):
    try:
        df = read_sheet_as_df(sheet, nombre_hoja)
    except:
        st.warning(f"No se pudo cargar la hoja '{nombre_hoja}'")
        return

    tiene_mes_anio = "mes" in df.columns and "año" in df.columns
    df_filtrado = df[(df["mes"] == mes) & (df["año"] == año)] if tiene_mes_anio else df.copy()
    st.subheader(f"{nombre_hoja} ({mes}/{año})" if tiene_mes_anio else nombre_hoja)

    columnas_ocultas = ["mes", "año"]
    columnas_visibles = [c for c in df_filtrado.columns if c not in columnas_ocultas]

    edited_df = st.data_editor(
        df_filtrado[columnas_visibles],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            col: st.column_config.SelectboxColumn("Cuenta", options=lista_cuentas, required=True)
            for col in (columnas_dropdown or []) if col in columnas_visibles
        }
    )

    if st.button(f"💾 Guardar cambios en {nombre_hoja}", key=f"save_{nombre_hoja}"):
        if tiene_mes_anio:
            edited_df["mes"] = mes
            edited_df["año"] = año
            df_sin_filtro = df[~((df["mes"] == mes) & (df["año"] == año))]
            df_final = pd.concat([df_sin_filtro, edited_df], ignore_index=True)
        else:
            df_final = edited_df
        write_df_to_sheet(sheet, nombre_hoja, df_final)
        st.success(f"{nombre_hoja} actualizado correctamente.")

# === Tabs para mostrar categorías dentro de "Datos Detallados" ===
main_tabs = st.tabs(["📊 Resumen General",
                    "🔔 Alertas",
                    "📋 Datos Detallados",
                     "📈 Reportes y Análisis"])


with main_tabs[0]:
        st.subheader("📊 Resumen General")
    
with main_tabs[1]:
        st.subheader("🔔 Alertas")

with main_tabs[2]:
    # === Tabs principales reorganizados ===
    sub_tabs = st.tabs([
        "📥 Ingresos", 
        "🧾 Provisiones", 
        "💡 Gastos Fijos", 
        "🏦 Ahorros", 
        "👨‍👩‍👧‍👦 Reservas Familiares", 
        "💳 Deudas",
        "⚙️ Configuración"
    ])

    with sub_tabs[0]: mostrar_editor("Ingresos", columnas_dropdown=["cuenta"])
    with sub_tabs[1]: mostrar_editor("Provisiones")
    with sub_tabs[2]: mostrar_editor("Gastos Fijos", columnas_dropdown=["cuenta_pago"])
    with sub_tabs[3]: mostrar_editor("Ahorros", columnas_dropdown=["cuenta"])
    with sub_tabs[4]: mostrar_editor("Reservas Familiares", columnas_dropdown=["cuenta"])
    with sub_tabs[5]: mostrar_editor("Deudas")

    with sub_tabs[6]:
        st.subheader("🏦 Cuentas")
        try:
            df_cuentas = read_sheet_as_df(sheet, "Cuentas")
        except:
            st.warning("No se pudo cargar la hoja 'Cuentas'")
            df_cuentas = pd.DataFrame(columns=["nombre_cuenta", "banco", "tipo"])

        edited_cuentas = st.data_editor(
            df_cuentas,
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("💾 Guardar cambios en Cuentas"):
            if edited_cuentas["nombre_cuenta"].isnull().any() or edited_cuentas["nombre_cuenta"].duplicated().any():
                st.error("No se permiten nombres vacíos ni duplicados.")
            else:
                write_df_to_sheet(sheet, "Cuentas", edited_cuentas)
                st.success("Cuentas actualizadas correctamente.")

    
with main_tabs[3]:
        st.subheader("📈 Reportes y Análisis")                