# 🧾 Control Financiero Personal

Hecho por **Macarena Mallea – Mayo 2025** 🫶

Esta aplicación te permite registrar, visualizar y analizar tus ingresos, gastos, provisiones, ahorros y deudas de forma mensual. Está construida con **Python + Streamlit** y conectada directamente a **Google Sheets** como base de datos.

---

## 🚀 ¿Qué necesitas para usarla?

### 1. Clonar o descargar este proyecto

```bash
git clone https://tu-repositorio-o-zip.com
cd nombre_del_proyecto
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Crear tu archivo `secrets.toml`

Dentro de `.streamlit/secrets.toml`:

```toml
[credentials]
type = "service_account"
client_email = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n..."

[security]
pin = "1234"
```

> Usa tu archivo `credentials.json` de Google Cloud para rellenar `[credentials]`.

---

## 🔐 Seguridad

Al abrir la app, se solicita un **PIN** para proteger tus datos. Puedes cambiarlo en el archivo `secrets.toml`.

---

## 🧠 Funcionalidades principales

- Registro y edición de ingresos, gastos, ahorros, provisiones y deudas
- Editor dinámico con validaciones
- Confirmación antes de guardar
- Alertas automáticas (gastos pendientes, provisiones en $0)
- Copiar mes anterior
- Visualización mensual: métricas, torta, evolución
- Análisis por categoría (Top 5)
- Calendario de vencimientos con gráfico de timeline
- Exportar resumen mensual a Excel
- Descargar histórico anual en Excel

---

## 🧪 Para probar en local

```bash
streamlit run app.py
```

---

## 🌐 Desplegar en Streamlit Cloud

1. Subir los archivos del proyecto a GitHub
2. Crear app nueva en [https://streamlit.io/cloud](https://streamlit.io/cloud)
3. Cargar tu archivo `secrets.toml` en el menú lateral → `Secrets`
4. ¡Listo!

---

## 💡 Créditos

Desarrollado por Macarena Mallea ✨
Asistencia técnica y amorosa por Max 💻🫶