import streamlit as st
from docx import Document
from io import BytesIO

st.set_page_config(page_title="Lienify Arizona Waiver Generator", layout="wide")
st.title("Lineify - Arizona Lien Waiver Generator")

# -------------------------
# Step 0: Pre-Screening
# -------------------------
st.header("Step 0: Pre-Screening")

is_arizona = st.radio(
    "Are you working on a construction project in Arizona?",
    ("Yes", "No")
)

if is_arizona == "No":
    st.warning("Arizona statutory lien waivers are only valid for Arizona projects.")
    st.stop()

role = st.selectbox(
    "Your role on this project",
    ["Contractor", "Subcontractor", "Supplier", "Material Provider"]
)

payment_type = st.radio("Is this waiver for a Progress or Final payment?", ("Progress", "Final"))

payment_received = st.radio("Has payment been received yet for this waiver?", ("Yes", "No"))

# Determine conditional vs unconditional
conditional_on_payment = "No" if payment_received == "Yes" else "Yes"

# -------------------------
# Step 1: Detailed Data Collection
# -------------------------
st.header("Step 1: Detailed Data Collection")

owner_name = st.text_input("Property Owner Name ({{OwnerName}})")
project_address = st.text_input("Property / Job Address ({{ProjectAddress}})")
customer_name = st.text_input("Customer / Paying Entity Name ({{CustomerName}})")
lienor_name = st.text_input("Lienor / Contractor Name ({{LienorName}})")
payment_amount = st.text_input("Payment Amount ({{PaymentAmount}})")
work_through_date = st.text_input("Work Through Date (for Progress Payment) ({{WorkThroughDate}})")
job_number = st.text_input("Job / Project Number ({{JobNumber}})")
property_description = st.text_input("Description of Property / Job ({{PropertyDescription}})")
execution_date = st.text_input("Date of Waiver Execution ({{ExecutionDate}})")
authorized_rep = st.text_input("Authorized Representative / Signatory ({{AuthorizedRep}})")

# Validation
if payment_type == "Progress" and not work_through_date:
    st.warning("Work Through Date is required for Progress Payments.")
    st.stop()

# -------------------------
# Step 2: Select Template
# -------------------------
st.header("Step 2: Generate Waiver")

template_folder = "templates/Arizona/"

# Mapping
template_map = {
    ("Progress", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Progress", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Final", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
    ("Final", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
}

selected_template = template_map[(payment_type, conditional_on_payment)]

# -------------------------
# Step 3: Merge Placeholders
# -------------------------
def fill_docx_template(template_path, placeholders):
    doc = Document(template_path)
    for paragraph in doc.paragraphs:
        for key, value in placeholders.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, value)
    # Also replace in tables if needed
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, value in placeholders.items():
                    if key in cell.text:
                        cell.text = cell.text.replace(key, value)
    return doc

placeholders = {
    "{{OwnerName}}": owner_name,
    "{{ProjectAddress}}": project_address,
    "{{CustomerName}}": customer_name,
    "{{LienorName}}": lienor_name,
    "{{PaymentAmount}}": payment_amount,
    "{{WorkThroughDate}}": work_through_date,
    "{{JobNumber}}": job_number,
    "{{PropertyDescription}}": property_description,
    "{{ExecutionDate}}": execution_date,
    "{{AuthorizedRep}}": authorized_rep,
    "{{ConditionalOnPayment}}": conditional_on_payment
}

template_path = template_folder + selected_template
filled_doc = fill_docx_template(template_path, placeholders)

# Save in memory
output_stream = BytesIO()
filled_doc.save(output_stream)
output_stream.seek(0)

st.success(f"Template Selected: {selected_template}")
st.download_button(
    label="Download Filled Waiver",
    data=output_stream,
    file_name=selected_template,
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
