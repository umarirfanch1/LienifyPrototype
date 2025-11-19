# app.py - Lienify Arizona Lien & Waiver Form Generator (Streamlit)
import streamlit as st
import zipfile, os, tempfile
from docx import Document
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="Lienify - Arizona Lien Waiver Generator", layout="centered")

# -------------------------
# Config: ZIP name and extraction base
# -------------------------
ZIP_NAME = "02_Templates-20251119T041237Z-1-001.zip"  # update if different
EXTRACT_BASE = "02_Templates_extracted"

# -------------------------
# Helpers: template handling
# -------------------------
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
    return None

AZ_FOLDER = ensure_templates()
if not AZ_FOLDER:
    st.error("Arizona template folder not found inside ZIP. Make sure 'Arizona' folder exists in the uploaded ZIP.")
    st.stop()

TEMPLATE_MAP = {
    ("Progress", "Yes"): "CONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Progress", "No"):  "UNCONDITIONAL WAIVER AND RELEASE ON PROGRESS PAYMENT.pdf",
    ("Final", "Yes"):    "CONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
    ("Final", "No"):     "UNCONDITIONAL WAIVER AND RELEASE ON FINAL PAYMENT.pdf",
}

def find_template_file(expected_name):
    basename = expected_name.replace(".pdf","").lower()
    for f in os.listdir(AZ_FOLDER):
        if basename in f.lower():
            return os.path.join(AZ_FOLDER, f)
    return None

def try_open_docx(path):
    """
    Try to open a path as a docx Document. If path ends with .pdf but actually
    there's a .docx with same base name, try that. Return Document or raise.
    """
    try:
        return Document(path)
    except Exception:
        # try swap extension to .docx
        base, ext = os.path.splitext(path)
        alt = base + ".docx"
        if os.path.exists(alt):
            return Document(alt)
        raise

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

# -------------------------
# Session state initialization
# -------------------------
if "step" not in st.session_state:
    st.session_state.step = 0
if "show_state_select" not in st.session_state:
    st.session_state.show_state_select = False

# helpful navigation
def go_next():
    st.session_state.step += 1

def go_back():
    st.session_state.step = max(0, st.session_state.step - 1)

# UX header displayed after welcome
def render_header():
    st.markdown("# Lienify — Lien and Waiver form generator")
    st.markdown("Please fill out required form *")

# small helper to parse "$" amount input like "$1,234.56"
def parse_currency_input(s):
    if s is None:
        return None
    s = s.strip()
    if s == "":
        return None
    s = s.replace("$", "").replace(",", "")
    try:
        return float(s)
    except:
        return None

# -------------------------
# Step 0: Welcome + "Select your state" button
# -------------------------
if st.session_state.step == 0:
    st.markdown("# Welcome to Lienify Waiver and Lien Form Generator")
    if st.button("Select your state"):
        st.session_state.show_state_select = True

    if st.session_state.show_state_select:
        STATES = ["Arizona","California","Nevada","Texas","Florida","Georgia","Washington","Oregon","Colorado","Utah","New Mexico","Idaho"]
        state = st.selectbox("Choose state", [""] + STATES, key="state_select")
        if state:
            st.session_state.state = state
            if state != "Arizona":
                st.warning("Only Arizona is open for testing right now. Please select Arizona to continue.")
            else:
                # auto advance to compliance screen
                st.success("Thanks for selecting Arizona. Proceeding...")
                st.session_state.step = 1

# -------------------------
# Step 1: Compliance screen (only once, after selecting AZ)
# -------------------------
elif st.session_state.step == 1:
    render_header()
    st.markdown("**Thanks for selecting Arizona — have a look at compliance check before we proceed**")
    st.info("""
**Arizona compliance summary (quick):**
- Preliminary Notice: must be sent **within 20 days of first delivery**.  
- Conditional waivers bind upon evidence of payment; Unconditional bind upon signing.  
- Waiving lien rights before performing work is illegal.  
- Unlicensed contractors may lose lien rights.  
- Stop notices allowed on private projects (except owner-occupied dwellings).  
- Payment bonds, tenant-as-agent, highway projects and UPL rules may affect lien eligibility.
""")
    if st.button("Yes, I understood. Please proceed"):
        st.session_state.step = 2

    if st.button("Back"):
        go_back()

# -------------------------
# Steps 2..n : Single-question flow (one item per page, auto-advance)
# We'll map steps to fields (order matters).
# -------------------------
else:
    # Define the ordered fields and which step number they map to.
    # step 2 -> role, 3 -> payment_type, 4 -> payment_received, 5 -> first_delivery,
    # 6 -> WorkThroughDate (if Progress), 7 -> OwnerName, 8 -> ProjectAddress, 9 -> CustomerName,
    # 10 -> LienorName, 11 -> LicenseNumber, 12 -> PaymentAmount, 13 -> ExecutionDate,
    # 14 -> JobNumber, 15 -> PropertyDescription, 16 -> Review & Generate
    field_order = [
        "role", "payment_type", "payment_received", "first_delivery",
        "work_through_date", "OwnerName", "ProjectAddress", "CustomerName",
        "LienorName", "LicenseNumber", "PaymentAmount", "ExecutionDate",
        "JobNumber", "PropertyDescription"
    ]

    # compute the index into field_order
    idx = st.session_state.step - 2
    # clamp
    if idx < 0:
        st.session_state.step = 2
        idx = 0
    if idx >= len(field_order):
        # all done -> Review & Generate
        st.session_state.step = 16

    # Render the header each page
    render_header()

    # helper to advance once a value is set
    def set_and_next(key, value):
        st.session_state[key] = value
        # advance
        st.session_state.step += 1

    # field: role
    if st.session_state.step == 2:
        val = st.selectbox("Your role on this project (required)", ["", "Contractor","Subcontractor","Supplier","Material Provider"], key="role_input")
        if val:
            set_and_next("role", val)
        if st.button("Back"):
            go_back()

    # payment_type
    elif st.session_state.step == 3:
        val = st.radio("Is this waiver for a Progress or Final payment? (required)", ("","Progress","Final"), key="payment_type_input")
        if val:
            set_and_next("payment_type", val)
        if st.button("Back"):
            go_back()

    # payment_received
    elif st.session_state.step == 4:
        val = st.radio("Has payment been received for this waiver? (required)", ("","Yes","No"), key="payment_received_input")
        if val:
            set_and_next("payment_received", val)
        if st.button("Back"):
            go_back()

    # first_delivery (date) - required; show PN calculation in same page
    elif st.session_state.step == 5:
        fd = st.date_input("First Delivery Date (required — used to calculate Preliminary Notice deadline)", key="first_delivery_input")
        if fd:
            st.session_state.first_delivery = fd
            pn_deadline = fd + timedelta(days=20)
            st.write(f"Preliminary Notice deadline = {pn_deadline.strftime('%Y-%m-%d')}")
            # next
            if st.button("Save & Continue"):
                st.session_state.step += 1
        if st.button("Back"):
            go_back()

    # WorkThroughDate (only required for Progress)
    elif st.session_state.step == 6:
        # Only ask this if payment_type == Progress; else skip automatically
        if st.session_state.get("payment_type") != "Progress":
            st.session_state.step += 1
            st.experimental_rerun()
        wtd = st.date_input("Work Through Date (required for Progress payments)", key="work_through_input")
        if wtd:
            set_and_next("work_through_date", wtd)
        if st.button("Back"):
            go_back()

    # OwnerName
    elif st.session_state.step == 7:
        v = st.text_input("Owner Name (required)", key="OwnerName_input")
        if v and v.strip():
            set_and_next("OwnerName", v.strip())
        if st.button("Back"):
            go_back()

    # ProjectAddress
    elif st.session_state.step == 8:
        v = st.text_input("Project / Job Address (required)", key="ProjectAddress_input")
        if v and v.strip():
            set_and_next("ProjectAddress", v.strip())
        if st.button("Back"):
            go_back()

    # CustomerName
    elif st.session_state.step == 9:
        v = st.text_input("Customer / Paying Entity Name (required)", key="CustomerName_input")
        if v and v.strip():
            set_and_next("CustomerName", v.strip())
        if st.button("Back"):
            go_back()

    # LienorName
    elif st.session_state.step == 10:
        v = st.text_input("Lienor / Contractor / Provider Name (required)", key="LienorName_input")
        if v and v.strip():
            set_and_next("LienorName", v.strip())
        if st.button("Back"):
            go_back()

    # LicenseNumber
    elif st.session_state.step == 11:
        v = st.text_input("Contractor / Lienor License Number (required)", key="LicenseNumber_input")
        if v and v.strip():
            set_and_next("LicenseNumber", v.strip())
        if st.button("Back"):
            go_back()

    # PaymentAmount - single field with $ in placeholder
    elif st.session_state.step == 12:
        v = st.text_input("Payment Amount (required). Include $ sign if you like. Example: $1,234.56", placeholder="$0.00", key="PaymentAmount_input")
        parsed = parse_currency_input(v)
        if v and parsed is not None:
            # store standardized string with $ and comma formatting
            st.session_state.PaymentAmount = "${:,.2f}".format(parsed)
            set_and_next("PaymentAmount", st.session_state.PaymentAmount)
        else:
            if v and parsed is None:
                st.error("Payment value not recognised. Use numeric format like $1234.56 or 1234.56")
        if st.button("Back"):
            go_back()

    # ExecutionDate
    elif st.session_state.step == 13:
        ed = st.date_input("Execution Date (required — when waiver is signed)", value=datetime.today(), key="ExecutionDate_input")
        if ed:
            set_and_next("ExecutionDate", ed)
        if st.button("Back"):
            go_back()

    # JobNumber
    elif st.session_state.step == 14:
        v = st.text_input("Job / Project Number (required)", key="JobNumber_input")
        if v and v.strip():
            set_and_next("JobNumber", v.strip())
        if st.button("Back"):
            go_back()

    # PropertyDescription
    elif st.session_state.step == 15:
        v = st.text_area("Property Description / Legal Description (required)", height=150, key="PropertyDescription_input")
        if v and v.strip():
            set_and_next("PropertyDescription", v.strip())
        if st.button("Back"):
            go_back()

    # Review & Generate
    elif st.session_state.step == 16:
        st.subheader("Review & Generate")
        # natural layout summary
        st.markdown("Below are the details you provided. If everything looks correct, press **Generate & Download** to create your filled waiver form.")
        summary_display = {
            "Owner Name": st.session_state.get("OwnerName",""),
            "Project Address": st.session_state.get("ProjectAddress",""),
            "Customer / Paying Entity": st.session_state.get("CustomerName",""),
            "Lienor / Contractor": st.session_state.get("LienorName",""),
            "License Number": st.session_state.get("LicenseNumber",""),
            "Payment Amount": st.session_state.get("PaymentAmount",""),
            "Work Through Date": (st.session_state.get("work_through_date").strftime("%B %d, %Y") if st.session_state.get("work_through_date") else "N/A"),
            "Execution Date": (st.session_state.get("ExecutionDate").strftime("%B %d, %Y") if st.session_state.get("ExecutionDate") else ""),
            "Job / Project Number": st.session_state.get("JobNumber",""),
            "Property Description": st.session_state.get("PropertyDescription",""),
            "First Delivery Date": (st.session_state.get("first_delivery").strftime("%B %d, %Y") if st.session_state.get("first_delivery") else "")
        }
        # show nicely
        for k,v in summary_display.items():
            st.markdown(f"**{k}:** {v}")

        cols = st.columns([1,1,1])
        with cols[0]:
            if st.button("Back"):
                st.session_state.step = 15
        with cols[2]:
            if st.button("Generate & Download"):
                # choose template name and find it
                ptype = st.session_state.get("payment_type","Progress")
                paid = st.session_state.get("payment_received","No")
                cond = "Yes" if paid == "No" else "No"  # conditional if payment not received
                template_key = (ptype, cond)
                selected_filename = TEMPLATE_MAP.get(template_key)
                template_path = find_template_file(selected_filename)
                if not template_path:
                    st.error("Template file could not be found in Arizona folder.")
                else:
                    # attempt to open as docx (supports case where file is .pdf but actual docx exists)
                    try:
                        doc = try_open_docx(template_path)
                    except Exception as e:
                        st.error("Could not open the template as a Word (.docx) file. Automatic filling requires a .docx template. If your template is a Word file but named .pdf, place a .docx version in the Arizona folder with same base name.")
                        st.stop()

                    mapping = {
                        "{{OwnerName}}": st.session_state.get("OwnerName",""),
                        "{{ProjectAddress}}": st.session_state.get("ProjectAddress",""),
                        "{{CustomerName}}": st.session_state.get("CustomerName",""),
                        "{{LienorName}}": st.session_state.get("LienorName",""),
                        "{{LicenseNumber}}": st.session_state.get("LicenseNumber",""),
                        "{{PaymentAmount}}": st.session_state.get("PaymentAmount",""),
                        "{{WorkThroughDate}}": (st.session_state.get("work_through_date").strftime("%B %d, %Y") if st.session_state.get("work_through_date") else ""),
                        "{{ExecutionDate}}": (st.session_state.get("ExecutionDate").strftime("%B %d, %Y") if st.session_state.get("ExecutionDate") else ""),
                        "{{AuthorizedRep}}": st.session_state.get("AuthorizedRep","") if "AuthorizedRep" in st.session_state else "",
                        "{{JobNumber}}": st.session_state.get("JobNumber",""),
                        "{{PropertyDescription}}": st.session_state.get("PropertyDescription",""),
                        "{{FirstDeliveryDate}}": (st.session_state.get("first_delivery").strftime("%B %d, %Y") if st.session_state.get("first_delivery") else "")
                    }

                    replace_all(doc, mapping)

                    # save and offer download
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                        tmp_path = tmp.name
                        doc.save(tmp_path)
                    display_name = f"Lienify_AZ_{ptype}_{'Conditional' if cond=='Yes' else 'Unconditional'}_{datetime.today().strftime('%Y%m%d')}.docx"
                    with open(tmp_path, "rb") as f:
                        st.download_button("Download Filled Waiver (.docx)", data=f, file_name=display_name, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    st.success("Generated document includes all provided details.")
