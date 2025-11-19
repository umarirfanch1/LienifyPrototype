# app.py - Lienify Arizona Lien & Waiver Form Generator (Optimized)
import streamlit as st
import zipfile, os, tempfile
from docx import Document
from datetime import datetime, timedelta

st.set_page_config(page_title="Lienify - Arizona Lien Waiver Generator", layout="centered")

# ---------------------
# Header for all pages after Welcome
# ---------------------
def page_header():
    st.markdown("# **Lienify – Lien & Waiver Form Generator**")
    st.markdown("Please fill out the required fields *")

# ---------------------
# Template extraction
# ---------------------
ZIP_NAME = "02_Templates-20251119T041237Z-1-001.zip"
EXTRACT_BASE = "02_Templates_extracted"

def ensure_templates():
    if not os.path.exists(EXTRACT_BASE):
        if not os.path.exists(ZIP_NAME):
            st.error(f"Template ZIP not found: {ZIP_NAME}")
            st.stop()
        os.makedirs(EXTRACT_BASE, exist_ok=True)
        with zipfile.ZipFile(ZIP_NAME, 'r') as z:
            z.extractall(EXTRACT_BASE)

    for root, dirs, files in os.walk(EXTRACT_BASE):
        if os.path.basename(root).lower() == "arizona" or "arizona" in root.lower():
            return root
    return None

AZ_FOLDER = ensure_templates()
if not AZ_FOLDER:
    st.error("Arizona template folder not found in ZIP.")
    st.stop()

TEMPLATE_MAP = {
    ("Progress", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Progress", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Final", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
    ("Final", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
}

def find_template_file(expected_name):
    basename = expected_name.replace(".pdf","").lower()
    for f in os.listdir(AZ_FOLDER):
        if basename in f.lower():
            return os.path.join(AZ_FOLDER, f)
    return None

# ---------------------
# Multi-step UI
# ---------------------
if "step" not in st.session_state:
    st.session_state.step = 0

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step = max(0, st.session_state.step - 1)

# ---------------------
# Step 0: Welcome / State Selection
# ---------------------
if st.session_state.step == 0:
    st.subheader("Welcome")
    st.write("Welcome to **Lienify — Lien & Waiver Form Generator**")
    st.write("Prototype by Muhammad Umar Irfan.")

    STATES = ["Arizona","California","Nevada","Texas","Florida","Georgia","Washington","Oregon","Colorado","Utah","New Mexico","Idaho"]
    state = st.selectbox("Select State", [""] + STATES)
    if state:
        if state != "Arizona":
            st.warning("Currently only Arizona is supported. Please select Arizona to continue.")
        else:
            st.session_state.state = state
            if st.button("Next →"):
                next_step()

# ---------------------
# Step 1: Compliance Page
# ---------------------
elif st.session_state.step == 1:
    page_header()
    st.info("""
Thanks for selecting Arizona. Have a look at compliance check before we proceed:

- Preliminary Notice: must be sent **within 20 days of first delivery**.  
- Conditional waivers bind upon evidence of payment; Unconditional bind upon signing.  
- Waiving lien rights before performing work is illegal.  
- Unlicensed contractors may lose lien rights.  
- Stop notices allowed on private projects (except owner-occupied dwellings).  
- Payment bonds, tenant-as-agent, highway projects and UPL rules may affect lien eligibility.
""")
    if st.button("Yes, I understood, please proceed"):
        next_step()

# ---------------------
# Step 2A: Role
# ---------------------
elif st.session_state.step == 2:
    page_header()
    role = st.selectbox("Your role on this project", ["", "Contractor","Subcontractor","Supplier","Material Provider"])
    if role:
        st.session_state.role = role
        if st.button("Next →"):
            next_step()
    if st.button("Back"):
        prev_step()

# ---------------------
# Step 2B: Payment Type
# ---------------------
elif st.session_state.step == 3:
    page_header()
    payment_type = st.radio("Is this waiver for a Progress or Final payment?", ("","Progress","Final"))
    if payment_type:
        st.session_state.payment_type = payment_type
        if st.button("Next →"):
            next_step()
    if st.button("Back"):
        prev_step()

# ---------------------
# Step 2C: Payment Received
# ---------------------
elif st.session_state.step == 4:
    page_header()
    payment_received = st.radio("Has payment been received for this waiver?", ("","Yes","No"))
    if payment_received:
        st.session_state.payment_received = payment_received
        if st.button("Next →"):
            next_step()
    if st.button("Back"):
        prev_step()

# ---------------------
# Step 2D: First Delivery Date
# ---------------------
elif st.session_state.step == 5:
    page_header()
    first_delivery = st.date_input("First Delivery Date (for Preliminary Notice calculation)", value=None)
    if first_delivery:
        st.session_state.first_delivery = first_delivery
        if st.button("Next →"):
            next_step()
    if st.button("Back"):
        prev_step()

# ---------------------
# Step 3: Project & Payment Details
# ---------------------
elif st.session_state.step == 6:
    page_header()
    OwnerName = st.text_input("Owner Name")
    ProjectAddress = st.text_input("Project / Job Address")
    CustomerName = st.text_input("Customer / Paying Entity Name")
    LienorName = st.text_input("Lienor / Contractor / Provider Name")
    LicenseNumber = st.text_input("Contractor / Lienor License Number")
    PaymentAmount = st.text_input("Payment Amount", value="$0.00")
    WorkThroughDate = st.date_input("Work Through Date (if applicable)")
    ExecutionDate = st.date_input("Execution Date (when waiver is signed)", value=datetime.today())
    JobNumber = st.text_input("Job / Project Number")
    PropertyDescription = st.text_area("Property Description / Legal Description", height=100)

    missing = []
    required_fields = [OwnerName, ProjectAddress, CustomerName, LienorName, LicenseNumber, PaymentAmount, ExecutionDate, JobNumber, PropertyDescription]
    for i,v in enumerate(required_fields):
        if not v:
            missing.append(i)

    if st.button("Back"):
        prev_step()

    if not missing and st.button("Next →"):
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
        next_step()
    elif missing:
        st.warning("Please fill out all required fields.")

# ---------------------
# Step 4: Review & Generate
# ---------------------
elif st.session_state.step == 7:
    page_header()
    st.markdown("### Review your information")
    st.write(f"**Owner Name:** {st.session_state.OwnerName}")
    st.write(f"**Project Address:** {st.session_state.ProjectAddress}")
    st.write(f"**Customer Name:** {st.session_state.CustomerName}")
    st.write(f"**Lienor Name:** {st.session_state.LienorName}")
    st.write(f"**License Number:** {st.session_state.LicenseNumber}")
    st.write(f"**Payment Amount:** {st.session_state.PaymentAmount}")
    st.write(f"**Work Through Date:** {st.session_state.WorkThroughDate}")
    st.write(f"**Execution Date:** {st.session_state.ExecutionDate}")
    st.write(f"**Job Number:** {st.session_state.JobNumber}")
    st.write(f"**Property Description:** {st.session_state.PropertyDescription}")
    st.write(f"**First Delivery Date:** {st.session_state.first_delivery}")

    if st.button("Back"):
        prev_step()

    if st.button("Generate & Download"):
        st.info("Please wait... your form is being generated.")
        ptype = st.session_state.payment_type
        cond = "Yes" if st.session_state.payment_received == "No" else "No"
        template_file = TEMPLATE_MAP[(ptype, cond)]
        template_path = find_template_file(template_file)
        if not template_path:
            st.error("Template file not found.")
        else:
            doc = Document(template_path)
            mapping = {
                "{{OwnerName}}": st.session_state.OwnerName,
                "{{ProjectAddress}}": st.session_state.ProjectAddress,
                "{{CustomerName}}": st.session_state.CustomerName,
                "{{LienorName}}": st.session_state.LienorName,
                "{{LicenseNumber}}": st.session_state.LicenseNumber,
                "{{PaymentAmount}}": st.session_state.PaymentAmount,
                "{{WorkThroughDate}}": st.session_state.WorkThroughDate.strftime("%B %d, %Y") if st.session_state.WorkThroughDate else "",
                "{{ExecutionDate}}": st.session_state.ExecutionDate.strftime("%B %d, %Y"),
                "{{JobNumber}}": st.session_state.JobNumber,
                "{{PropertyDescription}}": st.session_state.PropertyDescription,
                "{{FirstDeliveryDate}}": st.session_state.first_delivery.strftime("%B %d, %Y")
            }
            for p in doc.paragraphs:
                for k,v in mapping.items():
                    if k in p.text: p.text = p.text.replace(k,v)
            for t in doc.tables:
                for row in t.rows:
                    for cell in row.cells:
                        for k,v in mapping.items():
                            if k in cell.text: cell.text = cell.text.replace(k,v)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                doc.save(tmp.name)
                tmp_path = tmp.name
            display_name = f"Lienify_AZ_{ptype}_{'Conditional' if cond=='Yes' else 'Unconditional'}_{datetime.today().strftime('%Y%m%d')}.docx"
            with open(tmp_path, "rb") as f:
                st.download_button("Download Filled Waiver (.docx)", f, file_name=display_name, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.success("Your form has been generated with all provided details.")
