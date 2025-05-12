# app.py
import streamlit as st
import pandas as pd
from google_sheets import connect_to_sheet, read_sheet_as_df, write_df_to_sheet
import datetime

# Configuración
SHEET_KEY = "1OPCAwKXoEHBmagpvkhntywqkAit7178pZv3ptXd9d9w"  # tu archivo en Drive
JSON_KEYFILE = "credentials.json"

# Conectar
sheet = connect_to_sheet(JSON_KEYFILE, SHEET_KEY)

# Elegir mes/año
st.title("🧾 Control de Ingresos")
today = datetime.date.today()
mes = st.selectbox("Mes", list(range(1, 13)), index=today.month - 1)
año = st.selectbox("Año", list(range(2024, 2031)), index=1)

# Leer y filtrar ingresos
df_ingresos = read_sheet_as_df(sheet, "Ingresos")
df_filtrado = df_ingresos[(df_ingresos['año'] == año) & (df_ingresos['mes'] == mes)]

# Mostrar editor
st.subheader(f"Ingresos registrados para {mes}/{año}")
edited_df = st.data_editor(df_filtrado, num_rows="dynamic", use_container_width=True)

# Guardar
if st.button("💾 Guardar cambios"):
    df_sin_filtro = df_ingresos[~((df_ingresos['año'] == año) & (df_ingresos['mes'] == mes))]
    df_final = pd.concat([df_sin_filtro, edited_df], ignore_index=True)
    write_df_to_sheet(sheet, "Ingresos", df_final)
    st.success("Datos actualizados correctamente.")
