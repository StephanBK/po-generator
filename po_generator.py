from fpdf import FPDF
import pandas as pd
from datetime import datetime
import streamlit as st
import os

st.set_page_config(page_title="PO Generator", layout="centered")
st.title("PO Generator")

uploaded_file = st.file_uploader("Upload the Glass Excel File", type=["xlsx"])

# Collect user inputs
st.subheader("Purchase Order Details")
po_number = st.text_input("PO Number", "03028")
po_date = st.date_input("PO Date", datetime.today()).strftime("%m/%d/%Y")
requisitioner = st.text_input("Requisitioner", "DD")
job_no = st.text_input("Job Number", "ENVD")
job_location = st.text_input("Job Location", "Boulder, CO")
to_name = st.text_input("Recipient Name", "Jeff Henry")
to_email = st.text_input("Recipient Email", "jhenry@nxlite.com")
lead_time = st.text_input("Lead Time", "4 weeks")
ship_via = st.text_input("Shipped Via", "Ground")
terms = st.text_input("Terms", "50% delivery by 7/18")
price_per_sqft = st.number_input("Price per Square Foot", value=6.45, step=0.01)

# Cost summary inputs
sales_tax = st.number_input("Sales Tax ($)", value=0.00, step=0.01)
packaging = st.number_input("Packaging ($)", value=0.00, step=0.01)
shipping = st.number_input("Shipping & Handling ($)", value=0.00, step=0.01)

if uploaded_file and st.button("Generate PO PDF"):
    df = pd.read_excel(uploaded_file, sheet_name="Glass", skiprows=10)
    df.columns = [
        "Item", "Width (in)", "Width (frac)", "Height (in)", "Height (frac)",
        "Area Each (ft²)", "Qty", "Area Total (ft²)"
    ]
    df = df[df["Item"].apply(pd.to_numeric, errors='coerce').notnull()]
    df["Width (in)"] = df["Width (in)"].astype(float)
    df["Height (in)"] = df["Height (in)"].astype(float)
    df["Qty"] = df["Qty"].astype(int)
    df["Area Each (ft²)"] = df["Area Each (ft²)"].astype(float)
    df["Area Total (ft²)"] = df["Area Total (ft²)"].astype(float)
    df["Total Price"] = df["Area Total (ft²)"] * price_per_sqft

    subtotal = df["Total Price"].sum()
    total = subtotal + sales_tax + packaging + shipping

    pdf = FPDF()
    pdf.set_auto_page_break(auto=False, margin=15)
    pdf.add_page()

    # Add logo
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=10, w=40)

    # Title
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, "PURCHASE ORDER", ln=True, align="C")
    pdf.ln(15)

    # Address columns
    col_width = 65
    spacing = 10
    pdf.set_font("Arial", "B", 10)
    pdf.cell(col_width, 6, "TO:", ln=0)
    pdf.cell(spacing)
    pdf.cell(col_width, 6, "SHIP TO:", ln=0)
    pdf.cell(spacing)
    pdf.cell(col_width, 6, "BILL TO:", ln=1)

    pdf.set_font("Arial", "", 7.5)  # smaller font here
    to_lines = [to_name, to_email, f"JOB NO.: {job_no}", f"JOB LOCATION: {job_location}"]
    ship_to_lines = ["Momentum Glass, LLC", "Attn: INOVUES, INC.", "25825 Aldine Westfield Rd.", "Spring, TX 77373", "281.809.2830"]
    bill_to_lines = ["INOVUES, INC.", "2700 Post Oak Blvd., 2100", "Houston, TX 77056", "accounts@inovues.com", "(833) 466-8837 (INO-VUES)"]

    for i in range(max(len(to_lines), len(ship_to_lines), len(bill_to_lines))):
        pdf.cell(col_width, 5, to_lines[i] if i < len(to_lines) else "", ln=0)
        pdf.cell(spacing)
        pdf.cell(col_width, 5, ship_to_lines[i] if i < len(ship_to_lines) else "", ln=0)
        pdf.cell(spacing)
        pdf.cell(col_width, 5, bill_to_lines[i] if i < len(bill_to_lines) else "", ln=1)

    pdf.ln(4)

    # Summary info
    summary_headers = ["PO DATE", "PO NUMBER", "REQUISITIONER", "LEAD TIME", "SHIPPED VIA", "TERMS"]
    summary_values = [po_date, po_number, requisitioner, lead_time, ship_via, terms]
    summary_widths = [30, 30, 30, 30, 30, 40]

    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 10)
    for i, h in enumerate(summary_headers):
        pdf.cell(summary_widths[i], 8, h, 1, 0, "C", fill=True)
    pdf.ln()

    pdf.set_font("Arial", "", 10)
    for i, val in enumerate(summary_values):
        pdf.cell(summary_widths[i], 8, val, 1, 0)
    pdf.ln(9)

    # Line items
    headers = ["ITEM#", "DESCRIPTION", "UNIT SIZE", "UNIT AREA", "QTY", "TOTAL AREA", "PRICE", "TOTAL"]
    widths = [15, 30, 30, 25, 12, 24, 20, 34]  # Slightly adjusted
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 10)
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 8, h, 1, 0, "C", fill=True)
    pdf.ln()

    pdf.set_font("Arial", "", 9)
    for _, row in df.iterrows():
        pdf.cell(widths[0], 8, str(int(row["Item"])), 1)
        pdf.cell(widths[1], 8, "Glass unit", 1)
        size_str = f'{row["Width (in)"]:.3f}" x {row["Height (in)"]:.3f}"'
        pdf.cell(widths[2], 8, size_str, 1)
        pdf.cell(widths[3], 8, f'{row["Area Each (ft²)"]:.2f}', 1, 0, "R")
        pdf.cell(widths[4], 8, str(int(row["Qty"])), 1, 0, "R")
        pdf.cell(widths[5], 8, f'{row["Area Total (ft²)"]:.1f}', 1, 0, "R")
        pdf.cell(widths[6], 8, f'${price_per_sqft:.2f}', 1, 0, "R")
        pdf.cell(widths[7], 8, f'${row["Total Price"]:.2f}', 1, 0, "R")
        pdf.ln()

    def cost_row(label, amount):
        pdf.set_font("Arial", "", 10)
        pdf.cell(sum(widths[:-1]), 8, label, 1)
        pdf.cell(widths[-1], 8, f"${amount:.2f}", 1, 1, "R")

    pdf.set_font("Arial", "B", 10)
    cost_row("SUBTOTAL", subtotal)
    cost_row("SALES TAX", sales_tax)
    cost_row("PACKAGING", packaging)
    cost_row("SHIPPING & HANDLING", shipping)
    cost_row("TOTAL", total)

    pdf.ln(5)
    pdf.set_font("Arial", "", 7)
    disclaimers = [
        "1. Enter this order in accordance with the prices, terms, delivery method, and specifications listed in this purchase order.",
        "2. Please notify us immediately if you are unable to ship as specified.",
        "3. Send all correspondence to: INOVUES, INC., 2700 Post Oak Blvd, 2100, Houston, TX 77056 | (833) 466-8837 | accounts@inovues.com"
    ]
    for line in disclaimers:
        pdf.multi_cell(0, 4.5, line)

    pdf.ln(3)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 8, f"Authorized by _____________________ {po_date}", ln=True)

    pdf.ln(3)
    pdf.set_font("Arial", "", 7)
    pdf.cell(0, 4.5, "INOVUES, INC. | 2700 Post Oak Blvd, 2100, Houston, TX 77056 | (833) 466-8837 | www.inovues.com | info@inovues.com", ln=True, align="C")

    output_path = "Generated_PO.pdf"
    pdf.output(output_path)
    with open(output_path, "rb") as f:
        st.success("PDF successfully generated!")
        st.download_button("Download PO PDF", data=f, file_name=f"PO_{po_number}.pdf", mime="application/pdf")
