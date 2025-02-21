# Streamlit Terraform App

## 🚀 Overview
This project is a **Streamlit-based web application** that allows users to:
- Select infrastructure details via UI.
- Upload a file with configuration details.
- Get cloud optimization recommendations based on the use case.
- Deploy infrastructure with one click using Terraform in the backend.

## 📁 Project Structure
streamlit-terraform-app/ 
  │── app/ # Streamlit app source code
  ├── pages/ # Additional multi-page support (optional) 
  ├── assets/ # Static assets (images, icons, etc.) 
  ├── main.py # Main Streamlit app file 
  ├── config_parser.py # File handling logic 
  │── infra/ # Terraform configurations 
  ├── main.tf # Main Terraform script
  ├── variables.tf # Terraform variables
  ├── outputs.tf # Terraform outputs 
  │── .gitignore # Ignore unnecessary files 
  │── requirements.txt # Python dependencies 
  │── README.md # Project documentation

  
## 🛠️ Setup Instructions

### 1️⃣ Prerequisites
Ensure you have the following installed:
- **Python 3.8+**: [Download](https://www.python.org/downloads/)
- **Terraform CLI**: [Install Guide](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
- **Streamlit**: `pip install streamlit`
- **Cloud SDKs** (AWS CLI, Azure CLI, GCP SDK) as needed

### 2️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/streamlit-terraform-app.git
cd streamlit-terraform-app```

### 3️⃣ Set Up Virtual Environment
```bash
Copy
Edit
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt```
