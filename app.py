import streamlit as st
from docx import Document
import pandas as pd
import os
import zipfile

st.title("Lineify – Arizona Lien Waiver Automation")

# ------------------------------
# 1. Unzip templates if needed
# ------------------------------
zip_path = "templates.zip"  # your uploaded zip
extract_path = "templates"

if not os.path.exists(extract_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

template_folder = os.path.join(extract_path, "02_Templates/Arizona/")

# ------------------------------
# 2. Template mapping
# ------------------------------
template_map = {
    ("Progress", "Conditional"): "CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Progress", "Unconditional"): "UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Final", "Conditional"): "CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
    ("Final", "Unconditional"): "UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf"
}

# ------------------------------
# 3. Collect user input
# ------------------------------
st.header("Step 0: Pre-Data Collection")

payment_type = st.radio("Is this waiver for a progress payment or a final payment?", ["Progress", "Final"])
payment_received = st.radio("Has payment been received yet for this waiver?", ["Yes", "No"])

conditional_on_payment = "No" if payment_received == "Yes" else "Yes"

st.header("Step 1: Detailed Data Collection")
OwnerName = st.text_input("Property Owner Name", "")
ProjectAddress = st.text_input("Property / Job Address", "")
CustomerName = st.text_input("Customer / Paying Entity Name", "")
LienorName = st.text_input("Lienor / Contractor Name", "")
PaymentAmount = st.text_input("Payment Amount", "")
WorkThroughDate = st.text_input("Work Through Date (for progress waiver)", "")
JobNumber = st.text_input("Job / Project Number", "")
PropertyDescription = st.text_input("Description of Property / Job", "")
ExecutionDate = st.text_input("Date of waiver execution", "")
AuthorizedRep = st.text_input("Authorized Representative / Signatory", "")

# ------------------------------
# 4. Fill the template
# ------------------------------
def fill_word_template(template_path, placeholders):
    doc = Document(template_path)
    for p in doc.paragraphs:
        for key, val in placeholders.items():
            if key in p.text:
                p.text = p.text.replace(key, str(val))
    # Also replace in tables if needed
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, val in placeholders.items():
                    if key in cell.text:
                        cell.text = cell.text.replace(key, str(val))
    return doc

# ------------------------------
# 5. Generate filled waiver
# ------------------------------
if st.button("Generate Waiver"):
    if not OwnerName or not ProjectAddress or not CustomerName or not LienorName or not PaymentAmount:
        st.error("Please fill in all required fields.")
    else:
        selected_template = template_map[(payment_type, "Conditional" if conditional_on_payment=="Yes" else "Unconditional")]
        template_path = os.path.join(template_folder, selected_template)
        
        placeholders = {
            "{{OwnerName}}": OwnerName,
            "{{ProjectAddress}}": ProjectAddress,
            "{{CustomerName}}": CustomerName,
            "{{LienorName}}": LienorName,
            "{{PaymentAmount}}": PaymentAmount,
            "{{WorkThroughDate}}": WorkThroughDate,
            "{{ExecutionDate}}": ExecutionDate,
            "{{AuthorizedRep}}": AuthorizedRep,
            "{{JobNumber}}": JobNumber,
            "{{PropertyDescription}}": PropertyDescription,
            "{{ConditionalOnPayment}}": conditional_on_payment
        }

        filled_doc = fill_word_template(template_path, placeholders)
        
        output_file = f"AZ_{'Conditional' if conditional_on_payment=='Yes' else 'Unconditional'}_{payment_type}_{ExecutionDate.replace('/', '-')}.docx"
        filled_doc.save(output_file)
        
        st.success("Waiver generated successfully!")
        st.download_button("Download Waiver", open(output_file, "rb"), file_name=output_file)
