import streamlit as st

# Page title
st.title("Cloud Infrastructure Deployment")

# Cloud Provider Selection
cloud_provider = st.selectbox("Select Cloud Provider:", ["AWS", "Azure", "GCP"])

# Upload Configuration File
uploaded_file = st.file_uploader("Upload Configuration File", type=["json", "yaml"])

if uploaded_file:
    st.success("File uploaded successfully!")

# Button to trigger Terraform Deployment
if st.button("Deploy Infrastructure"):
    st.write(f"Deploying on {cloud_provider}... (Terraform execution will be handled here)")