# app.py
import streamlit as st
from zipfile import ZipFile
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
from io import BytesIO

# ---------------- Configuration ----------------
TEMPLATES_ZIP_PATH = "./02_Templates-20251119T041237Z-1-001.zip"
ARIZONA_FOLDER_NAME = "Arizona Templates"

# Map for template selection: (Payment Type, Payment Received Yes/No)
TEMPLATE_FILENAME_MAP = {
    ("Progress", False): "CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Progress", True):  "UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Final", False):    "CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
    ("Final", True):     "UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
}

# ---------------- Session State Init ----------------
def init_session():
    if "step" not in st.session_state:
        st.session_state.step = 0
    defaults = {
        "state": "",
        "compliance_ack": False,
        "role": "",
        "payment_type": "",
        "payment_received": "",
        "first_delivery_date": None,
        "project_name": "",
        "project_address": "",
        "owner_name": "",
        "contractor_name": "",
        "payment_amount_raw": "",
        "invoice_number": "",
        "job_description": "",
        "job_start_date": None,
        "job_end_date": None,
        "generated_file_bytes": None,
        "generated_filename": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ---------------- Helpers ----------------
def currency_format(raw_str):
    if not raw_str:
        return "$0.00"
    try:
        val = float(raw_str)
        return f"${val:,.2f}"
    except:
        return f"${raw_str}"

def safe_filename(text):
    return "".join(c for c in text if c.isalnum() or c in "_- .").replace(" ", "_")

def step_navigation(can_go_next=True):
    cols = st.columns([1, 1, 1])
    with cols[0]:
        if st.button("Back", key=f"back_btn_{st.session_state.step}"):
            st.session_state.step = max(0, st.session_state.step - 1)
            st.rerun()
    with cols[2]:
        if st.button("Next", key=f"next_btn_{st.session_state.step}", disabled=not can_go_next):
            st.session_state.step += 1
            st.rerun()
    st.write("")
    st.markdown("---")

# ---------------- Template Extraction ----------------
def extract_template_from_zip(zip_path: str, template_relpath: str, extract_to: str):
    template_basename = Path(template_relpath).stem.lower()  # ignore extension
    with ZipFile(zip_path, "r") as z:
        matched_file = None
        for name in z.namelist():
            if Path(name).stem.lower() == template_basename:
                matched_file = name
                break
        if not matched_file:
            all_files = "\n".join(z.namelist())
            raise FileNotFoundError(
                f"Could not find template {template_basename} in {zip_path}. Files in zip:\n{all_files}"
            )
        z.extract(matched_file, path=extract_to)
        return Path(extract_to) / matched_file

def generate_document():
    payment_type = st.session_state.payment_type
    unconditional = True if st.session_state.payment_received == "Yes" else False
    key = (payment_type, unconditional)
    template_filename = TEMPLATE_FILENAME_MAP[key]
    template_relpath = f"{ARIZONA_FOLDER_NAME}/{template_filename}"
    tmpdir = tempfile.mkdtemp()
    try:
        extracted_file = extract_template_from_zip(TEMPLATES_ZIP_PATH, template_relpath, tmpdir)
        # Read as bytes
        with open(extracted_file, "rb") as f:
            file_bytes = f.read()
        conditional_text = "Unconditional" if unconditional else "Conditional"
        date_part = datetime.now().strftime("%Y%m%d")
        out_filename = f"Lienify_AZ_{payment_type}_{conditional_text}_{date_part}.docx"
        out_filename = safe_filename(out_filename)
        return file_bytes, out_filename
    finally:
        try:
            shutil.rmtree(tmpdir)
        except:
            pass

# ---------------- Step Functions ----------------
def step_welcome():
    st.header("Welcome to Lienify Waiver and Lien Form Generator")
    st.caption("Step-by-step generator for Arizona waiver & release forms")
    if st.button("Select State"):
        st.session_state.step = 1
        st.rerun()
    st.markdown("---")

def step_state_selection():
    st.header("State Selection")
    st.caption("Currently, only Arizona templates are active.")
    state = st.selectbox("Choose your state", ["-- Select --", "Arizona", "Other"], key="state_select")
    st.session_state.state = state
    if state == "Arizona":
        st.success("Arizona selected.")
        if st.button("Proceed to Compliance"):
            st.session_state.step = 2
            st.rerun()
        step_navigation(True)
    elif state == "Other":
        st.warning("Only Arizona templates are available in this prototype.")
        step_navigation(False)
    else:
        step_navigation(False)

def step_compliance():
    st.header("Arizona Compliance Summary")
    st.caption("Important compliance notes for Arizona lien/waiver forms.")
    st.markdown(
        """
        Arizona has specific rules for construction waivers/releases.
        Generated documents should be verified for accuracy.
        """
    )
    if st.button("Yes, I understand, please proceed"):
        st.session_state.compliance_ack = True
        st.session_state.step = 3
        st.rerun()
    step_navigation(can_go_next=st.session_state.compliance_ack)

def step_prescreen_role():
    st.header("Pre-screening — Role")
    role = st.selectbox("Your role", ["", "Owner", "Contractor", "Subcontractor", "Supplier", "Other"], key="role_select")
    st.session_state.role = role
    if role:
        step_navigation(True)
    else:
        step_navigation(False)

def step_prescreen_payment_type():
    st.header("Pre-screening — Payment Type")
    payment_type = st.radio("Payment Type", ["Progress", "Final"], key="payment_type")
    st.session_state.payment_type = payment_type
    step_navigation(True)

def step_prescreen_payment_received():
    st.header("Pre-screening — Payment Received")
    received = st.radio("Payment Received?", ["Yes", "No"], key="payment_received")
    st.session_state.payment_received = received
    step_navigation(True)

def step_prescreen_first_delivery():
    st.header("Pre-screening — First Delivery Date")
    first_date = st.date_input("First delivery date", key="first_delivery_date")
    st.session_state.first_delivery_date = first_date
    step_navigation(True)

def step_project_payment_details():
    st.header("Project & Payment Details")
    st.text_input("Project name", key="project_name")
    st.text_input("Project address", key="project_address")
    st.text_input("Owner name", key="owner_name")
    st.text_input("Contractor name", key="contractor_name")
    st.text_input("Invoice number", key="invoice_number")
    st.text_input("Payment amount", key="payment_amount_raw")
    st.date_input("Job start date", key="job_start_date")
    st.date_input("Job end date", key="job_end_date")
    st.text_area("Job description", key="job_description", height=100)
    fields_filled = all([
        st.session_state.project_name,
        st.session_state.project_address,
        st.session_state.owner_name,
        st.session_state.contractor_name,
        st.session_state.invoice_number,
        st.session_state.payment_amount_raw,
        st.session_state.job_start_date,
        st.session_state.job_end_date,
        st.session_state.job_description
    ])
    if not fields_filled:
        st.warning("Please complete all required fields to proceed.")
    step_navigation(fields_filled)

def step_review_and_generate():
    st.header("Review Details Before Generating")
    st.write(f"**Project:** {st.session_state.project_name}")
    st.write(f"**Owner:** {st.session_state.owner_name}")
    st.write(f"**Contractor:** {st.session_state.contractor_name}")
    st.write(f"**Payment Type:** {st.session_state.payment_type}")
    st.write(f"**Payment Received:** {st.session_state.payment_received}")
    st.write(f"**Amount:** {currency_format(st.session_state.payment_amount_raw)}")
    st.write(f"**Invoice:** {st.session_state.invoice_number}")
    st.write(f"**Job Start:** {st.session_state.job_start_date}")
    st.write(f"**Job End:** {st.session_state.job_end_date}")
    st.write(f"**First Delivery:** {st.session_state.first_delivery_date}")
    st.write(f"**Job Description:** {st.session_state.job_description}")
    st.markdown("---")
    if st.button("Generate Document"):
        with st.spinner("Please wait, generating your form..."):
            try:
                file_bytes, filename = generate_document()
                st.session_state.generated_file_bytes = file_bytes
                st.session_state.generated_filename = filename
                st.success("Document generated successfully.")
                st.session_state.step += 1
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate document: {e}")
    step_navigation(True)

def step_download():
    st.header("Download Your Generated Form")
    if st.session_state.generated_file_bytes and st.session_state.generated_filename:
        st.download_button(
            "Download Document",
            data=st.session_state.generated_file_bytes,
            file_name=st.session_state.generated_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        st.warning("No document available. Go back and generate the form.")
    step_navigation(False)

# ---------------- Main ----------------
def main():
    st.set_page_config(page_title="Lienify Waiver & Lien Generator", page_icon="🧾", layout="centered")
    init_session()

    steps = [
        step_welcome,
        step_state_selection,
        step_compliance,
        step_prescreen_role,
        step_prescreen_payment_type,
        step_prescreen_payment_received,
        step_prescreen_first_delivery,
        step_project_payment_details,
        step_review_and_generate,
        step_download
    ]

    if st.session_state.step >= len(steps):
        st.session_state.step = len(steps) - 1

    st.caption(f"Step {st.session_state.step+1} of {len(steps)}")
    steps[st.session_state.step]()

if __name__ == "__main__":
    main()
