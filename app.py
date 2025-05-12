import streamlit as st
import pandas as pd
from google_sheets import connect_to_sheet, read_sheet_as_df, write_df_to_sheet
import datetime

# Conexión a Google Sheets
SHEET_KEY = "1OPCAwKXoEHBmagpvkhntywqkAit7178pZv3ptXd9d9w"
credentials_secret = st.secrets["credentials"]
sheet = connect_to_sheet(credentials_secret, SHEET_KEY)

# Selección de mes y año
st.title("📊 Control Financiero Personal")
today = datetime.date.today()
mes = st.selectbox("Mes", list(range(1, 13)), index=today.month - 1)
año = st.selectbox("Año", list(range(2024, 2031)), index=1)

# Tabs por categoría
tabs = st.tabs(["Ingresos", "Provisiones", "Gastos Fijos", "Ahorros", "Reservas Familiares", "Deudas"])

# Función común para mostrar y editar
def mostrar_editor(nombre_hoja):
    df = read_sheet_as_df(sheet, nombre_hoja)
    if 'mes' in df.columns and 'año' in df.columns:
        df_filtrado = df[(df["mes"] == mes) & (df["año"] == año)]
    else:
        df_filtrado = df
    st.subheader(f"{nombre_hoja} ({mes}/{año})" if 'mes' in df.columns else f"{nombre_hoja}")
    edited_df = st.data_editor(df_filtrado, num_rows="dynamic", use_container_width=True)

    if st.button(f"💾 Guardar cambios en {nombre_hoja}", key=nombre_hoja):
        if 'mes' in df.columns and 'año' in df.columns:
            df_sin_filtro = df[~((df['mes'] == mes) & (df['año'] == año))]
            df_final = pd.concat([df_sin_filtro, edited_df], ignore_index=True)
        else:
            df_final = edited_df
        write_df_to_sheet(sheet, nombre_hoja, df_final)
        st.success(f"¡{nombre_hoja} actualizado correctamente!")

# Pestañas
with tabs[0]:
    mostrar_editor("Ingresos")

with tabs[1]:
    mostrar_editor("Provisiones")

with tabs[2]:
    mostrar_editor("Gastos Fijos")

with tabs[3]:
    mostrar_editor("Ahorros")

with tabs[4]:
    mostrar_editor("Reservas Familiares")

with tabs[5]:
    mostrar_editor("Deudas")
