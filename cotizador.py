
import streamlit as st
from fpdf import FPDF
import datetime
import os
import pandas as pd

st.set_page_config(page_title="Cotizador MCSI", layout="centered")

# Logo y título
import os
if os.path.exists("logo_mcsi.png"):
    st.image("logo_mcsi.png", width=150)

st.markdown("<h2 style='text-align: center; color: #1b4f72;'>Cotizador de Renta de Maquinaria - MCSI</h2>", unsafe_allow_html=True)

st.write("Por favor llena los siguientes campos para generar tu cotización.")

# Formulario de datos del cliente
with st.form("form_cliente"):
    nombre = st.text_input("Nombre completo")
    correo = st.text_input("Correo electrónico")
    telefono = st.text_input("Teléfono")
    fecha_servicio = st.date_input("Fecha del servicio", datetime.date.today())
    hora_inicio = st.time_input("Hora de inicio", datetime.time(7, 0))
    duracion = st.number_input("Duración del servicio (horas)", min_value=1, max_value=24, value=4)

    equipos = st.multiselect("Selecciona el equipo requerido", [
        "Retroexcavadora", "Bailarina", "Camión de volteo", 
        "Compactador", "Generador", "Motoconformadora"
    ])

    submit = st.form_submit_button("Generar cotización")

# Reglas para horarios y costos
def es_dia_festivo(fecha):
    festivos = ["01-01", "05-02", "21-03", "01-05", "16-09", "20-11", "25-12"]
    return fecha.strftime("%d-%m") in festivos

def tipo_precio(fecha, hora):
    if fecha.weekday() == 6 or es_dia_festivo(fecha):
        return "Día Festivo"
    elif fecha.weekday() == 5 and hora.hour >= 12:
        return "Hora Extra"
    elif fecha.weekday() < 5 and hora.hour >= 16:
        return "Hora Extra"
    else:
        return "Normal"

# Folio automático
def generar_folio():
    archivo_folio = "folio.txt"
    if not os.path.exists(archivo_folio):
        with open(archivo_folio, "w") as f:
            f.write("0001")
        return "COT 0001"
    else:
        with open(archivo_folio, "r+") as f:
            actual = int(f.read())
            nuevo = actual + 1
            f.seek(0)
            f.write(str(nuevo).zfill(4))
            return f"COT {str(nuevo).zfill(4)}"

# PDF y base de datos
if submit and nombre and correo and telefono and equipos:
    folio = generar_folio()
    tipo = tipo_precio(fecha_servicio, hora_inicio)
    subtotal = len(equipos) * 1500 * (1.25 if tipo != "Normal" else 1)
    iva = subtotal * 0.08
    total = subtotal + iva

    fecha_str = fecha_servicio.strftime("%d/%m/%Y")
    hora_str = hora_inicio.strftime("%H:%M")

    # Generar PDF
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo_mcsi.png"):
        pdf.image("logo_mcsi.png", x=10, y=8, w=40)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Cotización de Renta de Maquinaria", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Folio: {folio}", ln=True)
    pdf.cell(0, 10, f"Fecha de solicitud: {datetime.date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(0, 10, f"Cliente: {nombre}", ln=True)
    pdf.cell(0, 10, f"Correo: {correo}", ln=True)
    pdf.cell(0, 10, f"Teléfono: {telefono}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, f"Fecha del servicio: {fecha_str}", ln=True)
    pdf.cell(0, 10, f"Hora de inicio: {hora_str}", ln=True)
    pdf.cell(0, 10, f"Duración estimada: {duracion} horas", ln=True)
    pdf.cell(0, 10, f"Tipo de tarifa aplicada: {tipo}", ln=True)
    pdf.ln(5)

    pdf.cell(0, 10, "Equipos solicitados:", ln=True)
    for equipo in equipos:
        pdf.cell(0, 10, f"- {equipo}", ln=True)

    pdf.ln(5)
    pdf.cell(0, 10, f"Subtotal: ${subtotal:,.2f}", ln=True)
    pdf.cell(0, 10, f"IVA (8%): ${iva:,.2f}", ln=True)
    pdf.cell(0, 10, f"Total: ${total:,.2f}", ln=True)

    if duracion > 10:
        pdf.ln(5)
        pdf.set_font("Arial", "I", 11)
        pdf.multi_cell(0, 10, "Nota: Por tratarse de un período de renta superior a 10 días, puede solicitar una propuesta ajustada según volumen. Nuestro equipo con gusto le atenderá para ofrecerle condiciones preferenciales.")

    pdf.output("cotizacion.pdf")

    with open("cotizacion.pdf", "rb") as f:
        st.download_button("📥 Descargar cotización en PDF", f, file_name="cotizacion.pdf", mime="application/pdf")

    # Guardar cliente en base de datos
    registro = {
        "Folio": folio,
        "Nombre": nombre,
        "Correo": correo,
        "Teléfono": telefono,
        "Fecha de servicio": fecha_str,
        "Hora": hora_str,
        "Equipos": ", ".join(equipos),
        "Total": total
    }

    if os.path.exists("clientes.csv"):
        df = pd.read_csv("clientes.csv")
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
    else:
        df = pd.DataFrame([registro])

    df.to_csv("clientes.csv", index=False)
    st.success("Cotización generada y guardada correctamente.")
