import streamlit as st
import zipfile
import os
from docx import Document
from datetime import datetime

st.set_page_config(page_title="Lineify - Arizona Lien Waiver Automation")

st.title("Lineify Arizona Lien Waiver Automation")
st.write("Select your state, fill out the form, and generate the correct lien waiver document.")

# --- Step 0: Extract Templates from ZIP ---
zip_path = "02_Templates-20251119T041237Z-1-001.zip"
extract_folder = "02_Templates"

if not os.path.exists(extract_folder):
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)
    else:
        st.error(f"ZIP file not found: {zip_path}")
        st.stop()

# --- Step 1: Pre-Data Collection Form ---
st.header("Pre-Data Collection Form - Arizona")

# Step 0: Client Pre-Screening
state_project = st.radio("Are you working on a construction project in Arizona?", ["Yes", "No"])
if state_project == "No":
    st.warning("Arizona statutory lien waivers are only valid for Arizona projects.")
    st.stop()

role = st.selectbox("What is your role on this project?", ["Contractor", "Subcontractor", "Supplier", "Material Provider"])
payment_type = st.radio("Is this waiver for a progress payment or a final payment?", ["Progress", "Final"])
payment_received = st.radio("Has payment been received yet for this waiver?", ["Yes", "No"])

# Step 1: Detailed Data Collection
st.subheader("Detailed Project / Payment Info")
OwnerName = st.text_input("Property Owner Name")
ProjectAddress = st.text_input("Project Address")
CustomerName = st.text_input("Customer / Paying Entity Name")
LienorName = st.text_input("Lienor / Contractor Name")
PaymentAmount = st.number_input("Payment Amount", min_value=0.0, format="%.2f")
WorkThroughDate = st.date_input("Work Through Date (required for progress waiver)") if payment_type == "Progress" else None
ExecutionDate = st.date_input("Execution Date", value=datetime.today())
AuthorizedRep = st.text_input("Authorized Representative / Signatory")
JobNumber = st.text_input("Project / Job Number")
PropertyDescription = st.text_area("Description of Property / Job")

# Determine conditional/unconditional
ConditionalOnPayment = "No" if payment_received == "Yes" else "Yes"

# Validation
if PaymentAmount <= 0:
    st.error("Payment amount must be greater than 0.")
    st.stop()

if payment_type == "Final" and WorkThroughDate and WorkThroughDate > ExecutionDate:
    st.error("For final payment, Work Through Date cannot be after Execution Date.")
    st.stop()

# --- Step 2: Select Correct Template ---
template_folder = os.path.join(extract_folder, "Arizona")
template_map = {
    ("Progress", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.docx",
    ("Progress", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.docx",
    ("Final", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.docx",
    ("Final", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.docx",
}

selected_template = template_map[(payment_type, ConditionalOnPayment)]
template_path = os.path.join(template_folder, selected_template)

if not os.path.exists(template_path):
    st.error(f"Template not found: {selected_template}")
    st.stop()

# --- Step 3: Fill Template ---
def fill_template(doc_path, placeholders):
    doc = Document(doc_path)
    for p in doc.paragraphs:
        for key, value in placeholders.items():
            if key in p.text:
                p.text = p.text.replace(key, value)
    return doc

placeholders = {
    "{{OwnerName}}": OwnerName,
    "{{ProjectAddress}}": ProjectAddress,
    "{{CustomerName}}": CustomerName,
    "{{LienorName}}": LienorName,
    "{{PaymentAmount}}": f"${PaymentAmount:,.2f}",
    "{{WorkThroughDate}}": WorkThroughDate.strftime("%B %d, %Y") if WorkThroughDate else "",
    "{{ExecutionDate}}": ExecutionDate.strftime("%B %d, %Y"),
    "{{AuthorizedRep}}": AuthorizedRep,
    "{{JobNumber}}": JobNumber,
    "{{PropertyDescription}}": PropertyDescription,
    "{{ConditionalOnPayment}}": ConditionalOnPayment
}

filled_doc = fill_template(template_path, placeholders)

# --- Step 4: Save & Download ---
output_filename = f"AZ_{'Conditional' if ConditionalOnPayment=='Yes' else 'Unconditional'}_{payment_type}_{datetime.today().strftime('%Y%m%d')}.docx"
filled_doc.save(output_filename)

st.success(f"Document generated: {output_filename}")
with open(output_filename, "rb") as f:
    st.download_button(
        label="Download Lien Waiver",
        data=f,
        file_name=output_filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
