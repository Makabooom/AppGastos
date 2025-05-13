# ================================================================
# App de Control Financiero Personal
# Hecho por Macarena Mallea – Mayo 2025
# ================================================================

# === Importación de librerías necesarias ===
import streamlit as st                          # Para construir la interfaz web
import pandas as pd                             # Para manejo de datos y estructuras tipo tabla
import datetime                                 # Para trabajar con fechas
import matplotlib.pyplot as plt                 # Para generar gráficos
from google_sheets import connect_to_sheet, read_sheet_as_df, write_df_to_sheet  # Módulo de Google Sheets personalizado
from io import BytesIO

# === Validación de PIN de acceso ===
if "acceso_autorizado" not in st.session_state:
    st.session_state.acceso_autorizado = False

if not st.session_state.acceso_autorizado:
    st.title("🔐 Acceso protegido")
    pin_ingresado = st.text_input("Ingresa tu PIN:", type="password")

    if st.button("🔓 Ingresar"):
        if pin_ingresado == st.secrets["security"]["pin"]:
            st.session_state.acceso_autorizado = True
            st.success("Acceso concedido. Bienvenida 👋")
        else:
            st.error("PIN incorrecto.")

    if not st.session_state.acceso_autorizado:
        st.stop()  # Detener ejecución si no está autorizada

# === Conectarse al Google Sheet usando credenciales seguras ===
SHEET_KEY = "1OPCAwKXoEHBmagpvkhntywqkAit7178pZv3ptXd9d9w"  # ID del documento en Google Sheets
sheet = connect_to_sheet(st.secrets["credentials"], SHEET_KEY)  # Conexión autenticada

# === Leer lista de cuentas bancarias desde la hoja "Cuentas" ===
try:
    df_cuentas = read_sheet_as_df(sheet, "Cuentas")  # Obtener la hoja
    lista_cuentas = df_cuentas["nombre_cuenta"].dropna().unique().tolist()  # Lista desplegable
except:
    lista_cuentas = []  # Si falla, dejar la lista vacía

# === Selección centralizada de mes y año ===
st.title("📋 Control Financiero Personal")
today = datetime.date.today()
col1, col2 = st.columns(2)
with col1:
    mes = st.selectbox("Mes", list(range(1, 13)), index=today.month - 1)  # Selección del mes actual
with col2:
    año = st.selectbox("Año", list(range(2024, 2031)), index=1)  # Selección del año

def mostrar_editor(nombre_hoja, columnas_dropdown=None):
    try:
        # Leer la hoja desde Google Sheets
        df = read_sheet_as_df(sheet, nombre_hoja)
         # === COPIAR DATOS DEL MES ANTERIOR (opcional por hoja) ===
        if nombre_hoja in ["Gastos Fijos", "Provisiones", "Ahorros"]:
            if st.button("📋 Copiar desde el mes anterior", key=f"copiar_{nombre_hoja}"):
                # Determinar mes y año anterior
                mes_anterior = mes - 1 if mes > 1 else 12
                año_anterior = año if mes > 1 else año - 1

                # Filtrar datos del mes anterior
                if tiene_mes_anio:
                    df_prev = df[(df["mes"] == mes_anterior) & (df["año"] == año_anterior)].copy()

                    # Reemplazar a mes actual
                    df_prev["mes"] = mes
                    df_prev["año"] = año

                    # Añadir las filas al DataFrame actual
                    df_filtrado = pd.concat([df_filtrado, df_prev], ignore_index=True)

                    st.success(f"Se copiaron {len(df_prev)} registros desde {mes_anterior}/{año_anterior}.")
    except:
        st.warning(f"No se pudo cargar la hoja '{nombre_hoja}'")
        return

    # Verifica si tiene columnas 'mes' y 'año'
    tiene_mes_anio = "mes" in df.columns and "año" in df.columns

    # Filtra por mes y año actual si corresponde
    if tiene_mes_anio:
        df_filtrado = df[(df["mes"] == mes) & (df["año"] == año)].copy()
    else:
        df_filtrado = df.copy()

    st.subheader(f"{nombre_hoja} ({mes}/{año})" if tiene_mes_anio else nombre_hoja)

    # Filtro por estado (si existe la columna)
    if "estado" in df_filtrado.columns:
        estados = df_filtrado["estado"].dropna().unique().tolist()
        estado_filtrado = st.selectbox("Filtrar por estado:", ["Todos"] + estados, key=f"{nombre_hoja}_estado")
        if estado_filtrado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["estado"] == estado_filtrado]

    # Mostrar total si hay columna 'monto'
    if "monto" in df_filtrado.columns:
        total = df_filtrado["monto"].sum()
        st.markdown(f"💰 **Total monto:** ${total:,.0f}")

    # Botón para agregar una nueva fila vacía
    if st.button("➕ Agregar fila nueva", key=f"add_{nombre_hoja}"):
        nueva_fila = pd.DataFrame([{"mes": mes, "año": año}], columns=df.columns) if tiene_mes_anio else pd.DataFrame([{}], columns=df.columns)
        df_filtrado = pd.concat([df_filtrado, nueva_fila], ignore_index=True)

    # Ocultar columnas 'mes' y 'año' en el editor
    columnas_ocultas = ["mes", "año"]  # Mostramos "día", ocultamos solo mes y año
    columnas_visibles = [c for c in df_filtrado.columns if c not in columnas_ocultas]

    # Editor de datos interactivo
    edited_df = st.data_editor(
        df_filtrado[columnas_visibles],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            col: st.column_config.SelectboxColumn("Cuenta", options=lista_cuentas, required=True)
            for col in (columnas_dropdown or []) if col in columnas_visibles
        }
    )

    # === GUARDAR CON VALIDACIÓN Y CONFIRMACIÓN ===
    if f"confirm_{nombre_hoja}" not in st.session_state:
        st.session_state[f"confirm_{nombre_hoja}"] = False

    # Mostrar casilla de confirmación
    confirmar = st.checkbox("✅ Confirmo que deseo guardar los cambios", key=f"confirm_{nombre_hoja}")
    
    if st.button(f"💾 Guardar cambios en {nombre_hoja}", key=f"save_{nombre_hoja}"):

        # VALIDACIONES
        errores = []

        if "monto" in edited_df.columns:
            if not pd.to_numeric(edited_df["monto"], errors="coerce").notna().all():
                errores.append("Hay valores no numéricos en la columna 'monto'.")
            elif (edited_df["monto"] < 0).any():
                errores.append("Hay montos negativos en la columna 'monto'.")

        for col in ["cuenta", "cuenta_pago"]:
            if col in edited_df.columns:
                if not edited_df[col].isin(lista_cuentas).all():
                    errores.append(f"Hay cuentas no válidas en la columna '{col}'.")

        if errores:
            for err in errores:
                st.error(f"🛑 {err}")
            return

        if not confirmar:
            st.info("Marca la casilla para confirmar antes de guardar.")
            return

        # COMPLETAR MES Y AÑO
        if tiene_mes_anio:
            edited_df["mes"] = mes
            edited_df["año"] = año
            df_sin_filtro = df[~((df["mes"] == mes) & (df["año"] == año))]
            df_final = pd.concat([df_sin_filtro, edited_df], ignore_index=True)
        else:
            df_final = edited_df

        # GUARDAR
        write_df_to_sheet(sheet, nombre_hoja, df_final)
        st.success(f"{nombre_hoja} actualizado correctamente.")

        # Resetear checkbox
        st.session_state[f"confirm_{nombre_hoja}"] = False

from io import BytesIO

def generar_excel_resumen(mes, año, resumen, df_gas, df_aho, df_prov, df_deu, df_ing):
    from openpyxl import Workbook
    from openpyxl.chart import PieChart, Reference
    from openpyxl.utils.dataframe import dataframe_to_rows

    wb = Workbook()
    ws = wb.active
    ws.title = "Resumen"

    # Escribir resumen
    ws.append(["Resumen financiero", f"{mes}/{año}"])
    ws.append([])
    for item in resumen:
        ws.append(item)

    ws.append([])
    ws.append(["Detalle de Egresos"])

    # === Exportar resumen ===
    st.markdown("### 📤 Exportar resumen mensual")

    resumen = [
        ["Total Ingresos", total_ingresos],
        ["Total Gastos Fijos", total_gastos],
        ["Total Deudas", total_deudas],
        ["Total Provisiones usadas", total_provisiones],
        ["Total Ahorros", total_ahorros],
        ["Saldo estimado", saldo]
    ]

    excel_bytes = generar_excel_resumen(mes, año, resumen, df_gas, df_aho, df_prov, df_deu, df_ing)

    st.download_button(
        label="📥 Descargar resumen en Excel",
        data=excel_bytes,
        file_name=f"Resumen_{mes}_{año}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # === Calendario de pagos del mes ===
    st.markdown("## 📆 Vencimientos del mes")

    try:
        calendario = []

        # Deudas
        if not df_deu.empty:
            for i, row in df_deu.iterrows():
                dia = row.get("día")
                dia = int(dia) if pd.notna(dia) else 5  # valor por defecto si está vacío
                fecha = datetime.date(año, mes, dia)
                descripcion = row.get("descripcion", "Deuda")
                monto = row.get("monto_cuota", 0)
                calendario.append((fecha, f"💳 {descripcion}", monto))

        # Gastos fijos
        if not df_gas.empty:
            for i, row in df_gas.iterrows():
                dia = row.get("día")
                dia = int(dia) if pd.notna(dia) else 5  # valor por defecto si está vacío
                fecha = datetime.date(año, mes, dia)
                nombre = row.get("nombre", "Gasto Fijo")
                monto = row.get("monto", 0)
                calendario.append((fecha, f"💡 {nombre}", monto))

        # Ordenar por fecha
        calendario.sort()

        # Mostrar tabla
        df_calendario = pd.DataFrame(calendario, columns=["Fecha", "Descripción", "Monto"])
        df_calendario["Fecha"] = df_calendario["Fecha"].dt.strftime("%d-%m-%Y")
        st.table(df_calendario)

    except Exception as e:
        st.error("No se pudo generar el calendario de pagos.")
        
    # === Timeline visual de pagos con colores y línea de hoy ===
    st.markdown("### 📅 Visualización de pagos del mes")

    try:
        if not df_calendario.empty:
            # Preparar datos
            df_calendario["Día"] = pd.to_datetime(df_calendario["Fecha"], format="%d-%m-%Y").dt.day

            # Detectar tipo por ícono en la descripción
            def detectar_tipo(desc):
                if "💳" in desc:
                    return "deuda"
                elif "💡" in desc:
                    return "gasto"
                else:
                    return "otro"

            df_calendario["tipo"] = df_calendario["Descripción"].apply(detectar_tipo)
            df_calendario.sort_values("Día", inplace=True)

            # Asignar colores
            colores = df_calendario["tipo"].map({
                "deuda": "#e74c3c",     # rojo
                "gasto": "#3498db",     # azul
                "otro": "#95a5a6"       # gris
            })

            # Dibujar gráfico
            fig, ax = plt.subplots(figsize=(8, len(df_calendario) * 0.6))

            ax.barh(df_calendario["Descripción"], df_calendario["Día"], color=colores)
            ax.set_xlabel("Día del mes")
            ax.set_title("Vencimientos del mes")
            ax.invert_yaxis()  # Los más próximos arriba
            ax.grid(axis="x")

            # Línea vertical para hoy (si coincide con el mes)
            hoy = datetime.date.today()
            if hoy.month == mes and hoy.year == año:
                ax.axvline(hoy.day, color="green", linestyle="--", label="Hoy")
                ax.legend()

            st.pyplot(fig)
        else:
            st.info("No hay datos para mostrar en el timeline.")
    except Exception as e:
        st.error("Error al generar el gráfico de timeline.")
            
    # Agregar gráfico de torta si hay valores
    egresos = resumen[1:]
    chart = PieChart()
    labels = Reference(ws, min_col=1, min_row=5, max_row=8)
    data = Reference(ws, min_col=2, min_row=5, max_row=8)
    chart.add_data(data, titles_from_data=False)
    chart.set_categories(labels)
    chart.title = "Distribución de Egresos"
    ws.add_chart(chart, "D10")

    # Agregar cada hoja de datos
    for nombre, df in [("Gastos", df_gas), ("Ahorros", df_aho), ("Provisiones", df_prov), ("Deudas", df_deu), ("Ingresos", df_ing)]:
        ws2 = wb.create_sheet(title=nombre)
        for r in dataframe_to_rows(df, index=False, header=True):
            ws2.append(r)

    # Exportar como BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


# === Resumen financiero del mes ===
with st.expander("📊 Ver resumen del mes actual", expanded=True):
    st.subheader(f"Resumen financiero - {mes}/{año}")

    # Cargar hojas necesarias para el resumen
    df_ing = read_sheet_as_df(sheet, "Ingresos")
    df_gas = read_sheet_as_df(sheet, "Gastos Fijos")
    df_prov = read_sheet_as_df(sheet, "Provisiones")
    df_deu = read_sheet_as_df(sheet, "Deudas")
    df_aho = read_sheet_as_df(sheet, "Ahorros")

    # Filtrar los datos por mes/año
    df_ing = df_ing[(df_ing["mes"] == mes) & (df_ing["año"] == año)]
    df_gas = df_gas[(df_gas["mes"] == mes) & (df_gas["año"] == año)]
    df_prov = df_prov[(df_prov["mes"] == mes) & (df_prov["año"] == año)]
    df_deu = df_deu[(df_deu["mes"] == mes) & (df_deu["año"] == año)]
    df_aho = df_aho[(df_aho["mes"] == mes) & (df_aho["año"] == año)]

    # Sumar totales por tipo
    total_ingresos = df_ing["monto"].sum() if "monto" in df_ing.columns else 0
    total_gastos = df_gas["monto"].sum() if "monto" in df_gas.columns else 0
    total_deudas = df_deu["monto_cuota"].sum() if "monto_cuota" in df_deu.columns else 0
    total_provisiones = df_prov["monto_usado"].sum() if "monto_usado" in df_prov.columns else 0
    total_ahorros = df_aho["monto_ingreso"].sum() if "monto_ingreso" in df_aho.columns else 0

    # Calcular saldo final estimado
    saldo = total_ingresos - (total_gastos + total_deudas + total_provisiones + total_ahorros)

    # Mostrar los totales con indicadores visuales
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🟢 Ingresos", f"${total_ingresos:,.0f}")
        st.metric("🟠 Gastos fijos", f"${total_gastos:,.0f}")
        st.metric("🔴 Deudas", f"${total_deudas:,.0f}")
    with col2:
        st.metric("🟣 Provisiones usadas", f"${total_provisiones:,.0f}")
        st.metric("🟡 Ahorros realizados", f"${total_ahorros:,.0f}")
        st.metric("🟢💰 Saldo estimado", f"${saldo:,.0f}")

    # === ALERTAS DE PRESUPUESTO ===
    st.markdown("### 🔔 Alertas de Presupuesto")

    try:
        # Leer hoja Presupuestos
        df_presup = read_sheet_as_df(sheet, "Presupuestos")
        df_presup = df_presup[(df_presup["mes"] == mes) & (df_presup["año"] == año)]

        # Crear diccionario con límites definidos
        presupuestos = dict(zip(df_presup["categoria"], df_presup["monto_maximo"]))

        # Comparar con montos reales
        comparaciones = {
            "Gastos Fijos": total_gastos,
            "Provisiones": total_provisiones,
            "Ahorros": total_ahorros
        }

        for cat, real in comparaciones.items():
            limite = presupuestos.get(cat)
            if limite is not None:
                if real > limite:
                    st.error(f"🚨 Te pasaste en **{cat}**: gastaste ${real:,.0f} (límite ${limite:,.0f})")
                else:
                    st.success(f"✅ {cat}: dentro del presupuesto (${real:,.0f} / ${limite:,.0f})")
            else:
                st.info(f"ℹ️ No hay presupuesto definido para **{cat}**")

    except Exception as e:
        st.warning("No se pudo cargar o procesar la hoja 'Presupuestos'. Revísala en Google Sheets.")


    # === Gráfico de torta con distribución de egresos ===
    egresos = {
        "Gastos": total_gastos,
        "Deudas": total_deudas,
        "Provisiones": total_provisiones,
        "Ahorros": total_ahorros
    }
    fig, ax = plt.subplots()
    ax.pie(egresos.values(), labels=egresos.keys(), autopct="%1.1f%%", startangle=90)
    ax.axis("equal")  # Hacerlo circular
    st.pyplot(fig)

    # === ALERTAS AUTOMÁTICAS ===
    st.markdown("### 🚨 Alertas automáticas")

    # Alertas en Provisiones
    prov_alertas = df_prov[df_prov["total_acumulado"] == 0] if "total_acumulado" in df_prov.columns else pd.DataFrame()
    if not prov_alertas.empty:
        for i, row in prov_alertas.iterrows():
            st.error(f"⚠️ Provisión sin fondo: **{row['nombre']}** tiene $0 disponible.")

    # Alertas en Gastos Fijos pendientes
    gastos_pend = df_gas[df_gas["estado"].str.lower() == "pendiente"] if "estado" in df_gas.columns else pd.DataFrame()
    if not gastos_pend.empty:
        for i, row in gastos_pend.iterrows():
            st.warning(f"🕒 Gasto pendiente: **{row['nombre']}** por ${row['monto']:,.0f} no ha sido pagado.")

    # Alertas en Deudas no pagadas (cuotas_mes = 0)
    deudas_sin_pago = df_deu[df_deu["cuotas_mes"] == 0] if "cuotas_mes" in df_deu.columns else pd.DataFrame()
    if not deudas_sin_pago.empty:
        for i, row in deudas_sin_pago.iterrows():
            st.warning(f"📌 Deuda sin pago este mes: **{row['descripcion']}** - cuota ${row['monto_cuota']:,.0f}")

# === Gráfico de evolución mensual ===
st.subheader("📈 Evolución mensual (últimos 12 meses)")

# Funcón para agrupar por mes y año
def agrupar(df, campo, nombre):
    if campo in df.columns:
        return df.groupby(["año", "mes"])[campo].sum().reset_index(name=nombre)
    else:
        return pd.DataFrame(columns=["año", "mes", nombre])

# Función para generar el histórico
def generar_excel_historico(anio, hojas_dict):
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    output = BytesIO()
    wb = Workbook()
    wb.remove(wb.active)

    for nombre, df in hojas_dict.items():
        df_filtrado = df[df["año"] == anio] if "año" in df.columns else df
        ws = wb.create_sheet(title=nombre)
        for r in dataframe_to_rows(df_filtrado, index=False, header=True):
            ws.append(r)

    wb.save(output)
    output.seek(0)
    return output

# Agrupar cada categoría
df_evo_ing = agrupar(df_ing, "monto", "Ingresos")
df_evo_gas = agrupar(df_gas, "monto", "Gastos")
df_evo_deu = agrupar(df_deu, "monto_cuota", "Deudas")
df_evo_prov = agrupar(df_prov, "monto_usado", "Provisiones")
df_evo_aho = agrupar(df_aho, "monto_ingreso", "Ahorros")

# Unir todas las tablas
from functools import reduce
st.image("banner_makaboom.png", use_column_width=True)

frames = [df_evo_ing, df_evo_gas, df_evo_deu, df_evo_prov, df_evo_aho]
df_evolucion = reduce(lambda left, right: pd.merge(left, right, on=["año", "mes"], how="outer"), frames)
df_evolucion.fillna(0, inplace=True)  # Reemplazar nulos

# Crear columna fecha y ordenar
df_evolucion["fecha"] = pd.to_datetime(dict(year=df_evolucion["año"], month=df_evolucion["mes"], day=1))
df_evolucion.sort_values("fecha", inplace=True)
df_evolucion = df_evolucion.tail(12)  # Mostrar últimos 12 meses

# Dibujar gráfico de líneas
fig, ax = plt.subplots(figsize=(10, 4))
for col in ["Ingresos", "Gastos", "Deudas", "Provisiones", "Ahorros"]:
    ax.plot(df_evolucion["fecha"], df_evolucion[col], label=col, marker="o")
ax.set_title("Evolución mensual")
ax.set_xlabel("Mes")
ax.set_ylabel("Monto")
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

# === Tabs principales del sistema ===
tabs = st.tabs([
    "📥 Ingresos", 
    "🧾 Provisiones", 
    "💡 Gastos Fijos", 
    "🏦 Ahorros", 
    "👨‍👩‍👧‍👦 Reservas Familiares", 
    "💳 Deudas",
    "⚙️ Configuración", 
    "📊 Presupuestos"
])

# Mostrar cada pestaña con sus opciones correspondientes
with tabs[0]: mostrar_editor("Ingresos", columnas_dropdown=["cuenta"])
with tabs[1]: mostrar_editor("Provisiones")
with tabs[2]: mostrar_editor("Gastos Fijos", columnas_dropdown=["cuenta_pago"])
with tabs[3]: mostrar_editor("Ahorros", columnas_dropdown=["cuenta"])
with tabs[4]: mostrar_editor("Reservas Familiares", columnas_dropdown=["cuenta"])
with tabs[5]: mostrar_editor("Deudas")

# === TAB 6: Configuración de Cuentas ===
with tabs[6]:
    st.subheader("⚙️ Configuración de Cuentas")

    try:
        df_cuentas = read_sheet_as_df(sheet, "Cuentas")
    except:
        df_cuentas = pd.DataFrame(columns=["nombre_cuenta", "banco", "tipo_cuenta"])

    edited_cuentas = st.data_editor(
        df_cuentas,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Guardar cambios en cuentas"):
        write_df_to_sheet(sheet, "Cuentas", edited_cuentas)
        st.success("Cuentas actualizadas correctamente.")

# === TAB 7: Presupuestos Mensuales ===
with tabs[7]:
    st.subheader("💰 Presupuestos por Categoría")

    try:
        df_presup = read_sheet_as_df(sheet, "Presupuestos")
    except:
        df_presup = pd.DataFrame(columns=["categoria", "monto_maximo", "mes", "año"])

    edited_presup = st.data_editor(
        df_presup,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Guardar presupuestos"):
        write_df_to_sheet(sheet, "Presupuestos", edited_presup)
        st.success("Presupuestos actualizados correctamente.")

# === Exportar histórico del año ===
st.markdown("## 📦 Descargar histórico anual")

todas_hojas = {
    "Ingresos": read_sheet_as_df(sheet, "Ingresos"),
    "Gastos Fijos": read_sheet_as_df(sheet, "Gastos Fijos"),
    "Provisiones": read_sheet_as_df(sheet, "Provisiones"),
    "Ahorros": read_sheet_as_df(sheet, "Ahorros"),
    "Deudas": read_sheet_as_df(sheet, "Deudas"),
    "Reservas Familiares": read_sheet_as_df(sheet, "Reservas Familiares")
}

archivo_historico = generar_excel_historico(año, todas_hojas)

st.download_button(
    label="📥 Descargar histórico anual",
    data=archivo_historico,
    file_name=f"Historico_{año}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


# === Análisis por categoría (Top 5 gastos) ===
st.markdown("## 📊 Análisis por categoría: Top 5 gastos fijos")

try:
    df_gastos_mes = df_gas[(df_gas["mes"] == mes) & (df_gas["año"] == año)]

    if not df_gastos_mes.empty:
        top_gastos = (
            df_gastos_mes.groupby("nombre")["monto"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )

        # Mostrar tabla
        st.table(top_gastos.reset_index().rename(columns={"monto": "Total"}))

        # Gráfico de torta
        fig, ax = plt.subplots()
        ax.pie(top_gastos.values, labels=top_gastos.index, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.info("No hay gastos registrados para este mes.")
except Exception as e:
    st.error("No se pudo generar el análisis por categoría.")        

# === Análisis por categoría: Top 5 provisiones usadas ===
st.markdown("## 📊 Análisis por categoría: Top 5 provisiones usadas")

try:
    df_prov_mes = df_prov[(df_prov["mes"] == mes) & (df_prov["año"] == año)]

    if not df_prov_mes.empty and "nombre" in df_prov_mes.columns and "monto_usado" in df_prov_mes.columns:
        top_prov = (
            df_prov_mes.groupby("nombre")["monto_usado"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )

        # Mostrar tabla
        st.table(top_prov.reset_index().rename(columns={"monto_usado": "Total Usado"}))

        # Gráfico de torta
        fig, ax = plt.subplots()
        ax.pie(top_prov.values, labels=top_prov.index, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.info("No hay provisiones usadas para este mes.")
except Exception as e:
    st.error("No se pudo generar el análisis de provisiones.")

# === Simulador del mes siguiente ===
st.markdown("## 🔮 Simulador del mes siguiente")

# Calcular mes y año siguiente
mes_sim = mes + 1 if mes < 12 else 1
año_sim = año if mes < 12 else año + 1

st.markdown(f"📅 Simulación para: **{mes_sim}/{año_sim}**")

try:
    # Copiar datos actuales
    sim_ing = df_ing.copy()
    sim_gas = df_gas.copy()
    sim_prov = df_prov.copy()
    sim_aho = df_aho.copy()
    sim_deu = df_deu.copy()

    # Reemplazar mes/año
    for df_sim in [sim_ing, sim_gas, sim_prov, sim_aho, sim_deu]:
        if "mes" in df_sim.columns:
            df_sim["mes"] = mes_sim
        if "año" in df_sim.columns:
            df_sim["año"] = año_sim

    # Sumar totales simulados
    s_ing = sim_ing["monto"].sum() if "monto" in sim_ing.columns else 0
    s_gas = sim_gas["monto"].sum() if "monto" in sim_gas.columns else 0
    s_deu = sim_deu["monto_cuota"].sum() if "monto_cuota" in sim_deu.columns else 0
    s_prov = sim_prov["monto_usado"].sum() if "monto_usado" in sim_prov.columns else 0
    s_aho = sim_aho["monto_ingreso"].sum() if "monto_ingreso" in sim_aho.columns else 0
    s_saldo = s_ing - (s_gas + s_deu + s_prov + s_aho)

    # Mostrar métricas
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🟢 Ingresos estimados", f"${s_ing:,.0f}")
        st.metric("🟠 Gastos fijos estimados", f"${s_gas:,.0f}")
        st.metric("🔴 Deudas estimadas", f"${s_deu:,.0f}")
    with col2:
        st.metric("🟣 Provisiones estimadas", f"${s_prov:,.0f}")
        st.metric("🟡 Ahorros estimados", f"${s_aho:,.0f}")
        st.metric("🟢💰 Saldo estimado", f"${s_saldo:,.0f}")

except Exception as e:
    st.error("No se pudo generar la simulación.")