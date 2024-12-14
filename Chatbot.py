import streamlit as st
from pathlib import Path
import base64
from ClientAgent import ClientAgent
from Autogen import Autogen
from Data import Data

# Set page configuration
st.set_page_config(layout="wide")

# Initialize session state
if "generated_pdf_files" not in st.session_state:
    st.session_state["generated_pdf_files"] = {}
if "show_reports" not in st.session_state:
    st.session_state["show_reports"] = False
if "feedback_stage" not in st.session_state:
    st.session_state["feedback_stage"] = None
if "selected_report" not in st.session_state:
    st.session_state["selected_report"] = None
if "client_search_stage" not in st.session_state:
    st.session_state["client_search_stage"] = "initial"
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "matching_clients" not in st.session_state:
    st.session_state["matching_clients"] = []

# Function to search clients by name
def search_clients_by_name(search_name):
    matching_clients = []
    clients = Data.clients
    for client_name, client_info in clients.items():
        if search_name.lower() in client_name.lower():
            personal_info = client_info.get("client_personal_info", {})
            matching_clients.append({
                "name": client_name,
                "address": personal_info.get("address", "N/A"),
                "phone_number": personal_info.get("phone_number", "N/A"),
            })
    return matching_clients

# Function to embed PDF
def embed_pdf(file_path):
    with open(file_path, "rb") as pdf_file:
        base64_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000"></iframe>'
    return pdf_display

# Display chat history
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

# Display initial message if no input has been provided yet
if not st.session_state["messages"]:
    initial_message = "Please enter the client name to start preparing the pre-meeting report."
    st.session_state["messages"].append({"role": "assistant", "content": initial_message})
    st.chat_message("assistant").write(initial_message)

# Single chat input for handling all stages
user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Stage 1: Search for clients by name
    if st.session_state["client_search_stage"] == "initial":
        search_name = user_input.strip()
        matching_clients = search_clients_by_name(search_name)

        if matching_clients:
            st.session_state["matching_clients"] = matching_clients
            st.session_state["client_search_stage"] = "client_list"

            response = "Matching Clients:\n"
            for idx, client_info in enumerate(matching_clients):
                response += f"\n{idx + 1}. Name: {client_info['name']}"
                response += f"\n   Address: {client_info['address']}"
                response += f"\n   Phone Number: {client_info['phone_number']}\n"
            response += "\nPlease enter the serial number of the client you want to verify."

            st.session_state["messages"].append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)
            st.stop()  # 中断执行，等待用户输入
        else:
            st.chat_message("assistant").write(f"No client found with name '{search_name}'. Please try again.")
            st.stop()

    # Stage 2: Verify client by serial number
    elif st.session_state["client_search_stage"] == "client_list":
        try:
            selected_index = int(user_input.strip()) - 1
            if 0 <= selected_index < len(st.session_state["matching_clients"]):
                selected_client = st.session_state["matching_clients"][selected_index]
                selected_client_name = selected_client['name']

                response = f"Verification completed for {selected_client_name}."
                st.session_state["messages"].append({"role": "assistant", "content": response})
                st.chat_message("assistant").write(response)

                st.session_state["current_client_name"] = selected_client_name
                st.session_state["client_search_stage"] = "verified"
                st.session_state["show_reports"] = True
                st.stop()
            else:
                st.chat_message("assistant").write("Invalid serial number. Please try again.")
                st.stop()
        except ValueError:
            st.chat_message("assistant").write("Invalid input. Please enter a valid serial number.")
            st.stop()

    # Generate and display reports
    if st.session_state["show_reports"] and not st.session_state["generated_pdf_files"]:
        client_processor = ClientAgent(st.session_state["current_client_name"])
        processed_client_data = client_processor.process_client_data()
        autogen = Autogen(st.session_state["current_client_name"], processed_client_data)
        report = autogen.generate_report()
        pdf_files = autogen.convert_to_pdf(report)
        st.session_state["generated_pdf_files"] = pdf_files

    # Display reports and prompt for feedback
    if st.session_state["show_reports"] and st.session_state["generated_pdf_files"]:
        for idx, (report_name, file_path) in enumerate(st.session_state["generated_pdf_files"].items()):
            with st.expander(f"{report_name}"):
                pdf_embed_code = embed_pdf(file_path)
                st.markdown(pdf_embed_code, unsafe_allow_html=True)
                st.download_button(
                    label=f"Download {report_name}",
                    data=open(file_path, "rb"),
                    file_name=Path(file_path).name,
                    mime="application/pdf",
                    key=f"download_{idx}"
                )

        if st.session_state["feedback_stage"] is None:
            st.session_state["feedback_stage"] = "select_report"
            st.chat_message("assistant").write("Please select a report number to update (1-3):")
            st.stop()

    # Handle feedback selection
    if st.session_state["feedback_stage"] == "select_report":
        if user_input: 
            try:
                selected_index = int(user_input.strip())
                if selected_index in [1, 2, 3]:
                    st.session_state["selected_report"] = selected_index
                    st.session_state["feedback_stage"] = "provide_feedback"
                    st.chat_message("assistant").write(f"Report {selected_index} selected. Please provide your feedback:")
                    st.stop()
                else:
                    st.chat_message("assistant").write("Invalid selection. Please enter a number between 1 and 3.")
                    st.stop()
            except ValueError:
                st.chat_message("assistant").write("Invalid input. Please enter a valid report number (1-3).")
                st.stop()

    # # Handle feedback submission
    # if st.session_state["feedback_stage"] == "provide_feedback":
    #     st.chat_message("assistant").write("Thank you for your feedback!")
    #     st.session_state["feedback_stage"] = None

    # Handle feedback submission
    if st.session_state["feedback_stage"] == "provide_feedback":
        st.chat_message("assistant").write("Thank you for your feedback!")
        
        selected_index = st.session_state["selected_report"]
        report_name, file_path = list(st.session_state["generated_pdf_files"].items())[selected_index - 1]
        
        st.chat_message("assistant").write(f"Here is the revised version of {report_name}:")
        pdf_embed_code = embed_pdf(file_path)
        st.markdown(pdf_embed_code, unsafe_allow_html=True)

        with open(file_path, "rb") as pdf_file:
            pdf_data = pdf_file.read()
        st.download_button(
            label=f"Download {report_name}",
            data=pdf_data,
            file_name=Path(file_path).name,
            mime="application/pdf",
            key=f"download_feedback_{selected_index}"
        )

        st.session_state["feedback_stage"] = None



