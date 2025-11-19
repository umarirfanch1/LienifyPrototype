# app.py
import streamlit as st
from zipfile import ZipFile
from io import BytesIO
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
import re
from docx import Document

# ---------- Configuration ----------
TEMPLATES_ZIP_PATH = "./02_Templates-20251119T041237Z-1-001.zip"
ARIZONA_FOLDER_NAME = "Arizona Templates"
TEMPLATE_FILENAME_MAP = {
    ("Progress", False): "CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Progress", True):  "UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Final", False):    "CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
    ("Final", True):     "UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
}

# ---------- Utilities ----------
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

def currency_format(raw_str):
    if raw_str is None:
        return "$0.00"
    cleaned = re.sub(r"[^\d.\-]", "", str(raw_str))
    try:
        val = float(cleaned)
    except:
        return f"${raw_str}"
    return f"${val:,.2f}"

def safe_filename(text):
    return re.sub(r"[^\w\-_\. ]", "", text).replace(" ", "_")

def replace_docx_placeholders(doc: Document, replacements: dict):
    for p in doc.paragraphs:
        full_text = "".join([r.text for r in p.runs])
        new_text = full_text
        for key, val in replacements.items():
            new_text = re.sub(r"\[" + re.escape(key) + r"\]", str(val), new_text)
            new_text = re.sub(r"\{" + re.escape(key) + r"\}", str(val), new_text)
            new_text = new_text.replace(key, str(val))
        if new_text != full_text:
            for i in range(len(p.runs)-1, -1, -1):
                p.runs[i].clear()
            if len(p.runs) == 0:
                p.add_run(new_text)
            else:
                p.runs[0].text = new_text
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_text = "".join([p.text for p in cell.paragraphs])
                new_cell_text = cell_text
                for key, val in replacements.items():
                    new_cell_text = re.sub(r"\[" + re.escape(key) + r"\]", str(val), new_cell_text)
                    new_cell_text = re.sub(r"\{" + re.escape(key) + r"\}", str(val), new_cell_text)
                    new_cell_text = new_cell_text.replace(key, str(val))
                if new_cell_text != cell_text:
                    for p in cell.paragraphs:
                        p.clear()
                    cell.paragraphs[0].add_run(new_cell_text)

def build_replacement_map():
    mapping = {}
    mapping["OWNER"] = st.session_state.owner_name
    mapping["Owner"] = st.session_state.owner_name
    mapping["OWNER_NAME"] = st.session_state.owner_name
    mapping["CONTRACTOR"] = st.session_state.contractor_name
    mapping["Contractor"] = st.session_state.contractor_name
    mapping["CONTRACTOR_NAME"] = st.session_state.contractor_name
    mapping["PROJECT"] = st.session_state.project_name
    mapping["Project"] = st.session_state.project_name
    mapping["PROJECT_NAME"] = st.session_state.project_name
    mapping["PROJECT_ADDRESS"] = st.session_state.project_address
    mapping["ADDRESS"] = st.session_state.project_address
    mapping["AMOUNT"] = currency_format(st.session_state.payment_amount_raw)
    mapping["Amount"] = currency_format(st.session_state.payment_amount_raw)
    mapping["PAYMENT_AMOUNT"] = currency_format(st.session_state.payment_amount_raw)
    mapping["INVOICE"] = st.session_state.invoice_number
    mapping["INVOICE_NUMBER"] = st.session_state.invoice_number
    mapping["JOB_DESCRIPTION"] = st.session_state.job_description
    mapping["JOB"] = st.session_state.job_description
    mapping["FIRST_DELIVERY_DATE"] = st.session_state.first_delivery_date.strftime("%B %d, %Y") if st.session_state.first_delivery_date else ""
    mapping["JOB_START_DATE"] = st.session_state.job_start_date.strftime("%B %d, %Y") if st.session_state.job_start_date else ""
    mapping["JOB_END_DATE"] = st.session_state.job_end_date.strftime("%B %d, %Y") if st.session_state.job_end_date else ""
    mapping["DATE"] = datetime.now().strftime("%B %d, %Y")
    mapping["_____"] = ""
    return mapping

# ---------- UI Helpers ----------
def step_navigation(can_go_next=True):
    cols = st.columns([1, 1, 1])
    with cols[0]:
        if st.button("Back", key=f"back_btn_{st.session_state.step}"):
            st.session_state.step = max(0, st.session_state.step - 1)
            st.rerun()
    with cols[2]:
        if st.button("Next", key=f"next_btn_{st.session_state.step}", disabled=not can_go_next):
            st.session_state.step = st.session_state.step + 1
            st.rerun()
    st.write("")
    st.markdown("---")

# ---------- Steps ----------
def step_welcome():
    st.header("Welcome to Lienify Waiver and Lien Form Generator")
    st.caption("A simple step-by-step generator for Arizona waiver & release forms.")
    st.write("")
    if st.button("Select state", key="welcome_select_state"):
        st.session_state.step = 1
        st.rerun()
    st.write("")
    st.markdown("---")

def step_state_selection():
    st.header("State Selection")
    st.caption("Currently we support Arizona. Select your state to continue.")
    st.write("")
    state = st.selectbox("Choose your state", options=["-- Select --", "Arizona", "Other"], key="state_select_az")
    st.session_state.state = state
    if state == "Arizona":
        st.success("Arizona selected. Proceeding to compliance.")
        st.write("")
        st.caption("Click Next to continue or the button below to proceed immediately.")
        if st.button("Proceed to Arizona compliance", key="to_compliance_az"):
            st.session_state.step = 2
            st.rerun()
        step_navigation(can_go_next=True)
    elif state == "Other":
        st.warning("Only Arizona templates are active in this prototype. Please select Arizona to continue.")
        step_navigation(can_go_next=False)
    else:
        st.info("Please select your state to continue.")
        step_navigation(can_go_next=False)

def step_compliance():
    st.header("Arizona Compliance Summary")
    st.caption("Important compliance notes for Arizona lien/waiver forms.")
    st.markdown(
        """
        **Short summary:** Arizona has specific rules for construction waivers/releases and lien notices.
        This tool provides a fillable waiver/release based on the form templates for Arizona.
        Make sure you review the generated document for legal accuracy for your project, and consult counsel when necessary.
        """
    )
    st.write("")
    st.info("By continuing you confirm you have read these notes and will use the form responsibly.")
    if st.button("Yes, I understand, please proceed", key="compliance_ack_btn"):
        st.session_state.compliance_ack = True
        st.session_state.step = 3
        st.rerun()
    step_navigation(can_go_next=st.session_state.compliance_ack)

def step_prescreen_role():
    st.header("Pre-screening — Role")
    st.caption("Select the role you have in this transaction (required).")
    role = st.selectbox("Your role", options=["", "Owner", "Contractor", "Subcontractor", "Supplier", "Other"], key="role_select_1")
    st.session_state.role = role
    if role == "":
        st.warning("Please select your role to proceed.")
        step_navigation(can_go_next=False)
    else:
        step_navigation(can_go_next=True)

def step_prescreen_payment_type():
    st.header("Pre-screening — Payment Type")
    st.caption("Is this a Progress payment or a Final payment? (required)")
    payment_type = st.radio("Payment Type", options=["Progress", "Final"], key="payment_type_radio_1")
    st.session_state.payment_type = payment_type
    st.write("")
    st.caption("Progress = partial / interim payment. Final = final release on project completion.")
    step_navigation(can_go_next=True)

def step_prescreen_payment_received():
    st.header("Pre-screening — Payment Received")
    st.caption("Has the payment been received? (required)")
    received = st.radio("Payment Received?", options=["Yes", "No"], key="payment_received_radio_1")
    st.session_state.payment_received = received
    if received == "Yes":
        st.success("Marking as received — this will select an Unconditional release template.")
    else:
        st.info("Marked as not received — this will select a Conditional release template.")
    step_navigation(can_go_next=True)

def step_prescreen_first_delivery():
    st.header("Pre-screening — First Delivery Date")
    st.caption("Enter the first date when materials or labor were delivered (required).")
    first_date = st.date_input("First delivery date", key="first_delivery_date_input")
    st.session_state.first_delivery_date = first_date
    step_navigation(can_go_next=True)

def step_project_payment_details():
    st.header("Project & Payment Details")
    st.caption("All fields required. Use calendar widgets for dates. Format amounts in numbers; $ will be added automatically.")
    st.write("")
    st.text_input("Project name", key="project_name_input", placeholder="e.g., Highway Renovation #12")
    st.session_state.project_name = st.session_state.get("project_name_input")
    st.text_input("Project address", key="project_address_input")
    st.session_state.project_address = st.session_state.get("project_address_input")
    st.text_input("Owner name", key="owner_name_input")
    st.session_state.owner_name = st.session_state.get("owner_name_input")
    st.text_input("Contractor name", key="contractor_name_input")
    st.session_state.contractor_name = st.session_state.get("contractor_name_input")
    st.text_input("Invoice number", key="invoice_number_input")
    st.session_state.invoice_number = st.session_state.get("invoice_number_input")
    st.text_input("Payment amount (numbers only)", key="payment_amount_input")
    st.session_state.payment_amount_raw = st.session_state.get("payment_amount_input")
    st.date_input("Job start date", key="job_start_date_input")
    st.session_state.job_start_date = st.session_state.get("job_start_date_input")
    st.date_input("Job end date", key="job_end_date_input")
    st.session_state.job_end_date = st.session_state.get("job_end_date_input")
    st.text_area("Brief job description", key="job_description_input", height=120)
    st.session_state.job_description = st.session_state.get("job_description_input")
    required_fields = [
        st.session_state.project_name,
        st.session_state.project_address,
        st.session_state.owner_name,
        st.session_state.contractor_name,
        st.session_state.invoice_number,
        st.session_state.payment_amount_raw,
        st.session_state.job_start_date,
        st.session_state.job_end_date,
        st.session_state.job_description,
    ]
    all_filled = all([bool(f) for f in required_fields])
    if not all_filled:
        st.warning("Please complete all required project and payment details before proceeding.")
    step_navigation(can_go_next=all_filled)

def step_review_and_generate():
    st.header("Review — Confirm details before generating")
    st.caption("Review all details below. Click Generate to create the Word document.")
    st.markdown("---")
    st.subheader("Project")
    st.write(f"**Project name:** {st.session_state.project_name}")
    st.write(f"**Project address:** {st.session_state.project_address}")
    st.write(f"**Job description:** {st.session_state.job_description}")
    st.subheader("Parties & References")
    st.write(f"**Owner:** {st.session_state.owner_name}")
    st.write(f"**Contractor / Claimant:** {st.session_state.contractor_name}")
    st.write(f"**Invoice / Ref No.:** {st.session_state.invoice_number}")
    st.subheader("Payment")
    st.write(f"**Payment type:** {st.session_state.payment_type}")
    st.write(f"**Payment received:** {st.session_state.payment_received}")
    st.write(f"**Amount:** {currency_format(st.session_state.payment_amount_raw)}")
    st.subheader("Dates")
    st.write(f"**First delivery:** {st.session_state.first_delivery_date.strftime('%B %d, %Y') if st.session_state.first_delivery_date else ''}")
    st.write(f"**Job start:** {st.session_state.job_start_date.strftime('%B %d, %Y') if st.session_state.job_start_date else ''}")
    st.write(f"**Job end:** {st.session_state.job_end_date.strftime('%B %d, %Y') if st.session_state.job_end_date else ''}")
    st.markdown("---")
    st.info("If any detail is incorrect, use Back to edit. All fields are required.")
    if st.button("Generate document", key="generate_doc_btn"):
        with st.spinner("Please wait, your form is being generated..."):
            try:
                doc_bytes, filename = generate_document()
                st.session_state.generated_file_bytes = doc_bytes
                st.session_state.generated_filename = filename
                st.success("Document generated successfully.")
                st.session_state.step += 1
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate document: {e}")
    step_navigation(can_go_next=True)

def step_download():
    st.header("Done — Download your populated form")
    st.caption("Click the button below to download the generated document.")
    if st.session_state.generated_file_bytes and st.session_state.generated_filename:
        st.download_button(
            label="Download populated document",
            data=st.session_state.generated_file_bytes,
            file_name=st.session_state.generated_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="download_populated_doc"
        )
        st.success("If needed, change inputs and regenerate another copy.")
    else:
        st.warning("No generated file available. Go back and press Generate.")
    step_navigation(can_go_next=False)

# ---------- Document generation ----------
def extract_template_from_zip(zip_path: str, template_relpath: str, extract_to: str):
    template_basename = Path(template_relpath).name
    with ZipFile(zip_path, "r") as z:
        # find any file in zip that ends with the template filename
        matched_file = None
        for name in z.namelist():
            if Path(name).name == template_basename:
                matched_file = name
                break
        if matched_file is None:
            raise FileNotFoundError(f"Could not find template {template_relpath} in {zip_path}")
        z.extract(matched_file, path=extract_to)
        return Path(extract_to) / matched_file

def generate_document():
    payment_type = st.session_state.payment_type
    received = st.session_state.payment_received
    unconditional = True if received == "Yes" else False
    key = (payment_type, unconditional)
    if key not in TEMPLATE_FILENAME_MAP:
        raise ValueError("Template mapping not found for your selection.")
    template_filename = TEMPLATE_FILENAME_MAP[key]
    template_relpath = f"{ARIZONA_FOLDER_NAME}/{template_filename}"
    tmpdir = tempfile.mkdtemp()
    try:
        extracted = extract_template_from_zip(TEMPLATES_ZIP_PATH, template_relpath, tmpdir)
        doc = Document(str(extracted))
        replacements = build_replacement_map()
        replace_docx_placeholders(doc, replacements)
        fbytes = BytesIO()
        doc.save(fbytes)
        fbytes.seek(0)
        conditional_text = "Unconditional" if unconditional else "Conditional"
        date_part = datetime.now().strftime("%Y%m%d")
        progressive_text = payment_type
        out_filename = f"Lienify_AZ_{progressive_text}_{conditional_text}_{date_part}.docx"
        out_filename = safe_filename(out_filename)
        return fbytes.getvalue(), out_filename
    finally:
        try:
            shutil.rmtree(tmpdir)
        except:
            pass

# ---------- Main App ----------
def main():
    st.set_page_config(page_title="Lienify — Waiver & Lien Generator", page_icon="🧾", layout="centered")
    init_session()
    st.write("")

    steps_titles = [
        "Welcome",
        "State Selection",
        "Compliance",
        "Role",
        "Payment Type",
        "Payment Received",
        "First Delivery",
        "Project Details",
        "Review & Generate",
        "Download"
    ]
    st.caption(f"Step {st.session_state.step + 1} of {len(steps_titles)} — {steps_titles[min(st.session_state.step, len(steps_titles)-1)]}")
    st.markdown("---")

    mapping = {
        0: step_welcome,
        1: step_state_selection,
        2: step_compliance,
        3: step_prescreen_role,
        4: step_prescreen_payment_type,
        5: step_prescreen_payment_received,
        6: step_prescreen_first_delivery,
        7: step_project_payment_details,
        8: step_review_and_generate,
        9: step_download,
    }
    func = mapping.get(st.session_state.step, step_welcome)
    func()

if __name__ == "__main__":
    main()
