import streamlit as st
import zipfile
import os
import tempfile
from docx import Document

# ---------------------------------------------------------
# PAGE TITLE + HEADER
# ---------------------------------------------------------
st.set_page_config(page_title="Lienify - Arizona Lien Waiver Automation", layout="wide")

st.markdown("""
# **Lienify – Arizona Lien Waiver Automation**  
### *Prototype by Muhammad Umar Irfan*
---
""")

# ---------------------------------------------------------
# UNZIP THE TEMPLATE FOLDER AUTOMATICALLY
# ---------------------------------------------------------
ZIP_FILE_NAME = "02_Templates-20251119T041237Z-1-001.zip"

if not os.path.exists(ZIP_FILE_NAME):
    st.error(f"Template ZIP file not found: {ZIP_FILE_NAME}")
    st.stop()

# Extract zip to temporary working dir
temp_dir = tempfile.mkdtemp()

with zipfile.ZipFile(ZIP_FILE_NAME, 'r') as zip_ref:
    zip_ref.extractall(temp_dir)

# Arizona folder path (auto-detect)
AZ_FOLDER = None
for root, dirs, files in os.walk(temp_dir):
    if "Arizona" in root or "AZ" in root:
        AZ_FOLDER = root
        break

if not AZ_FOLDER:
    st.error("Could not locate Arizona template folder inside ZIP.")
    st.stop()

# ---------------------------------------------------------
# LOCATE THE FOUR TEMPLATES (DOCX files named as .pdf)
# ---------------------------------------------------------
def find_template(name):
    """
    Because your files are DOCX but named .pdf,
    we scan for files containing the name regardless of extension.
    """
    for file in os.listdir(AZ_FOLDER):
        if name.replace(".docx", "").replace(".pdf", "").lower() in file.lower():
            return os.path.join(AZ_FOLDER, file)
    return None

TEMPLATE_PROGRESS_CONDITIONAL = find_template("CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT")
TEMPLATE_PROGRESS_UNCONDITIONAL = find_template("UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT")
TEMPLATE_FINAL_CONDITIONAL = find_template("CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT")
TEMPLATE_FINAL_UNCONDITIONAL = find_template("UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT")

templates_map = {
    "progress_yes": TEMPLATE_PROGRESS_CONDITIONAL,
    "progress_no": TEMPLATE_PROGRESS_UNCONDITIONAL,
    "final_yes": TEMPLATE_FINAL_CONDITIONAL,
    "final_no": TEMPLATE_FINAL_UNCONDITIONAL,
}

# ---------------------------------------------------------
# PRE–SCREENING UI (Matches Your Developer Logic Form)
# ---------------------------------------------------------
st.subheader("Arizona Project Pre-Screening")

project_state = st.radio("Are you working on a construction project in Arizona?", ["Yes", "No"])

if project_state == "No":
    st.warning("Arizona statutory lien waivers are only valid for Arizona projects.")
    st.stop()

role = st.selectbox("Your role:", ["Contractor", "Subcontractor", "Supplier", "Material Provider"])

payment_type = st.radio("Is this for a progress payment or a final payment?", ["Progress", "Final"])

payment_received = st.radio("Has payment been received?", ["Yes", "No"])

# Determine template key
key = payment_type.lower() + "_" + ("no" if payment_received == "Yes" else "yes")
template_file = templates_map.get(key)

if not template_file:
    st.error("Template not found based on your selections.")
    st.stop()

st.success(f"Template selected: **{os.path.basename(template_file)}**")

# ---------------------------------------------------------
# DETAILED DATA COLLECTION
# ---------------------------------------------------------
st.subheader("Detailed Waiver Information")

OwnerName = st.text_input("Owner Name")
ProjectAddress = st.text_input("Property / Job Address")
CustomerName = st.text_input("Customer / Paying Entity Name")
LienorName = st.text_input("Lienor / Contractor / Provider Name")

# Dollar sign added automatically
PaymentAmount = st.text_input("Payment Amount", placeholder="$25,000.00")

WorkThroughDate = None
if payment_type == "Progress":
    WorkThroughDate = st.text_input("Work Through Date (Progress Waiver Only)", placeholder="November 1, 2025")

JobNumber = st.text_input("Project Job Number")
PropertyDescription = st.text_area("Property / Job Description", height=80)

ConditionalOnPayment = "No" if payment_received == "Yes" else "Yes"

ExecutionDate = st.text_input("Execution Date", placeholder="Nov 7, 2025")
AuthorizedRep = st.text_input("Authorized Representative / Signatory Name")

# Arizona-specific compliance note (required per your sheet)
st.info("""
### Arizona Compliance Reminder  
• Preliminary Notice must be sent **within 20 days of first delivery**  
• Unconditional waivers become binding *when signed*  
• Conditional waivers become binding *when payment evidence exists*  
• Waiving lien rights before performing work is illegal  
""")

# ---------------------------------------------------------
# GENERATE DOCUMENT
# ---------------------------------------------------------
def replace_tags(doc, mapping):
    """Replace {{tags}} in a .docx document."""
    for paragraph in doc.paragraphs:
        for key, val in mapping.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, val)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, val in mapping.items():
                    if key in cell.text:
                        cell.text = cell.text.replace(key, val)

st.subheader("Generate Arizona Lien Waiver")

if st.button("Generate Document"):
    if not os.path.exists(template_file):
        st.error("Template file missing.")
        st.stop()

    # Load DOCX template (even though named .pdf)
    doc = Document(template_file)

    data_map = {
        "{{OwnerName}}": OwnerName,
        "{{ProjectAddress}}": ProjectAddress,
        "{{CustomerName}}": CustomerName,
        "{{LienorName}}": LienorName,
        "{{PaymentAmount}}": PaymentAmount,
        "{{WorkThroughDate}}": WorkThroughDate or "",
        "{{JobNumber}}": JobNumber,
        "{{PropertyDescription}}": PropertyDescription,
        "{{ConditionalOnPayment}}": ConditionalOnPayment,
        "{{ExecutionDate}}": ExecutionDate,
        "{{AuthorizedRep}}": AuthorizedRep,
    }

    replace_tags(doc, data_map)

    # Save output
    output_path = os.path.join(temp_dir, f"Lienify_{payment_type}_{ConditionalOnPayment}.docx")
    doc.save(output_path)

    st.success("Arizona lien waiver generated successfully!")

    with open(output_path, "rb") as f:
        st.download_button(
            label="Download Completed Lien Waiver",
            data=f,
            file_name=os.path.basename(output_path),
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.markdown("""
---
#### © Lienify — Prototype by **Muhammad Umar Irfan**
""")
