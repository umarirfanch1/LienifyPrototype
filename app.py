# app.py - Lienify Arizona Lien & Waiver Form Generator (Streamlit)
import streamlit as st
import zipfile, os, tempfile
from docx import Document
from datetime import datetime, timedelta

st.set_page_config(page_title="Lienify - Arizona Lien Waiver Generator", layout="centered")

# -------------------
# Utility: unzip templates if needed
# -------------------
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

    # find Arizona folder
    for root, dirs, files in os.walk(EXTRACT_BASE):
        if "arizona" in os.path.basename(root).lower() or "arizona" in root.lower():
            return root
    return None

AZ_FOLDER = ensure_templates()
if not AZ_FOLDER:
    st.error("Arizona folder not found inside ZIP. Make sure it exists and named correctly.")
    st.stop()

# Template mapping
TEMPLATE_MAP = {
    ("Progress", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Progress", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Final", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
    ("Final", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
}

def find_template_file(filename):
    for f in os.listdir(AZ_FOLDER):
        if filename.replace(".pdf","").lower() in f.lower():
            return os.path.join(AZ_FOLDER, f)
    return None

# -------------------
# Session state setup
# -------------------
if "step" not in st.session_state:
    st.session_state.step = 0

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step = max(0, st.session_state.step - 1)

# -------------------
# Step 0: Welcome / State selection
# -------------------
if st.session_state.step == 0:
    st.markdown("# Lienify – Lien & Waiver Form Generator")
    st.write("Welcome to Lienify. Prototype by Muhammad Umar Irfan.")
    st.write("Please select your state to continue.")
    
    STATES = ["Arizona","California","Nevada","Texas","Florida","Georgia","Washington","Oregon","Colorado","Utah","New Mexico","Idaho"]
    state = st.selectbox("Select State", [""] + STATES, key="state_select")
    
    if state:
        if state != "Arizona":
            st.warning("Currently only Arizona is supported for testing. Please select Arizona.")
        else:
            st.session_state.state = state
            next_step()

# -------------------
# Step 1: Arizona Compliance Check
# -------------------
elif st.session_state.step == 1:
    st.markdown("# Lienify – Lien & Waiver Form Generator")
    st.subheader("Arizona Compliance Summary")
    st.info("""
Thanks for selecting Arizona. Have a look at compliance check before we proceed:

- Preliminary Notice: must be sent within 20 days of first delivery.
- Conditional waivers bind upon evidence of payment; Unconditional bind upon signing.
- Waiving lien rights before performing work is illegal.
- Unlicensed contractors may lose lien rights.
- Stop notices allowed on private projects (except owner-occupied dwellings).
- Payment bonds, tenant-as-agent, highway projects and UPL rules may affect lien eligibility.
    """)
    if st.button("Yes, I understand. Please proceed", key="compliance_next"):
        next_step()

# -------------------
# Step 2: Role selection (one question per screen)
# -------------------
elif st.session_state.step == 2:
    st.markdown("# Lienify – Lien & Waiver Form Generator")
    st.subheader("Step 1 — Your Role")
    role = st.selectbox("Select your role on this project", ["","Contractor","Subcontractor","Supplier","Material Provider"], key="role")
    if role:
        st.session_state.role = role
        next_step()
    if st.button("Back", key="back_role"):
        prev_step()

# -------------------
# Step 3: Payment Type
# -------------------
elif st.session_state.step == 3:
    st.markdown("# Lienify – Lien & Waiver Form Generator")
    st.subheader("Step 2 — Payment Type")
    payment_type = st.radio("Is this waiver for a Progress or Final payment?", ["","Progress","Final"], key="payment_type")
    if payment_type:
        st.session_state.payment_type = payment_type
        next_step()
    if st.button("Back", key="back_payment_type"):
        prev_step()

# -------------------
# Step 4: Payment Received
# -------------------
elif st.session_state.step == 4:
    st.markdown("# Lienify – Lien & Waiver Form Generator")
    st.subheader("Step 3 — Payment Status")
    payment_received = st.radio("Has payment been received for this waiver?", ["","Yes","No"], key="payment_received")
    if payment_received:
        st.session_state.payment_received = payment_received
        next_step()
    if st.button("Back", key="back_payment_received"):
        prev_step()

# -------------------
# Step 5: First Delivery Date
# -------------------
elif st.session_state.step == 5:
    st.markdown("# Lienify – Lien & Waiver Form Generator")
    st.subheader("Step 4 — Preliminary Notice")
    first_delivery = st.date_input("First Delivery Date (required)", key="first_delivery")
    if first_delivery:
        st.session_state.first_delivery = first_delivery
        st.info(f"Preliminary Notice deadline: {(first_delivery + timedelta(days=20)).strftime('%Y-%m-%d')}")
        if st.button("Next →", key="next_first_delivery"):
            next_step()
    if st.button("Back", key="back_first_delivery"):
        prev_step()

# -------------------
# Step 6: Project & Payment Details
# -------------------
elif st.session_state.step == 6:
    st.markdown("# Lienify – Lien & Waiver Form Generator")
    st.subheader("Step 5 — Project & Payment Details")
    st.write("Please fill out all required fields.")
    
    OwnerName = st.text_input("Owner Name", key="owner_name")
    ProjectAddress = st.text_input("Project / Job Address", key="project_address")
    CustomerName = st.text_input("Customer / Paying Entity Name", key="customer_name")
    LienorName = st.text_input("Lienor / Contractor / Provider Name", key="lienor_name")
    LicenseNumber = st.text_input("Contractor / Lienor License Number", key="license_number")
    PaymentAmount_num = st.number_input("Payment Amount ($)", min_value=0.0, format="%.2f", key="payment_amount")

    WorkThroughDate = None
    if st.session_state.payment_type == "Progress":
        WorkThroughDate = st.date_input("Work Through Date (required for Progress payments)", key="work_through")
    else:
        WorkThroughDate = st.date_input("Work Through Date (optional)", key="work_through")
    
    ExecutionDate = st.date_input("Execution Date (when waiver is signed)", value=datetime.today(), key="execution_date")
    JobNumber = st.text_input("Job / Project Number", key="job_number")
    PropertyDescription = st.text_area("Property Description / Legal Description", key="property_description")

    required_fields = [OwnerName, ProjectAddress, CustomerName, LienorName, LicenseNumber, PaymentAmount_num, ExecutionDate, JobNumber, PropertyDescription]
    all_filled = all(required_fields) and (WorkThroughDate if st.session_state.payment_type=="Progress" else True)

    cols = st.columns([1,1])
    with cols[0]:
        if st.button("Back", key="back_project"):
            prev_step()
    with cols[1]:
        if all_filled:
            if st.button("Next →", key="next_project"):
                # save into session
                st.session_state.OwnerName = OwnerName
                st.session_state.ProjectAddress = ProjectAddress
                st.session_state.CustomerName = CustomerName
                st.session_state.LienorName = LienorName
                st.session_state.LicenseNumber = LicenseNumber
                st.session_state.PaymentAmount = f"${PaymentAmount_num:,.2f}"
                st.session_state.WorkThroughDate = WorkThroughDate
                st.session_state.ExecutionDate = ExecutionDate
                st.session_state.JobNumber = JobNumber
                st.session_state.PropertyDescription = PropertyDescription
                next_step()
        else:
            st.button("Next → (disabled)", key="next_project_disabled", disabled=True)

# -------------------
# Step 7: Review & Generate Form
# -------------------
elif st.session_state.step == 7:
    st.markdown("# Lienify – Lien & Waiver Form Generator")
    st.subheader("Step 6 — Generate Form")

    ptype = st.session_state.payment_type
    paid = st.session_state.payment_received
    cond = "Yes" if paid=="No" else "No"
    template_file = TEMPLATE_MAP.get((ptype, cond))
    st.write(f"Based on your selection, the form required is: **{template_file}**")
    st.write("Click generate to create the form with your details filled.")

    cols = st.columns([1,1])
    with cols[0]:
        if st.button("Back", key="back_generate"):
            prev_step()
    with cols[1]:
        if st.button("Generate & Download", key="generate_doc"):
            template_path = find_template_file(template_file)
            if not template_path:
                st.error("Template not found!")
            else:
                with st.spinner("Please wait, your form is being generated..."):
                    doc = Document(template_path)
                    # Manual mapping by scanning lines
                    # Since no placeholders exist, we simply append details at the top or inject manually
                    # For simplicity, we replace the first few underscores (you can adjust as needed)
                    for p in doc.paragraphs:
                        text = p.text
                        text = text.replace("_____________________________", st.session_state.ProjectAddress)
                        text = text.replace("[Maker of check]", st.session_state.CustomerName)
                        text = text.replace("[Amount of Check]", st.session_state.PaymentAmount)
                        text = text.replace("[Payee or Payees of Check]", st.session_state.LienorName)
                        text = text.replace("[Owner]", st.session_state.OwnerName)
                        text = text.replace("[Job Description]", st.session_state.PropertyDescription)
                        p.text = text

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                        doc.save(tmp.name)
                        tmp_path = tmp.name

                    display_name = f"Lienify_AZ_{ptype}_{'Conditional' if cond=='Yes' else 'Unconditional'}_{datetime.today().strftime('%Y%m%d')}.docx"
                    with open(tmp_path, "rb") as f:
                        st.download_button("Download Filled Waiver (.docx)", data=f, file_name=display_name,
                                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    st.success("Form generated successfully with your entered details.")
