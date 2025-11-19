# app.py - Lienify Arizona Lien & Waiver Form Generator (Streamlit)
import streamlit as st
from datetime import datetime, timedelta
import zipfile, os, tempfile
from docx import Document

st.set_page_config(page_title="Lienify – Arizona Lien Waiver Generator", layout="centered")

# -------------------------
# Utility: unzip templates if needed
# -------------------------
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
        if os.path.basename(root).lower() == "arizona":
            return root
    return None

AZ_FOLDER = ensure_templates()
if not AZ_FOLDER:
    st.error("Arizona folder not found inside ZIP")
    st.stop()

# Template filenames (docx inside ZIP)
TEMPLATE_MAP = {
    ("Progress", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.docx",
    ("Progress", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.docx",
    ("Final", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.docx",
    ("Final", "No"): "UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.docx",
}

def find_template_file(filename):
    for f in os.listdir(AZ_FOLDER):
        if f.lower() == filename.lower():
            return os.path.join(AZ_FOLDER, f)
    return None

# -------------------------
# Multi-step flow
# -------------------------
if "step" not in st.session_state:
    st.session_state.step = 0

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step = max(0, st.session_state.step - 1)

# -------------------------
# Header function
# -------------------------
def show_header():
    st.markdown("# **Lienify – Lien & Waiver Form Generator**")
    st.markdown("Please fill out all required fields.\n---")

# -------------------------
# Step 0: Welcome & State Selection
# -------------------------
if st.session_state.step == 0:
    show_header()
    st.write("Welcome to **Lienify** — Lien & Waiver Form Generator.")
    STATES = ["Arizona","California","Nevada","Texas","Florida","Georgia","Washington","Oregon","Colorado","Utah","New Mexico","Idaho"]
    state = st.selectbox("Select State", [""] + STATES)
    if state:
        if state != "Arizona":
            st.warning("Currently only Arizona is supported. Please select Arizona to continue.")
        else:
            st.session_state.state = state
            next_step()

# -------------------------
# Step 1: Compliance Reminder
# -------------------------
elif st.session_state.step == 1:
    show_header()
    st.info("""
**Thanks for selecting Arizona. Have a look at compliance check before we proceed:**

- Preliminary Notice: must be sent within 20 days of first delivery.  
- Conditional waivers bind upon evidence of payment; Unconditional bind upon signing.  
- Waiving lien rights before performing work is illegal.  
- Unlicensed contractors may lose lien rights.  
- Stop notices allowed on private projects (except owner-occupied dwellings).  
- Payment bonds, tenant-as-agent, highway projects and UPL rules may affect lien eligibility.
""")
    if st.button("Yes, I understood, please proceed"):
        next_step()

# -------------------------
# Step 2: Pre-Screening (one question per screen)
# -------------------------
elif st.session_state.step in [2,3,4,5]:
    show_header()
    if st.session_state.step == 2:
        q = "Your role on this project"
        options = ["Contractor","Subcontractor","Supplier","Material Provider"]
        ans = st.selectbox(q, [""] + options)
        if ans:
            st.session_state.role = ans
            st.button("Next →", on_click=next_step)
    elif st.session_state.step == 3:
        q = "Is this waiver for a Progress or Final payment?"
        ans = st.radio(q, ["Progress","Final"])
        if ans:
            st.session_state.payment_type = ans
            st.button("Next →", on_click=next_step)
    elif st.session_state.step == 4:
        q = "Has payment been received for this waiver?"
        ans = st.radio(q, ["Yes","No"])
        if ans:
            st.session_state.payment_received = ans
            st.button("Next →", on_click=next_step)
    elif st.session_state.step == 5:
        st.write("Select First Delivery Date (Preliminary Notice calculation)")
        ans = st.date_input("First Delivery Date", value=None)
        if ans:
            st.session_state.first_delivery = ans
            st.button("Next →", on_click=next_step)

# -------------------------
# Step 3: Project & Payment Details
# -------------------------
elif st.session_state.step == 6:
    show_header()
    st.subheader("Project & Payment Details")

    st.session_state.OwnerName = st.text_input("Owner Name")
    st.session_state.ProjectAddress = st.text_input("Project / Job Address")
    st.session_state.CustomerName = st.text_input("Customer / Paying Entity Name")
    st.session_state.LienorName = st.text_input("Lienor / Contractor / Provider Name")
    st.session_state.LicenseNumber = st.text_input("Contractor / Lienor License Number")
    st.session_state.PaymentAmount = st.text_input("Payment Amount (with $)", value="$0.00")
    if st.session_state.payment_type == "Progress":
        st.session_state.WorkThroughDate = st.date_input("Work Through Date (required for Progress payments)")
    else:
        st.session_state.WorkThroughDate = st.date_input("Work Through Date (if applicable)", value=None)
    st.session_state.ExecutionDate = st.date_input("Execution Date", value=datetime.today())
    st.session_state.JobNumber = st.text_input("Job / Project Number")
    st.session_state.PropertyDescription = st.text_area("Property Description / Legal Description", height=100)

    if st.button("Next →"):
        # Simple required validation
        required_fields = ["OwnerName","ProjectAddress","CustomerName","LienorName","LicenseNumber","PaymentAmount","ExecutionDate","JobNumber","PropertyDescription"]
        missing = [f for f in required_fields if not st.session_state.get(f)]
        if missing:
            st.error("Please fill all required fields before proceeding: " + ", ".join(missing))
        else:
            next_step()

# -------------------------
# Step 4: Generate Form
# -------------------------
elif st.session_state.step == 7:
    show_header()
    st.subheader("Generate Your Arizona Lien & Waiver Form")

    ptype = st.session_state.payment_type
    paid = st.session_state.payment_received
    cond = "Yes" if paid=="No" else "No"
    template_file = TEMPLATE_MAP[(ptype, cond)]
    template_path = find_template_file(template_file)

    st.write("Click below to generate your form. Please wait while the form is being prepared…")

    if st.button("Generate Form"):
        if not template_path:
            st.error("Template not found!")
        else:
            doc = Document(template_path)

            # Simple underscore replacement after labels
            def replace_field(paragraph, label, value):
                if label in paragraph.text:
                    paragraph.text = paragraph.text.replace("___________________________", value)

            # Map all fields
            for p in doc.paragraphs:
                replace_field(p, "Project:", st.session_state.ProjectAddress)
                replace_field(p, "Job No:", st.session_state.JobNumber)
                replace_field(p, "[Maker of check]", st.session_state.CustomerName)
                replace_field(p, "[Amount of Check]", st.session_state.PaymentAmount)
                replace_field(p, "[Payee or Payees of Check]", st.session_state.LienorName)
                replace_field(p, "[Owner]", st.session_state.OwnerName)
                replace_field(p, "[Job Description]", st.session_state.PropertyDescription)
                replace_field(p, "[Person with whom undersigned contracted]", st.session_state.CustomerName)

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                doc.save(tmp.name)
                tmp_path = tmp.name

            display_name = f"Lienify_AZ_{ptype}_{'Conditional' if cond=='Yes' else 'Unconditional'}_{datetime.today().strftime('%Y%m%d')}.docx"
            with open(tmp_path, "rb") as f:
                st.download_button("Download Filled Waiver (.docx)", data=f, file_name=display_name,
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

            st.success("Your form has been generated with all provided details!")

# -------------------------
# Footer
# -------------------------
st.markdown("---")
st.markdown("##### © Lienify — Prototype by Muhammad Umar Irfan")
