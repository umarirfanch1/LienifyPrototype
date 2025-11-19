# app.py - Lienify Arizona Lien & Waiver Form Generator (Streamlit)
import streamlit as st
import zipfile, os, tempfile, shutil
from docx import Document
from datetime import datetime, timedelta

st.set_page_config(page_title="Lienify - Arizona Lien Waiver Generator", layout="centered")

# HEADER
st.markdown("""
# **Lienify – Lien & Waiver Form Generator**  
**Prototype by Muhammad Umar Irfan**  
---
""")

# COMPLIANCE REMINDER (top)
st.info("""
**Arizona compliance summary (quick):**
- Preliminary Notice: must be sent **within 20 days of first delivery**.  
- Conditional waivers bind upon evidence of payment; Unconditional bind upon signing.  
- Waiving lien rights before performing work is illegal.  
- Unlicensed contractors may lose lien rights.  
- Stop notices allowed on private projects (except owner-occupied dwellings).  
- Payment bonds, tenant-as-agent, highway projects and UPL rules may affect lien eligibility.
""")

# ---------------------
# Utility: unzip templates if needed and find Arizona folder
# ---------------------
ZIP_NAME = "02_Templates-20251119T041237Z-1-001.zip"  # exact name you uploaded
EXTRACT_BASE = "02_Templates_extracted"

def ensure_templates():
    if not os.path.exists(EXTRACT_BASE):
        if not os.path.exists(ZIP_NAME):
            st.error(f"Template ZIP not found in repo: {ZIP_NAME}")
            st.stop()
        os.makedirs(EXTRACT_BASE, exist_ok=True)
        with zipfile.ZipFile(ZIP_NAME, 'r') as z:
            z.extractall(EXTRACT_BASE)

    # find Arizona folder path
    for root, dirs, files in os.walk(EXTRACT_BASE):
        lower = root.lower()
        if os.path.basename(root).lower() == "arizona" or "arizona" in lower:
            return root
    # fallback: check subfolders named similarly
    return None

AZ_FOLDER = ensure_templates()
if not AZ_FOLDER:
    st.error("Arizona template folder not found inside ZIP. Make sure 'Arizona' folder exists in the uploaded ZIP.")
    st.stop()

# Template filenames (your actual files are Word but named .pdf)
TEMPLATE_MAP = {
    ("Progress", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Progress", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Final", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
    ("Final", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
}

def find_template_file(expected_name):
    # search for a file that contains expected base (case-insensitive)
    basename = expected_name.replace(".pdf","").lower()
    for f in os.listdir(AZ_FOLDER):
        if basename in f.lower():
            return os.path.join(AZ_FOLDER, f)
    return None

# ---------------------
# Multi-step UI (Stepper style)
# ---------------------
if "step" not in st.session_state:
    st.session_state.step = 0

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step = max(0, st.session_state.step - 1)

# Step 0: Welcome / State selection
if st.session_state.step == 0:
    st.subheader("Welcome")
    st.write("Welcome to **Lienify** — Lien & Waiver Form Generator.")
    st.write("Prototype by Muhammad Umar Irfan.")
    # choose from list of 12 states (Arizona primary)
    STATES = ["Arizona","California","Nevada","Texas","Florida","Georgia","Washington","Oregon","Colorado","Utah","New Mexico","Idaho"]
    state = st.selectbox("Select State", [""] + STATES)
    if not state:
        st.write("Please select a state to continue.")
    else:
        if state != "Arizona":
            st.warning("Currently only Arizona is supported. Please select Arizona to continue.")
        else:
            st.session_state.state = state
            st.button("Next →", on_click=next_step)

# Step 1: Pre-screening + Role + Payment type + preliminary info
elif st.session_state.step == 1:
    st.subheader("Step 1 — Pre-Screening & Payment Type")
    st.markdown("Answer these to determine correct form and compliance checks.")
    role = st.selectbox("Your role on this project", ["", "Contractor","Subcontractor","Supplier","Material Provider"])
    payment_type = st.radio("Is this waiver for a Progress or Final payment?", ("","Progress","Final"))
    payment_received = st.radio("Has payment been received for this waiver?", ("","Yes","No"))

    # First delivery (for preliminary notice) - calendar
    first_delivery = st.date_input("First Delivery Date (for Preliminary Notice calculation)", value=None)
    st.write("Preliminary Notice deadline = First Delivery + 20 days (shown after you pick a date).")
    if first_delivery:
        pn_deadline = first_delivery + timedelta(days=20)
        st.info(f"Preliminary Notice deadline: **{pn_deadline.strftime('%Y-%m-%d')}**")

    # enforce required
    proceed = False
    if role and payment_type and payment_received and first_delivery:
        # save to session
        st.session_state.role = role
        st.session_state.payment_type = payment_type
        st.session_state.payment_received = payment_received
        st.session_state.first_delivery = first_delivery
        proceed = True

    cols = st.columns([1,1,1])
    with cols[0]:
        if st.button("Back"):
            prev_step()
    with cols[2]:
        if proceed:
            st.button("Next →", on_click=next_step)
        else:
            st.button("Next → (disabled)", disabled=True)

# Step 2: Detailed Data Collection (all mandatory except optional fields)
elif st.session_state.step == 2:
    st.subheader("Step 2 — Project & Payment Details (All fields required unless marked optional)")
    # Collect fields, use calendar widgets where dates required
    OwnerName = st.text_input("Owner Name")
    ProjectAddress = st.text_input("Project / Job Address")
    CustomerName = st.text_input("Customer / Paying Entity Name")
    LienorName = st.text_input("Lienor / Contractor / Provider Name")
    LicenseNumber = st.text_input("Contractor / Lienor License Number")
    PaymentAmount_num = st.number_input("Payment Amount (numeric)", min_value=0.0, format="%.2f")
    # show formatted string separately
    PaymentAmount = f"${PaymentAmount_num:,.2f}"
    st.write("Payment Amount (formatted):", PaymentAmount)

    WorkThroughDate = None
    if st.session_state.payment_type == "Progress":
        WorkThroughDate = st.date_input("Work Through Date (required for Progress payments)")
    else:
        # optional but shown
        WorkThroughDate = st.date_input("Work Through Date (if applicable)", value=None)

    ExecutionDate = st.date_input("Execution Date (when waiver is signed)", value=datetime.today())
    JobNumber = st.text_input("Job / Project Number")
    PropertyDescription = st.text_area("Property Description / Legal Description", height=100)

    # All fields required validations:
    missing = []
    required_fields = {
        "OwnerName": OwnerName,
        "ProjectAddress": ProjectAddress,
        "CustomerName": CustomerName,
        "LienorName": LienorName,
        "LicenseNumber": LicenseNumber,
        "PaymentAmount": PaymentAmount_num,
        "ExecutionDate": ExecutionDate,
        "JobNumber": JobNumber,
        "PropertyDescription": PropertyDescription
    }
    for k,v in required_fields.items():
        if (isinstance(v, str) and v.strip()=="") or (v is None):
            missing.append(k)

    # Additional checks:
    # WorkThroughDate required for Progress
    if st.session_state.payment_type == "Progress" and not WorkThroughDate:
        missing.append("WorkThroughDate (required for Progress)")

    # For Final: WorkThroughDate must be <= ExecutionDate if provided
    if st.session_state.payment_type == "Final" and WorkThroughDate and WorkThroughDate > ExecutionDate:
        st.error("Work Through Date cannot be after Execution Date for Final payments.")
        missing.append("Invalid dates")

    # Preliminary Notice check using first_delivery from session
    fd = st.session_state.first_delivery
    pn_deadline = fd + timedelta(days=20)
    meets_pn = ExecutionDate <= pn_deadline
    st.write(f"Preliminary Notice deadline: {pn_deadline.strftime('%Y-%m-%d')}. Execution Date: {ExecutionDate.strftime('%Y-%m-%d')}")
    if meets_pn:
        st.success("Execution Date is within Preliminary Notice deadline window.")
    else:
        st.warning("Execution Date is **after** Preliminary Notice 20-day deadline. Review compliance.")

    cols = st.columns([1,1,1])
    with cols[0]:
        if st.button("Back"):
            prev_step()

    with cols[2]:
        if missing:
            st.error("Please complete all required fields before continuing.")
            st.write("Missing or invalid:", ", ".join(missing))
            st.button("Next → (disabled)", disabled=True)
        else:
            st.button("Next →", on_click=next_step)

    # save into session state if proceeding (not automatically; saved above when fill next pressed)
    st.session_state.OwnerName = OwnerName
    st.session_state.ProjectAddress = ProjectAddress
    st.session_state.CustomerName = CustomerName
    st.session_state.LienorName = LienorName
    st.session_state.LicenseNumber = LicenseNumber
    st.session_state.PaymentAmount = PaymentAmount
    st.session_state.WorkThroughDate = WorkThroughDate
    st.session_state.ExecutionDate = ExecutionDate
    st.session_state.JobNumber = JobNumber
    st.session_state.PropertyDescription = PropertyDescription

# Step 3: Review & Generate (show professional message and generate file)
elif st.session_state.step == 3:
    st.subheader("Step 3 — Review & Generate")
    # Show professional guidance and template name (not raw file dump)
    ptype = st.session_state.payment_type
    paid = st.session_state.payment_received
    cond = "Yes" if paid == "No" else "No"  # conditional if payment not received
    template_key = (ptype, cond)
    template_name = TEMPLATE_MAP[template_key]

    st.markdown("**Based on Arizona statutory requirements, the form you require is:**")
    st.markdown(f"### {template_name}")
    st.write("A professional legal form will be generated and populated with the details you provided.")

    # Show summary table of entered info
    st.markdown("#### Entered details (review)")
    summary = {
        "OwnerName": st.session_state.OwnerName,
        "ProjectAddress": st.session_state.ProjectAddress,
        "CustomerName": st.session_state.CustomerName,
        "LienorName": st.session_state.LienorName,
        "LicenseNumber": st.session_state.LicenseNumber,
        "PaymentAmount": st.session_state.PaymentAmount,
        "WorkThroughDate": st.session_state.WorkThroughDate,
        "ExecutionDate": st.session_state.ExecutionDate,
        "JobNumber": st.session_state.JobNumber,
        "PropertyDescription": st.session_state.PropertyDescription,
        "FirstDeliveryDate": st.session_state.first_delivery
    }
    st.json(summary)

    cols = st.columns([1,1,1])
    with cols[0]:
        if st.button("Back"):
            prev_step()

    with cols[2]:
        if st.button("Generate & Download"):
            # find actual template file in AZ_FOLDER
            selected_filename = TEMPLATE_MAP[(ptype, cond)]
            template_path = find_template_file(selected_filename)
            if not template_path:
                st.error("Template file could not be found in Arizona folder.")
            else:
                # load docx and replace
                doc = Document(template_path)
                # mapping placeholders -> values (ensure strings)
                mapping = {
                    "{{OwnerName}}": st.session_state.OwnerName,
                    "{{ProjectAddress}}": st.session_state.ProjectAddress,
                    "{{CustomerName}}": st.session_state.CustomerName,
                    "{{LienorName}}": st.session_state.LienorName,
                    "{{LicenseNumber}}": st.session_state.LicenseNumber,
                    "{{PaymentAmount}}": st.session_state.PaymentAmount,
                    "{{WorkThroughDate}}": (st.session_state.WorkThroughDate.strftime("%B %d, %Y") if st.session_state.WorkThroughDate else ""),
                    "{{ExecutionDate}}": st.session_state.ExecutionDate.strftime("%B %d, %Y"),
                    "{{AuthorizedRep}}": st.session_state.AuthorizedRep if "AuthorizedRep" in st.session_state else "",
                    "{{JobNumber}}": st.session_state.JobNumber,
                    "{{PropertyDescription}}": st.session_state.PropertyDescription,
                    "{{FirstDeliveryDate}}": st.session_state.first_delivery.strftime("%B %d, %Y")
                }
                # Replace in paragraphs and tables
                def replace_all(doc_obj, mp):
                    for p in doc_obj.paragraphs:
                        for k,v in mp.items():
                            if k in p.text:
                                p.text = p.text.replace(k, v)
                    for t in doc_obj.tables:
                        for row in t.rows:
                            for cell in row.cells:
                                for k,v in mp.items():
                                    if k in cell.text:
                                        cell.text = cell.text.replace(k, v)
                replace_all(doc, mapping)

                # save to temporary file and provide download
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp_path = tmp.name
                    doc.save(tmp_path)
                display_name = f"Lienify_AZ_{ptype}_{'Conditional' if cond=='Yes' else 'Unconditional'}_{datetime.today().strftime('%Y%m%d')}.docx"
                with open(tmp_path, "rb") as f:
                    st.download_button("Download Filled Waiver (.docx)", data=f, file_name=display_name, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                st.success("Generated document includes all provided details.")

# FOOTER
st.markdown("---")
st.markdown("##### © Lienify — Prototype by Muhammad Umar Irfan")
