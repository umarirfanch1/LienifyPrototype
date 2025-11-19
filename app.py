# app.py - Lienify Arizona Lien & Waiver Form Generator (Streamlit)
import streamlit as st
import zipfile, os, tempfile
from docx import Document
from datetime import datetime, timedelta

st.set_page_config(page_title="Lienify - Arizona Lien Waiver Generator", layout="centered")

# ---------------------
# Utility: unzip templates if needed and find Arizona folder
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
        if "arizona" in root.lower():
            return root
    return None

AZ_FOLDER = ensure_templates()
if not AZ_FOLDER:
    st.error("Arizona Templates folder not found inside ZIP.")
    st.stop()

# Exact template filenames
TEMPLATE_MAP = {
    ("Progress", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Progress", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Final", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
    ("Final", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
}

def find_template_file(filename):
    for root, dirs, files in os.walk(AZ_FOLDER):
        for f in files:
            if f.lower() == filename.lower():
                return os.path.join(root, f)
    return None

# ---------------------
# Session state
# ---------------------
if "step" not in st.session_state:
    st.session_state.step = 0

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step = max(0, st.session_state.step - 1)

# ---------------------
# Step 0: Welcome & state
# ---------------------
if st.session_state.step == 0:
    st.header("Lienify — Lien & Waiver Form Generator")
    st.write("Welcome to Lienify Waiver and Lien Form Generator.")
    
    STATES = ["Arizona","California","Nevada","Texas","Florida","Georgia","Washington","Oregon","Colorado","Utah","New Mexico","Idaho"]
    state = st.selectbox("Select your state", [""] + STATES)
    
    if state == "Arizona":
        st.session_state.state = state
        st.session_state.step = 0.5
    elif state != "":
        st.warning("Currently only Arizona is available for testing.")

# ---------------------
# Step 0.5: Arizona compliance
# ---------------------
if st.session_state.step == 0.5:
    st.header("Lienify — Lien & Waiver Form Generator")
    st.subheader("Thanks for selecting Arizona")
    st.write("Have a look at compliance summary before we proceed:")
    
    st.info("""
- Preliminary Notice: must be sent within 20 days of first delivery.
- Conditional waivers bind upon evidence of payment; Unconditional bind upon signing.
- Waiving lien rights before performing work is illegal.
- Unlicensed contractors may lose lien rights.
- Stop notices allowed on private projects (except owner-occupied dwellings).
- Payment bonds, tenant-as-agent, highway projects and UPL rules may affect lien eligibility.
    """)
    
    if st.button("Yes, I understood. Please proceed"):
        next_step()

# ---------------------
# Step 1: Role
# ---------------------
if st.session_state.step == 1:
    st.header("Lienify — Lien & Waiver Form Generator")
    st.write("Please fill out the required form.")
    
    role = st.radio("Your role on this project:", ["Contractor","Subcontractor","Supplier","Material Provider"])
    cols = st.columns([1,1])
    with cols[0]:
        if st.button("Back"):
            prev_step()
    with cols[1]:
        if role:
            st.session_state.role = role
            next_step()

# ---------------------
# Step 2: Payment type
# ---------------------
if st.session_state.step == 2:
    st.header("Lienify — Lien & Waiver Form Generator")
    st.write("Please fill out the required form.")
    
    payment_type = st.radio("Is this waiver for a Progress or Final payment?", ["Progress","Final"])
    cols = st.columns([1,1])
    with cols[0]:
        if st.button("Back"):
            prev_step()
    with cols[1]:
        if payment_type:
            st.session_state.payment_type = payment_type
            next_step()

# ---------------------
# Step 3: Payment received
# ---------------------
if st.session_state.step == 3:
    st.header("Lienify — Lien & Waiver Form Generator")
    st.write("Please fill out the required form.")
    
    payment_received = st.radio("Has payment been received for this waiver?", ["Yes","No"])
    cols = st.columns([1,1])
    with cols[0]:
        if st.button("Back"):
            prev_step()
    with cols[1]:
        if payment_received:
            st.session_state.payment_received = payment_received
            
            # Determine which form will be generated
            cond = "Yes" if payment_received == "No" else "No"
            template_file = TEMPLATE_MAP[(st.session_state.payment_type, cond)]
            st.success(f"Based on your selections, this form will be generated:\n**{template_file}**")
            
            if st.button("Next →"):
                next_step()

# ---------------------
# Step 4: First Delivery
# ---------------------
if st.session_state.step == 4:
    st.header("Lienify — Lien & Waiver Form Generator")
    st.write("Please fill out the required form.")
    
    first_delivery = st.date_input("First Delivery Date (for Preliminary Notice)")
    cols = st.columns([1,1])
    with cols[0]:
        if st.button("Back"):
            prev_step()
    with cols[1]:
        if first_delivery:
            st.session_state.first_delivery = first_delivery
            st.write(f"Preliminary Notice deadline: {first_delivery + timedelta(days=20)}")
            if st.button("Next →"):
                next_step()

# ---------------------
# Step 5: Project & Payment Details
# ---------------------
if st.session_state.step == 5:
    st.header("Lienify — Lien & Waiver Form Generator")
    st.write("Please fill out the required form.")
    
    OwnerName = st.text_input("Owner Name")
    ProjectAddress = st.text_input("Project / Job Address")
    CustomerName = st.text_input("Customer / Paying Entity Name")
    LienorName = st.text_input("Lienor / Contractor / Provider Name")
    LicenseNumber = st.text_input("Contractor / Lienor License Number")
    PaymentAmount = st.number_input("Payment Amount ($)", min_value=0.0, format="%.2f")
    
    if st.session_state.payment_type == "Progress":
        WorkThroughDate = st.date_input("Work Through Date (required)")
    else:
        WorkThroughDate = st.date_input("Work Through Date (optional)", value=None)
    ExecutionDate = st.date_input("Execution Date", value=datetime.today())
    JobNumber = st.text_input("Job / Project Number")
    PropertyDescription = st.text_area("Property Description / Legal Description", height=100)
    
    cols = st.columns([1,1])
    with cols[0]:
        if st.button("Back"):
            prev_step()
    with cols[1]:
        if st.button("Next →"):
            st.session_state.OwnerName = OwnerName
            st.session_state.ProjectAddress = ProjectAddress
            st.session_state.CustomerName = CustomerName
            st.session_state.LienorName = LienorName
            st.session_state.LicenseNumber = LicenseNumber
            st.session_state.PaymentAmount = f"${PaymentAmount:,.2f}"
            st.session_state.WorkThroughDate = WorkThroughDate
            st.session_state.ExecutionDate = ExecutionDate
            st.session_state.JobNumber = JobNumber
            st.session_state.PropertyDescription = PropertyDescription
            next_step()

# ---------------------
# Step 6: Generate & Download
# ---------------------
if st.session_state.step == 6:
    st.header("Lienify — Lien & Waiver Form Generator")
    st.write("Your form will be generated based on the details you provided.")
    
    ptype = st.session_state.payment_type
    paid = st.session_state.payment_received
    cond = "Yes" if paid == "No" else "No"
    template_file = TEMPLATE_MAP[(ptype, cond)]
    template_path = find_template_file(template_file)
    
    cols = st.columns([1,1])
    with cols[0]:
        if st.button("Back"):
            prev_step()
    with cols[1]:
        if template_path and st.button("Generate & Download"):
            with st.spinner("Please wait, your form is being generated..."):
                doc = Document(template_path)
                
                # Manual replacement
                replacements = {
                    "Project: _____________________________": f"Project: {st.session_state.ProjectAddress}",
                    "Job No: _____________________________": f"Job No: {st.session_state.JobNumber}",
                    "[Maker of check]": st.session_state.CustomerName,
                    "[Amount of Check]": st.session_state.PaymentAmount,
                    "[Payee or Payees of Check]": st.session_state.LienorName,
                    "[Owner]": st.session_state.OwnerName,
                    "[Job Description]": st.session_state.PropertyDescription,
                    "[Person with whom undersigned contracted]": st.session_state.CustomerName
                }
                
                for p in doc.paragraphs:
                    for key, val in replacements.items():
                        if key in p.text:
                            p.text = p.text.replace(key, val)
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp_path = tmp.name
                    doc.save(tmp_path)
                
                display_name = f"Lienify_AZ_{ptype}_{'Conditional' if cond=='Yes' else 'Unconditional'}_{datetime.today().strftime('%Y%m%d')}.docx"
                with open(tmp_path, "rb") as f:
                    st.download_button("Download Filled Waiver (.docx)", data=f, file_name=display_name, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
