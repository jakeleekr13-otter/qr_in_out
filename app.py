import streamlit as st

st.set_page_config(
    page_title="QR In/Out System",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 QR In/Out System")

st.markdown("""
Welcome to the QR In/Out System! This application allows you to manage checkpoints and track visitor entries and exits via QR codes.

### Pages:
- **👤 Admin**: Manage checkpoints, guests, and view activity logs.
- **🖥️ Host**: Display QR codes for visitors to scan.
- **👋 Guest**: Scan QR codes to check in and out.

Please select a page from the sidebar to get started.
""")

st.info("This system runs locally and uses JSON files for data storage.")
