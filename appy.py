import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import io
import time
import base64
from datetime import datetime, timedelta

st.set_page_config(page_title="Gestión de Inversionistas", layout="wide")

# =========================================================================
# 🎬 PANTALLA DE BIENVENIDA (8 SEGUNDOS EXACTOS)
# =========================================================================
if 'bienvenida_completada' not in st.session_state:

    def obtener_imagen_base64(ruta_archivo):
        if os.path.exists(ruta_archivo):
            with open(ruta_archivo, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        return None

    imagen_b64 = obtener_imagen_base64("Bienvenida.png")

    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
            .contenedor-bienvenida-fijo {
                width: 100%;
                max-width: 680px;
                margin: 0 auto;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.5);
                overflow: hidden;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    if imagen_b64:
        st.markdown(
            f"""
            <div class="contenedor-bienvenida-fijo">
                <img src="data:image/jpeg;base64,{imagen_b64}" style="width:100%; display:block;">
            </div>
            """, 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="contenedor-bienvenida-fijo" style="height:350px; background: linear-gradient(135deg, #1d3557, #4ea8de); 
            display:flex; flex-direction:column; align-items:center; justify-content:center; color:white; font-weight:bold;">
                ⚠️ Falta el archivo "Bienvenida.png" en la carpeta raíz del proyecto.
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    contenedor_linea_carga = st.empty()
    
    pasos = 100
    tiempo_total = 8.0
    espera_por_paso = tiempo_total / pasos
    
    for i in range(pasos + 1):
        with contenedor_linea_carga.container():
            st.progress(i / 100)
            st.markdown(f"<p style='text-align: center; font-size: 32px; font-weight: bold; color: #56cfe1; margin: 5px 0 0 0;'>{i}%</p>", unsafe_allow_html=True)
            
            texto_pantalla = ""
            if i < 30: texto_pantalla = "Conectando con los mercados financieros..."
            elif i < 70: texto_pantalla = "Sincronizando participación de inversionistas..."
            else: texto_pantalla = "Estructurando matriz de rendimiento analítico..."
                
            st.markdown(f"<p style='text-align: center; color: #888; font-size: 14px; margin-top: 2px;'>{texto_pantalla}</p>", unsafe_allow_html=True)
        time.sleep(espera_por_paso)
            
    st.session_state.bienvenida_completada = True
    st.rerun()


# =========================================================================
# 📊 CONTROL, RECONSTRUCCIÓN Y PREVENCIÓN DE ERRORES DE BASE DE DATOS
# =========================================================================

st.sidebar.header("🔑 Configuración de Conexión Nube")
AZURE_CONNECTION_STRING = st.sidebar.text_input("Cadena de Conexión Azure:", value="", type="password")
CONTAINER_NAME = "datos-fondo"

datos_apertura_nueva_semana = [
    {'INVERSIONISTA': 'EDDINSON', 'CAPITAL ACUMULADO': 17840.40, 'SALDO INICIAL': 31040.90, 'FECHA_LUNES': '2026-05-25'},
    {'INVERSIONISTA': 'CESAR', 'CAPITAL ACUMULADO': 9450.00, 'SALDO INICIAL': 19857.42, 'FECHA_LUNES': '2026-05-25'},
    {'INVERSIONISTA': 'NICOLAS', 'CAPITAL ACUMULADO': 15000.00, 'SALDO INICIAL': 18699.41, 'FECHA_LUNES': '2026-05-25'},
    {'INVERSIONISTA': 'TAGUIRA', 'CAPITAL ACUMULADO': 1814.85, 'SALDO INICIAL': 1935.98, 'FECHA_LUNES': '2026-05-25'},
    {'INVERSIONISTA': 'ARTURO', 'CAPITAL ACUMULADO': 5000.00, 'SALDO INICIAL': 7133.93, 'FECHA_LUNES': '2026-05-25'},
    {'INVERSIONISTA': 'EMMANUEL', 'CAPITAL ACUMULADO': 5000.00, 'SALDO INICIAL': 5911.02, 'FECHA_LUNES': '2026-05-25'},
    {'INVERSIONISTA': 'ZAID', 'CAPITAL ACUMULADO': 10000.00, 'SALDO INICIAL': 10225.90, 'FECHA_LUNES': '2026-05-25'},
    {'INVERSIONISTA': 'GABRIEL', 'CAPITAL ACUMULADO': 760.00, 'SALDO INICIAL': 1187.31, 'FECHA_LUNES': '2026-05-25'}
]

datos_historicos_defecto = [
    {'SEMANA': 'MAYO 18 - MAYO 24', 'INVERSIONISTA': 'EDDINSON', 'CAPITAL ACUMULADO': 17840.40, 'SALDO INICIAL': 30355.17, 'PART_INICIAL': 32.73, 'SALDO FINAL': 31040.90, 'GANANCIA / PERDIDA': 685.73, 'DEPOSITOS': 0.0, 'RETIROS': 0.0, 'SALDO ACTUAL': 31040.90, 'PART_FINAL': 32.49}
]

def cargar_desde_storage(nombre_archivo, datos_defecto):
    df_resultado = None
    if AZURE_CONNECTION_STRING and AZURE_CONNECTION_STRING.strip() != "":
        try:
            from azure.storage.blob import BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
            blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=nombre_archivo)
            if blob_client.exists():
                descarga = blob_client.download_blob()
                datos_leidos = descarga.readall()
                # BLINDAJE: Si el archivo existe pero está vacío, evitar el KeyError inyectando la estructura por defecto
                if len(datos_leidos) == 0:
                    df_resultado = pd.DataFrame(datos_defecto)
                else:
                    df_resultado = pd.read_csv(io.BytesIO(datos_leidos))
        except Exception as e:
            st.sidebar.warning(f"Usando copia local de respaldo: {e}")
    
    if df_resultado is None:
        if not os.path.exists(nombre_archivo) or os.path.getsize(nombre_archivo) == 0:
            df_resultado = pd.DataFrame(datos_defecto)
            df_resultado.to_csv(nombre_archivo, index=False)
        else:
            try:
                df_resultado = pd.read_csv(nombre_archivo)
            except Exception:
                df_resultado = pd.DataFrame(datos_defecto)
                df_resultado.to_csv(nombre_archivo, index=False)

    df_resultado.columns = df_resultado.columns.str.strip().str.upper()
    if df_resultado.index.name is not None and df_resultado.index.name.strip().upper() == 'INVERSIONISTA':
        df_resultado = df_resultado.reset_index()
        df_resultado.columns = df_resultado.columns.str.strip().str.upper()

    if 'INVERSIONISTA' not in df_resultado.columns:
        df_resultado = pd.DataFrame(datos_defecto)
        df_resultado.columns = df_resultado.columns.str.strip().str.upper()
        df_resultado.to_csv(nombre_archivo, index=False)
        
    return df_resultado

def guardar_en_storage(df, nombre_archivo):
    if df.index.name is not None and df.index.name.strip().upper() == 'INVERSIONISTA':
        df = df.reset_index()
    df.columns = df.columns.str.strip().str.upper()
    
    df.to_csv(nombre_archivo, index=False)
    if AZURE_CONNECTION_STRING and AZURE_CONNECTION_STRING.strip() != "":
        try:
            from azure.storage.blob import BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
            blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=nombre_archivo)
            blob_client.upload_blob(df.to_csv(index=False), overwrite=True)
        except Exception as e:
            st.sidebar.error(f"No se pudo respaldar en Azure: {e}")

# Ejecución de carga y limpieza
df_inv = cargar_desde_storage('inversionistas.csv', datos_apertura_nueva_semana)
df_hist = cargar_desde_storage('historico_semanal.csv', datos_historicos_defecto)

df_inv['INVERSIONISTA'] = df_inv['INVERSIONISTA'].astype(str).str.strip().str.upper()

# Sincronización exacta de variables para TAGUIRA
df_inv.loc[df_inv['INVERSIONISTA'] == 'TAGUIRA', 'SALDO INICIAL'] = 1935.98
df_inv.loc[df_inv['INVERSIONISTA'] == 'TAGUIRA', 'CAPITAL ACUMULADO'] = 1814.85
df_inv['FECHA_LUNES'] = '2026-05-25'

fecha_lunes_str = str(df_inv['FECHA_LUNES'].iloc[0])
lunes_actual = datetime.strptime(fecha_lunes_str, '%Y-%m-%d')
domingo_actual = lunes_actual + timedelta(days=6)

label_lunes_columna = "Mayo 25"
label_domingo_columna = "Mayo 31"
semana_actual_label = "MAYO 25 - MAYO 31"

st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>📊 Panel de Control de Inversiones</h1>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align: center; color: #6c757d; margin-top: 5px; font-family: monospace;'>Consolidado a: {datetime.now().strftime('%d-%m-%Y')}</h4>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# =========================================================================
# 🎨 DISEÑO ESTILIZADO CSS
# =========================================================================
st.markdown(
    """
    <style>
        .contenedor-metricas-global {
            display: flex;
            justify-content: center;
            gap: 20px;
            width: 100%;
            max-width: 1100px;
            margin: 0 auto 25px auto;
        }
        .tarjeta-metrica-custom {
            flex: 1;
            background-color: #f8f9fa;
            padding: 18px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
            border: 1px solid #e6e8f1;
        }
        .metrica-titulo-custom {
            font-size: 12px;
            color: #6c757d;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metrica-valor-custom {
            font-size: 28px;
            font-weight: bold;
            color: #1d3557;
            margin-top: 6px;
        }
        .tabla-contenedor-global { 
            display: flex; 
            justify-content: center; 
            width: 100%; 
            margin-bottom: 25px; 
        }
        .tabla-contenedor { 
            overflow-x: auto; 
            width: 100%;
            max-width: 1200px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
            border-radius: 6px; 
        }
        .tabla-contenedor-recortado {
            overflow-x: auto;
            width: auto !important; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
            border-radius: 6px;
            margin: 0 auto;
        }
        .tabla-inversiones { 
            border-collapse: collapse; 
            font-family: -apple-system, sans-serif; 
            font-size: 13px; 
            color: #31333F; 
            background-color: #ffffff; 
            width: 100%; 
        }
        .tabla-inversiones th { 
            background-color: #f1f3f6; 
            font-weight: bold !important; 
            font-size: 12px !important; 
            padding: 12px 14px; 
            border-bottom: 2px solid #e6e8f1; 
            color: #111111; 
            text-transform: uppercase; 
            white-space: nowrap !important; 
            line-height: 1.4 !important; 
            text-align: center !important; 
            vertical-align: middle !important; 
        }
        .tabla-inversiones td { 
            padding: 10px 14px; 
            border-bottom: 1px solid #e6e8f1; 
            vertical-align: middle; 
            white-space: nowrap; 
        }
        .tabla-inversiones tr:last-child td { 
            background-color: #f8f9fa; 
            font-weight: bold !important; 
            font-size: 13px !important; 
            border-top: 2px solid #111111; 
            border-bottom: 2px solid #111111; 
            color: #000000; 
        }
        .align-left { text-align: left !important; padding-left: 20px !important; }
        .align-center { text-align: center !important; }
        .align-right { text-align: right !important; padding-right: 20px !important; }
        .ganancia-positiva { background-color: #baeec4 !important; color: #0e622b !important; font-weight: bold; }
        .ganancia-negativa { background-color: #ffbaba !important; color: #a71d1d !important; font-weight: bold; }
        .titulo-tabla-centrado { text-align: center; margin-top: 40px; margin-bottom: 15px; color: #111111; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True
)

def formatear_moneda(valor):
    if abs(valor) < 0.01: return "$0.00"
    return f"-${abs(valor):,.2f}" if valor < 0 else f"${valor:,.2f}"

# =========================================================================
# 📊 GRÁFICOS INTERACTIVOS (PLOTLY)
# =========================================================================
def construir_grafico_pie(df_fuente):
    df_filtrado_pie = df_fuente[df_fuente['INVERSIONISTA'] != 'TOTAL FONDO']
    fig = px.pie(df_filtrado_pie, names='INVERSIONISTA', values='CAPITAL ACUMULADO', title="<b>Distribución Porcentual por Capital Histórico Aportado</b>", color_discrete_sequence=px.colors.sequential.Tealgrn)
    fig.update_layout(title_x=0.5, font=dict(family="Arial", size=13))
    return fig

def generar_grafico_barras_dinamico(saldo_mes_curso):
    meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO (CURSO)']
    valores = [55267.83, 62826.23, 59708.76, 75043.26, saldo_mes_curso]
    fig = go.Figure(data=[go.Bar(x=meses, y=valores, text=[f"${v:,.2f}" for v in valores], textposition='inside', marker_color='#1d3557')])
    fig.update_layout(title="<b>Evolución Histórica del Fondo (Cierre Mensual)</b>", title_x=0.5, template="plotly_white")
    return fig

MAPEO_ENCABEZADOS_BR = {
    "INVERSIONISTA": "INVERSIONISTA",
    "CAPITAL ACUMULADO": "CAPITAL<br>ACUMULADO",
    "SALDO INICIAL": f"SALDO INICIAL<br>{label_lunes_columna}",
    "% PARTICIPACION": "% PARTICIPACION",
    "SALDO FINAL": f"SALDO FINAL<br>{label_domingo_columna}",
    "GANANCIA / PERDIDA": "GANANCIA /<br>PERDIDA",
    "DEPOSITOS": "DEPOSITOS",
    "RETIROS": "RETIROS",
    "SALDO ACTUAL": "SALDO ACTUAL",
    "PART_INICIAL": "% PART.<br>INICIAL",
    "PART_FINAL": "% PART.<br>FINAL",
    "CAPITAL BASE HISTORICO": "CAPITAL BASE<br>HISTORICO",
    "SALDO ACTUALIZADO": "SALDO<br>ACTUALIZADO",
    "GANANCIA HISTORICA TOTAL": "GANANCIA<br>HISTORICA TOTAL",
    "RETORNO (ROI)": "RETORNO<br>(ROI)"
}

def convertir_df_a_html_estilizado(df_data, es_tabla_resumen=False):
    clase_contenedor = "tabla-contenedor-recortado" if es_tabla_resumen else "tabla-contenedor"
    html_res = f'<div class="tabla-contenedor-global"><div class="{clase_contenedor}"><table class="tabla-inversiones"><thead><tr>'
    for col in df_data.columns:
        html_res += f'<th>{MAPEO_ENCABEZADOS_BR.get(col, col)}</th>'
    html_res += '</tr></thead><tbody>'
    
    columna_analizar = "GANANCIA HISTORICA TOTAL" if es_tabla_resumen else "GANANCIA / PERDIDA"
    for idx, row in df_data.iterrows():
        es_ultima_fila = (idx == len(df_data) - 1)
        html_res += '<tr>'
        for col in df_data.columns:
            clase_align = "align-left" if col == "INVERSIONISTA" else ("align-center" if "%" in col or "ROI" in col or "PARTICIPACION" in col else "align-right")
            
            clase_color = ""
            if col == columna_analizar and not es_ultima_fila:
                try:
                    valor_num = float(str(row[col]).replace('$', '').replace(',', ''))
                    if valor_num > 0.01: clase_color = " ganancia-positiva"
                    elif valor_num < -0.01: clase_color = " ganancia-negativa"
                except: pass
            
            html_res += f'<td class="{clase_align}{clase_color}">{row[col]}</td>'
        html_res += '</tr>'
    return html_res + '</tbody></table></div></div>'


# =========================================================================
# ⚖️ REPORTES EN PDF
# =========================================================================
def generar_pdf_reporte(dataframe_vis, identificador_semana, df_live_num, df_final_res_live, titulo_dinamico, saldo_grafico_mayo):
    try:
        from fpdf import FPDF
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        return None

    class PDF(FPDF):
        def header(self):
            self.set_fill_color(10, 25, 47) 
            self.rect(0, 0, 297, 14, 'F') 
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(197, 160, 89)
            self.set_y(1.5)
            self.cell(0, 4, 'MATRIZ SEMANAL DE RENDIMIENTO', align='C', new_x="LMARGIN", new_y="NEXT")
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(255, 255, 255)
            self.cell(0, 4, f'Periodo Historico Auditado: {identificador_semana.upper()}', align='C', new_x="LMARGIN", new_y="NEXT")

        def footer(self):
            self.set_y(-12)
            self.set_font('Helvetica', 'I', 7.5)
            self.set_text_color(120, 120, 120)
            self.cell(0, 6, f'Reporte Consolidado Exclusivo - Pagina {self.page_no()}', align='C')

    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    
    def limpiar_texto(val):
        return str(val).replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n').encode('ascii', 'ignore').decode('ascii')

    pdf.set_y(17) 
    pdf.set_font('Helvetica', 'B', 7.5)
    pdf.set_fill_color(241, 243, 246)
    pdf.set_text_color(10, 25, 47)
    
    columnas_dobles = [
        ("INVERSIONISTA", "", 28), ("CAPITAL", "ACUMULADO", 24),
        ("SALDO INICIAL", label_lunes_columna, 27), ("% PARTICIPACION", "", 22),
        ("SALDO FINAL", label_domingo_columna, 27), ("GANANCIA /", "PERDIDA", 25),
        ("DEPOSITOS", "", 20), ("RETIROS", "", 20),
        ("SALDO ACTUAL", "", 24), ("% PART.", "FINAL", 18)
    ]
    
    ancho_total_t1 = sum(c[2] for c in columnas_dobles)
    sangria_t1 = (297 - ancho_total_t1) / 2
    
    y_cabecera_t1 = pdf.get_y()
    pos_x_actual = sangria_t1
    
    for l1, l2, ancho in columnas_dobles:
        pdf.rect(pos_x_actual, y_cabecera_t1, ancho, 10, 'DF')
        if l2 != "":
            pdf.set_xy(pos_x_actual, y_cabecera_t1 + 1.2)
            pdf.multi_cell(ancho, 3.8, limpiar_texto(f"{l1}\n{l2}"), align='C', border=0)
        else:
            pdf.set_xy(pos_x_actual, y_cabecera_t1 + 3.2)
            pdf.multi_cell(ancho, 3.8, limpiar_texto(l1), align='C', border=0)
        pos_x_actual += ancho
        
    pdf.set_xy(sangria_t1, y_cabecera_t1 + 10)
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font('Helvetica', '', 7.5)
    for _, row in dataframe_vis.iterrows():
        nombre_socio = str(row['INVERSIONISTA']).strip()
        if "TOTAL" in nombre_socio.upper(): continue
            
        pdf.set_x(sangria_t1)
        pdf.cell(28, 4.6, limpiar_texto(nombre_socio), border=1, align='L')
        pdf.cell(24, 4.6, limpiar_texto(row['CAPITAL ACUMULADO']), border=1, align='R')
        pdf.cell(27, 4.6, limpiar_texto(row['SALDO INICIAL']), border=1, align='R')
        pdf.cell(22, 4.6, limpiar_texto(row['% PARTICIPACION']), border=1, align='C')
        pdf.cell(27, 4.6, limpiar_texto(row['SALDO FINAL']), border=1, align='R')
        
        try:
            gp_monto = float(str(row['GANANCIA / PERDIDA']).replace('$', '').replace(',', ''))
        except: gp_monto = 0.0

        fill_cell = False
        if gp_monto > 0.01:
            pdf.set_fill_color(186, 238, 196)
            fill_cell = True
        elif gp_monto < -0.01:
            pdf.set_fill_color(255, 186, 186)
            fill_cell = True

        pdf.cell(25, 4.6, limpiar_texto(row['GANANCIA / PERDIDA']), border=1, align='R', fill=fill_cell)
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(20, 4.6, limpiar_texto(row['DEPOSITOS']), border=1, align='R')
        pdf.cell(20, 4.6, limpiar_texto(row['RETIROS']), border=1, align='R')
        pdf.cell(24, 4.6, limpiar_texto(row['SALDO ACTUAL']), border=1, align='R')
        pdf.cell(18, 4.6, limpiar_texto(row['% PARTICIPACION FIN']), border=1, align='C')
        pdf.ln()
        
    row_total = dataframe_vis.iloc[-1]
    pdf.set_font('Helvetica', 'B', 7.5)
    pdf.set_fill_color(248, 249, 250)
    pdf.set_x(sangria_t1)
    
    pdf.cell(28, 5.2, 'TOTAL FONDO', border=1, align='L', fill=True)
    pdf.cell(24, 5.2, limpiar_texto(row_total['CAPITAL ACUMULADO']), border=1, align='R', fill=True)
    pdf.cell(27, 5.2, limpiar_texto(row_total['SALDO INICIAL']), border=1, align='R', fill=True)
    pdf.cell(22, 5.2, limpiar_texto(row_total['% PARTICIPACION']), border=1, align='C', fill=True)
    pdf.cell(27, 5.2, limpiar_texto(row_total['SALDO FINAL']), border=1, align='R', fill=True)
    pdf.cell(25, 5.2, limpiar_texto(row_total['GANANCIA / PERDIDA']), border=1, align='R', fill=True)
    pdf.cell(20, 5.2, limpiar_texto(row_total['DEPOSITOS']), border=1, align='R', fill=True)
    pdf.cell(20, 5.2, limpiar_texto(row_total['RETIROS']), border=1, align='R', fill=True)
    pdf.cell(24, 5.2, limpiar_texto(row_total['SALDO ACTUAL']), border=1, align='R', fill=True)
    pdf.cell(18, 5.2, limpiar_texto(row_total['% PARTICIPACION FIN']), border=1, align='C', fill=True)
    
    pdf.set_y(74)

    if df_final_res_live is not None:
        pdf.set_font('Helvetica', 'B', 8.5)
        pdf.set_text_color(10, 25, 47)
        pdf.cell(0, 5, limpiar_texto(titulo_dinamico.upper()), align='C', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        
        cols_resumen = [
            ("INVERSIONISTA", 36), ("CAPITAL BASE\nHISTORICO", 36), 
            ("SALDO\nACTUALIZADO", 36), ("GANANCIA\nHISTORICA TOTAL", 42), ("RETORNO\n(ROI)", 24)
        ]
        
        ancho_total_t2 = sum(c[1] for c in cols_resumen)
        sangria_t2 = (297 - ancho_total_t2) / 2
        
        y_cabecera = pdf.get_y()
        pdf.set_font('Helvetica', 'B', 7.5)
        pos_x_actual = sangria_t2
        
        for c_nom, c_ancho in cols_resumen:
            pdf.set_xy(pos_x_actual, y_cabecera)
            pdf.set_fill_color(230, 235, 245)
            pdf.rect(pos_x_actual, y_cabecera, c_ancho, 9, 'DF')
            pdf.multi_cell(c_ancho, 4.5, limpiar_texto(c_nom), align='C')
            pos_x_actual += c_ancho
            
        pdf.set_y(y_cabecera + 9)
        pdf.set_text_color(0, 0, 0)
        
        for idx, r_res in df_final_res_live.iterrows():
            pdf.set_x(sangria_t2)
            es_total = "TOTAL" in str(r_res['INVERSIONISTA']).upper()
            
            pdf.set_font('Helvetica', 'B' if es_total else '', 7.5)
            if es_total: pdf.set_fill_color(248, 249, 250)
            
            pdf.cell(36, 5, limpiar_texto(r_res['INVERSIONISTA']), border=1, align='L', fill=es_total)
            pdf.cell(36, 5, limpiar_texto(r_res['CAPITAL BASE HISTORICO']), border=1, align='R', fill=es_total)
            pdf.cell(36, 5, limpiar_texto(r_res['SALDO ACTUALIZADO']), border=1, align='R', fill=es_total)
            
            pos_x_g = pdf.get_x()
            pos_y_g = pdf.get_y()
            if not es_total:
                pdf.set_fill_color(186, 238, 196)
                pdf.rect(pos_x_g, pos_y_g, 42, 5, 'DF')
            pdf.cell(42, 5, limpiar_texto(r_res['GANANCIA HISTORICA TOTAL']), border=1, align='R', fill=True)
            
            if es_total: pdf.set_fill_color(248, 249, 250)
            pdf.cell(24, 5, limpiar_texto(r_res['RETORNO (ROI)']), border=1, align='C', fill=es_total)
            pdf.ln()

    try:
        fig1, ax1 = plt.subplots(figsize=(4.5, 1.8), dpi=250)
        colores = ['#4ea8de', '#56cfe1', '#64dfdf', '#72efdd', '#80ffdb', '#7400b8', '#6930c3', '#5e60ce']
        nombres = df_live_num['INVERSIONISTA'].values
        valores = df_live_num['CAPITAL ACUMULADO'].values
        if isinstance(valores[0], str):
            valores = [float(str(v).replace('$', '').replace(',', '')) for v in valores]

        ax1.pie(valores, labels=nombres, autopct='%1.1f%%', startangle=90, colors=colores[:len(valores)], textprops={'fontsize': 5.0})
        ax1.axis('equal')
        ax1.set_title("Distribucion Porcentual por Capital Aportado", fontsize=6.5, fontweight='bold', pad=15)
        
        img_buf1 = io.BytesIO()
        plt.savefig(img_buf1, format='png', bbox_inches='tight')
        img_buf1.seek(0)
        plt.close(fig1)
        pdf.image(img_buf1, x=10, y=136, w=134)
        
        fig2, ax2 = plt.subplots(figsize=(4.5, 1.8), dpi=250)
        meses_list = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO']
        saldos_list = [55267.83, 62826.23, 59708.76, 75043.26, saldo_grafico_mayo]
        
        barras = ax2.bar(meses_list, saldos_list, color='#2a6f97', width=0.42)
        ax2.set_title("Evolucion Historica del Fondo (Cierre Mensual)", fontsize=6.5, fontweight='bold', pad=15)
        ax2.tick_params(axis='both', labelsize=5.0)
        ax2.grid(axis='y', linestyle='--', alpha=0.3)
        
        for bar in barras:
            yval = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2.0, yval/2, f"${yval:,.2f}", ha='center', va='center', color='white', fontsize=4.0, fontweight='bold')
            
        img_buf2 = io.BytesIO()
        plt.savefig(img_buf2, format='png', bbox_inches='tight')
        img_buf2.seek(0)
        plt.close(fig2)
        pdf.image(img_buf2, x=152, y=136, w=134)
        
    except Exception as e:
        pdf.set_y(136)
        pdf.set_font('Helvetica', 'I', 7)
        pdf.cell(0, 4, f'Nota del Sistema: Graficos omitidos por buffer: {str(e)}', align='C')

    return bytes(pdf.output())


# =========================================================================
# ⚙️ PANEL LATERAL (CONTROLES DE ENTRADA Y FORMULARIOS)
# =========================================================================
st.sidebar.markdown("---")
st.sidebar.header("👥 Inversionistas")

with st.sidebar.expander("➕ Incluir Socio"):
    with st.form(key="formulario_registro", clear_on_submit=True):
        nuevo_nombre = st.text_input("Nombre de Socio").upper().strip()
        capital_inicial = st.number_input("Capital Acumulado Histórico ($)", min_value=0.0, format="%.2f")
        saldo_inicial_real = st.number_input("Saldo Inicial Apertura ($)", min_value=0.0, format="%.2f")
        if st.form_submit_button("Registrar Socio"):
            if nuevo_nombre and nuevo_nombre not in df_inv['INVERSIONISTA'].values:
                nueva_fila = pd.DataFrame([{
                    'INVERSIONISTA': nuevo_nombre, 
                    'CAPITAL ACUMULADO': round(capital_inicial, 2), 
                    'SALDO INICIAL': round(saldo_inicial_real, 2), 
                    'FECHA_LUNES': fecha_lunes_str
                }])
                df_inv = pd.concat([df_inv, nueva_fila], ignore_index=True)
                guardar_en_storage(df_inv, 'inversionistas.csv')
                st.success(f"Socio {nuevo_nombre} registrado correctamente.")
                st.rerun()

with st.sidebar.expander("🗑️ Eliminar Socio"):
    opciones_remover = ["-- Seleccionar --"] + df_inv['INVERSIONISTA'].tolist()
    socio_a_eliminar = st.selectbox("Seleccione socio a remover:", opciones_remover)
    if socio_a_eliminar != "-- Seleccionar --":
        if st.button(f"Confirmar Eliminación de {socio_a_eliminar}", type="primary"):
            df_inv = df_inv[df_inv['INVERSIONISTA'] != socio_a_eliminar]
            guardar_en_storage(df_inv, 'inversionistas.csv')
            st.success(f"Socio {socio_a_eliminar} removido.")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### **Saldo Real de la Cuenta**") 

# El input siempre se inicializa en 0.0 al cargar la app o refrescar
saldo_cierre_mercado = st.sidebar.number_input(
    "💵 Saldo de Cuenta", 
    label_visibility="collapsed", 
    min_value=0.0, 
    value=0.0, 
    format="%.2f"
)

st.sidebar.markdown("---")
st.sidebar.header("📂 Históricos de Reportes")
opciones_semana = ["Semana Activa (En Curso)"] + sorted(list(df_hist['SEMANA'].unique())) if not df_hist.empty else ["Semana Activa (En Curso)"]
semana_seleccionada = st.sidebar.selectbox("Seleccione período a auditar:", opciones_semana)

st.sidebar.markdown("---")
st.sidebar.header("📂 Depósitos / Retiros")

if 'depositos_dict' not in st.session_state:
    st.session_state.depositos_dict = {nom: 0.0 for nom in df_inv['INVERSIONISTA'].values}
if 'retiros_dict' not in st.session_state:
    st.session_state.retiros_dict = {nom: 0.0 for nom in df_inv['INVERSIONISTA'].values}

with st.sidebar.expander("📥 Registrar Movimientos"):
    socio_seleccionado = st.selectbox("Inversionista para movimientos:", df_inv['INVERSIONISTA'].values)
    st.session_state.depositos_dict[socio_seleccionado] = st.number_input("Monto Depósito ($)", min_value=0.0, value=st.session_state.depositos_dict.get(socio_seleccionado, 0.0), format="%.2f", key=f"i_dep_{socio_seleccionado}")
    st.session_state.retiros_dict[socio_seleccionado] = st.number_input("Monto Retiro ($)", min_value=0.0, value=st.session_state.retiros_dict.get(socio_seleccionado, 0.0), format="%.2f", key=f"i_ret_{socio_seleccionado}")


# =========================================================================
# 🔥 OPERACIÓN DE CIERRE AUTOMÁTICO DE SEMANA
# =========================================================================
if st.sidebar.button("💾 Guardar y Cerrar Semana Definitivamente"):
    saldo_inicial_global = round(df_inv['SALDO INICIAL'].sum(), 2)
    saldo_final_esperado = saldo_inicial_global if saldo_cierre_mercado == 0.0 else saldo_cierre_mercado
    ganancia_global_mercado = round(saldo_final_esperado - saldo_inicial_global, 2)
    
    ganancias_teoricas = ganancia_global_mercado * (df_inv['SALDO INICIAL'] / saldo_inicial_global)
    ganancias_redondeadas = ganancias_teoricas.round(2)
    
    diferencia_remanente = round(ganancia_global_mercado - ganancias_redondeadas.sum(), 2)
    if diferencia_remanente != 0:
        idx_ajuste = (ganancias_teoricas - ganancias_redondeadas).abs().idxmax()
        ganancias_redondeadas.at[idx_ajuste] = round(ganancias_redondeadas.at[idx_ajuste] + diferencia_remanente, 2)

    nuevos_registros = []
    for i, inv in df_inv.iterrows():
        nom = inv['INVERSIONISTA']
        part_inicial_ratio = inv['SALDO INICIAL'] / saldo_inicial_global if saldo_inicial_global > 0 else 0.0
        
        gan_ind = ganancias_redondeadas.iloc[i]
        sal_final_sem = round(inv['SALDO INICIAL'] + gan_ind, 2)
        
        dep = st.session_state.depositos_dict.get(nom, 0.0)
        ret = st.session_state.retiros_dict.get(nom, 0.0)
        
        saldo_actual_calculado = round(sal_final_sem + dep - ret, 2)
        
        nuevos_registros.append({
            'SEMANA': semana_actual_label, 'INVERSIONISTA': nom, 'CAPITAL ACUMULADO': inv['CAPITAL ACUMULADO'],
            'SALDO INICIAL': round(inv['SALDO INICIAL'], 2), 'PART_INICIAL': round(part_inicial_ratio * 100, 2),
            'SALDO FINAL': sal_final_sem, 'GANANCIA / PERDIDA': gan_ind,
            'DEPOSITOS': round(dep, 2), 'RETIROS': round(ret, 2), 'SALDO ACTUAL': saldo_actual_calculado, 'PART_FINAL': 0.0
        })
        
    tot_sal_actual = sum(r['SALDO ACTUAL'] for r in nuevos_registros)
    nueva_fecha_lunes = lunes_actual + timedelta(days=7)
    nueva_fecha_lunes_str = nueva_fecha_lunes.strftime('%Y-%m-%d')

    for i, r in enumerate(nuevos_registros):
        r['PART_FINAL'] = round((r['SALDO ACTUAL'] / tot_sal_actual * 100), 2) if tot_sal_actual > 0 else 0.0
        df_inv.at[i, 'SALDO INICIAL'] = r['SALDO ACTUAL']
        df_inv.at[i, 'FECHA_LUNES'] = nueva_fecha_lunes_str
        
    df_hist = pd.concat([df_hist[df_hist['SEMANA'] != semana_actual_label], pd.DataFrame(nuevos_registros)], ignore_index=True)
    
    guardar_en_storage(df_hist, 'historico_semanal.csv')
    guardar_en_storage(df_inv, 'inversionistas.csv')
    
    for nom in df_inv['INVERSIONISTA'].values:
        st.session_state.depositos_dict[nom] = 0.0
        st.session_state.retiros_dict[nom] = 0.0
        
    for key in list(st.session_state.keys()):
        if key.startswith("i_dep_") or key.startswith("i_ret_"):
            st.session_state[key] = 0.0

    st.success(f"🎉 ¡Semana cerrada con éxito! Proyección operativa: Lunes {nueva_fecha_lunes.strftime('%d-%m-%Y')}.")
    time.sleep(1)
    st.rerun()


# =========================================================================
# 🎛️ DESPLIEGUE DEL DASHBOARD CENTRAL
# =========================================================================
if semana_seleccionada != "Semana Activa (En Curso)":
    st.markdown(f"<div style='text-align:center;'><span style='background-color:#e2e8f0; color:#475569; padding:6px 16px; border-radius:20px; font-weight:bold; font-size:14px;'>📂 HISTÓRICO SELECCIONADO: {semana_seleccionada}</span></div><br>", unsafe_allow_html=True)
    df_filtrado = df_hist[df_hist['SEMANA'] == semana_seleccionada]
    
    df_vis_hist = pd.DataFrame()
    df_vis_hist['INVERSIONISTA'] = df_filtrado['INVERSIONISTA']
    df_vis_hist['CAPITAL ACUMULADO'] = df_filtrado['CAPITAL ACUMULADO'].apply(formatear_moneda)
    df_vis_hist['SALDO INICIAL'] = df_filtrado['SALDO INICIAL'].apply(formatear_moneda)
    df_vis_hist['% PARTICIPACION'] = df_filtrado['PART_INICIAL'].map('{:.2f}%'.format)
    df_vis_hist['SALDO FINAL'] = df_filtrado['SALDO FINAL'].apply(formatear_moneda)
    df_vis_hist['GANANCIA / PERDIDA'] = df_filtrado['GANANCIA / PERDIDA'].apply(formatear_moneda)
    df_vis_hist['DEPOSITOS'] = df_filtrado['DEPOSITOS'].apply(formatear_moneda)
    df_vis_hist['RETIROS'] = df_filtrado['RETIROS'].apply(formatear_moneda)
    df_vis_hist['SALDO ACTUAL'] = df_filtrado['SALDO ACTUAL'].apply(formatear_moneda)
    df_vis_hist['% PARTICIPACION FIN'] = df_filtrado['PART_FINAL'].map('{:.2f}%'.format)
    
    total_saldo_actual_hist = df_filtrado['SALDO ACTUAL'].sum()
    
    fila_tot_hist = pd.DataFrame([{
        'INVERSIONISTA': 'TOTAL FONDO', 'CAPITAL ACUMULADO': f"${df_filtrado['CAPITAL ACUMULADO'].sum():,.2f}",
        'SALDO INICIAL': f"${df_filtrado['SALDO INICIAL'].sum():,.2f}", '% PARTICIPACION': '100.00%',
        'SALDO FINAL': f"${df_filtrado['SALDO FINAL'].sum():,.2f}", 'GANANCIA / PERDIDA': f"${df_filtrado['GANANCIA / PERDIDA'].sum():,.2f}",
        'DEPOSITOS': f"${df_filtrado['DEPOSITOS'].sum():,.2f}", 'RETIROS': f"${df_filtrado['RETIROS'].sum():,.2f}",
        'SALDO ACTUAL': f"${total_saldo_actual_hist:,.2f}", '% PARTICIPACION FIN': '100.00%'
    }])
    
    df_final_despliegue_hist = pd.concat([df_vis_hist, fila_tot_hist], ignore_index=True)
    st.markdown(convertir_df_a_html_estilizado(df_final_despliegue_hist, es_tabla_resumen=False), unsafe_allow_html=True)
    
    df_res_hist = pd.DataFrame()
    df_res_hist['INVERSIONISTA'] = df_filtrado['INVERSIONISTA']
    df_res_hist['CAPITAL BASE HISTORICO'] = df_filtrado['CAPITAL ACUMULADO'].apply(formatear_moneda)
    df_res_hist['SALDO ACTUALIZADO'] = df_filtrado['SALDO ACTUAL'].apply(formatear_moneda)
    
    g_hist_tot = df_filtrado['SALDO ACTUAL'] - df_filtrado['CAPITAL ACUMULADO']
    df_res_hist['GANANCIA HISTORICA TOTAL'] = g_hist_tot.apply(formatear_moneda)
    df_res_hist['RETORNO (ROI)'] = (g_hist_tot / df_filtrado['CAPITAL ACUMULADO'] * 100).fillna(0.0).map('{:.2f}%'.format)
    
    fila_tot_res_hist = pd.DataFrame([{
        'INVERSIONISTA': 'TOTAL FONDO', 'CAPITAL BASE HISTORICO': f"${df_filtrado['CAPITAL ACUMULADO'].sum():,.2f}",
        'SALDO ACTUALIZADO': f"${total_saldo_actual_hist:,.2f}", 'GANANCIA HISTORICA TOTAL': f"${(total_saldo_actual_hist - df_filtrado['CAPITAL ACUMULADO'].sum()):,.2f}",
        'RETORNO (ROI)': f"{((total_saldo_actual_hist - df_filtrado['CAPITAL ACUMULADO'].sum()) / df_filtrado['CAPITAL ACUMULADO'].sum() * 100):,.2f}%"
    }])
    df_final_res_hist = pd.concat([df_res_hist, fila_tot_res_hist], ignore_index=True)
    
    st.markdown(f'<h3 class="titulo-tabla-centrado">Consolidado Histórico Semanal</h3>', unsafe_allow_html=True)
    st.markdown(convertir_df_a_html_estilizado(df_final_res_hist, es_tabla_resumen=True), unsafe_allow_html=True)
    
    fig_bar_current = generar_grafico_barras_dinamico(total_saldo_actual_hist)
    pdf_data = generar_pdf_reporte(df_final_despliegue_hist, semana_seleccionada, df_filtrado, df_final_res_hist, f"Consolidado a: {semana_seleccionada}", saldo_grafico_mayo=total_saldo_actual_hist)
    if pdf_data:
        st.download_button(label=f"📥 Descargar PDF Histórico: {semana_seleccionada}", data=pdf_data, file_name=f"Reporte_{semana_seleccionada.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)

else:
    st.markdown(f"<div style='text-align:center;'><span style='background-color:#d1fae5; color:#065f46; padding:6px 16px; border-radius:20px; font-weight:bold; font-size:14px;'>⚡ PERÍODO ACTIVO: Semana del {semana_actual_label}</span></div><br>", unsafe_allow_html=True)
    
    saldo_inicial_global_live = round(df_inv['SALDO INICIAL'].sum(), 2) 
    
    # Sincronización exacta espejo si no has colocado ningún valor superior a cero
    if saldo_cierre_mercado == 0.00:
        saldo_dinamico_mercado = saldo_inicial_global_live
    else:
        saldo_dinamico_mercado = saldo_cierre_mercado
        
    ganancia_global_live = round(saldo_dinamico_mercado - saldo_inicial_global_live, 2) 
    
    df_inv['PART_INICIAL_RATIO'] = df_inv['SALDO INICIAL'] / saldo_inicial_global_live
    df_inv['GANANCIA_TEORICA'] = ganancia_global_live * df_inv['PART_INICIAL_RATIO']
    df_inv['GANANCIA / PERDIDA'] = df_inv['GANANCIA_TEORICA'].round(2)
    
    diferencia_exacta_centavos = round(ganancia_global_live - df_inv['GANANCIA / PERDIDA'].sum(), 2)
    if diferencia_exacta_centavos != 0:
        idx_ajuste_centavo = (df_inv['GANANCIA_TEORICA'] - df_inv['GANANCIA / PERDIDA']).abs().idxmax()
        df_inv.at[idx_ajuste_centavo, 'GANANCIA / PERDIDA'] = round(df_inv.at[idx_ajuste_centavo, 'GANANCIA / PERDIDA'] + diferencia_exacta_centavos, 2)
        
    lista_filas_live = []
    for i, row in df_inv.iterrows():
        nom = row['INVERSIONISTA']
        p_ini = row['PART_INICIAL_RATIO'] * 100
        g_ind = row['GANANCIA / PERDIDA']
        
        lista_filas_live.append({
            'INVERSIONISTA': nom, 
            'CAPITAL ACUMULADO': row['CAPITAL ACUMULADO'], 
            'SALDO INICIAL': row['SALDO INICIAL'],
            '% PARTICIPACION': p_ini, 
            'SALDO FINAL': round(row['SALDO INICIAL'] + g_ind, 2), 
            'GANANCIA / PERDIDA': g_ind,
            'DEPOSITOS': st.session_state.depositos_dict.get(nom, 0.0), 
            'RETIROS': st.session_state.retiros_dict.get(nom, 0.0)
        })
        
    df_live_num = pd.DataFrame(lista_filas_live)
    df_live_num['SALDO ACTUAL'] = round(df_live_num['SALDO FINAL'] + df_live_num['DEPOSITOS'] - df_live_num['RETIROS'], 2)
    
    tot_s_actual_live = round(df_live_num['SALDO ACTUAL'].sum(), 2)
    df_live_num['PART_FINAL'] = (df_live_num['SALDO ACTUAL'] / tot_s_actual_live * 100) if tot_s_actual_live > 0 else 0.0

    # Despliegue de los bloques de la parte superior sincronizados
    st.markdown(
        f"""
        <div class="contenedor-metricas-global">
            <div class="tarjeta-metrica-custom">
                <div class="metrica-titulo-custom">💰 SALDO INICIAL TOTAL ({label_lunes_columna.upper()})</div>
                <div class="metrica-valor-custom">${saldo_inicial_global_live:,.2f}</div>
            </div>
            <div class="tarjeta-metrica-custom">
                <div class="metrica-titulo-custom">📈 SALDO ACTUAL CONSOLIDADO REAL ({label_domingo_columna.upper()})</div>
                <div class="metrica-valor-custom">${saldo_dinamico_mercado:,.2f}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    df_vis = pd.DataFrame()
    df_vis['INVERSIONISTA'] = df_live_num['INVERSIONISTA']
    df_vis['CAPITAL ACUMULADO'] = df_live_num['CAPITAL ACUMULADO'].apply(formatear_moneda)
    df_vis['SALDO INICIAL'] = df_live_num['SALDO INICIAL'].apply(formatear_moneda)
    df_vis['% PARTICIPACION'] = df_live_num['% PARTICIPACION'].map('{:.2f}%'.format)
    df_vis['SALDO FINAL'] = df_live_num['SALDO FINAL'].apply(formatear_moneda)
    df_vis['GANANCIA / PERDIDA'] = df_live_num['GANANCIA / PERDIDA'].apply(formatear_moneda)
    df_vis['DEPOSITOS'] = df_live_num['DEPOSITOS'].apply(formatear_moneda)
    df_vis['RETIROS'] = df_live_num['RETIROS'].apply(formatear_moneda)
    df_vis['SALDO ACTUAL'] = df_live_num['SALDO ACTUAL'].apply(formatear_moneda)
    df_vis['% PARTICIPACION FIN'] = df_live_num['PART_FINAL'].map('{:.2f}%'.format)
    
    fila_tot = pd.DataFrame([{
        'INVERSIONISTA': 'TOTAL FONDO', 'CAPITAL ACUMULADO': f"${df_inv['CAPITAL ACUMULADO'].sum():,.2f}",
        'SALDO INICIAL': f"${saldo_inicial_global_live:,.2f}", '% PARTICIPACION': '100.00%',
        'SALDO FINAL': f"${df_live_num['SALDO FINAL'].sum():,.2f}", 'GANANCIA / PERDIDA': formatear_moneda(ganancia_global_live),
        'DEPOSITOS': f"${df_live_num['DEPOSITOS'].sum():,.2f}", 'RETIROS': f"${df_live_num['RETIROS'].sum():,.2f}",
        'SALDO ACTUAL': f"${tot_s_actual_live:,.2f}", '% PARTICIPACION FIN': '100.00%'
    }])
    
    df_final_despliegue = pd.concat([df_vis, fila_tot], ignore_index=True)
    st.markdown(convertir_df_a_html_estilizado(df_final_despliegue, es_tabla_resumen=False), unsafe_allow_html=True)
    
    df_res_live = pd.DataFrame()
    df_res_live['INVERSIONISTA'] = df_live_num['INVERSIONISTA']
    df_res_live['CAPITAL BASE HISTORICO'] = df_live_num['CAPITAL ACUMULADO'].apply(formatear_moneda)
    df_res_live['SALDO ACTUALIZADO'] = df_live_num['SALDO ACTUAL'].apply(formatear_moneda)
    
    ganancia_historica_live = df_live_num['SALDO ACTUAL'] - df_live_num['CAPITAL ACUMULADO']
    df_res_live['GANANCIA HISTORICA TOTAL'] = ganancia_historica_live.apply(formatear_moneda)
    df_res_live['RETORNO (ROI)'] = (ganancia_historica_live / df_live_num['CAPITAL ACUMULADO'] * 100).fillna(0.0).map('{:.2f}%'.format)
    
    total_cap_base_live = df_live_num['CAPITAL ACUMULADO'].sum()
    total_ganancia_hist_live = tot_s_actual_live - total_cap_base_live
    
    fila_tot_res_live = pd.DataFrame([{
        'INVERSIONISTA': 'TOTAL FONDO', 'CAPITAL BASE HISTORICO': f"${total_cap_base_live:,.2f}",
        'SALDO ACTUALIZADO': f"${tot_s_actual_live:,.2f}", 'GANANCIA HISTORICA TOTAL': f"${total_ganancia_hist_live:,.2f}",
        'RETORNO (ROI)': f"{((total_ganancia_hist_live / total_cap_base_live * 100) if total_cap_base_live > 0 else 0.0):,.2f}%"
    }])
    df_final_res_live = pd.concat([df_res_live, fila_tot_res_live], ignore_index=True)
    
    titulo_dinamico = "Consolidado Acumulado Integral"
    st.markdown(f'<h3 class="titulo-tabla-centrado">{titulo_dinamico}</h3>', unsafe_allow_html=True)
    st.markdown(convertir_df_a_html_estilizado(df_final_res_live, es_tabla_resumen=True), unsafe_allow_html=True)
    
    fig_bar_current = generar_grafico_barras_dinamico(tot_s_actual_live)
    
    pdf_data = generar_pdf_reporte(df_final_despliegue, semana_actual_label, df_live_num, df_final_res_live, f"Consolidado a: {lunes_actual.strftime('%d-%m-%Y')}", saldo_grafico_mayo=tot_s_actual_live)
    if pdf_data:
        st.download_button(label=f"📥 Descargar PDF Oficial: Semana {semana_actual_label}", data=pdf_data, file_name=f"Reporte_Semanal_{semana_actual_label.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)

# --- GRÁFICOS ANALÍTICOS ---
st.markdown("---")
st.markdown("<h3 style='text-align: center;'>📊 Análisis y Métricas Visuales del Fondo</h3>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

if semana_seleccionada == "Semana Activa (En Curso)":
    st.plotly_chart(construir_grafico_pie(df_live_num), use_container_width=True)
else:
    st.plotly_chart(construir_grafico_pie(df_filtrado), use_container_width=True)

st.plotly_chart(fig_bar_current, use_container_width=True)