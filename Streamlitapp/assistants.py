#  # Importing required packages
# import streamlit as st
# import openai
# import uuid
# import time
# import pandas as pd
# import io
# from openai import OpenAI

# # Initialize OpenAI client
# client = OpenAI()

# # Your chosen model
# MODEL = "gpt-4-1106-preview"

# # Initialize session state variables
# if "session_id" not in st.session_state:
#     st.session_state.session_id = str(uuid.uuid4())

# if "run" not in st.session_state:
#     st.session_state.run = {"status": None}

# if "messages" not in st.session_state:
#     st.session_state.messages = []

# if "retry_error" not in st.session_state:
#     st.session_state.retry_error = 0

# # Set up the page
# st.set_page_config(page_title="Enter title here")
# st.sidebar.title("Title")
# st.sidebar.divider()
# st.sidebar.markdown("Your name", unsafe_allow_html=True)
# st.sidebar.markdown("Assistant GPT")
# st.sidebar.divider()

# # File uploader for CSV, XLS, XLSX
# uploaded_file = st.file_uploader("Upload your file", type=["csv", "xls", "xlsx"])

# if uploaded_file is not None:
#     # Determine the file type
#     file_type = uploaded_file.type

#     try:
#         # Read the file into a Pandas DataFrame
#         if file_type == "text/csv":
#             df = pd.read_csv(uploaded_file)
#         elif file_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
#             df = pd.read_excel(uploaded_file)

#         # Convert DataFrame to JSON
#         json_str = df.to_json(orient='records', indent=4)
#         file_stream = io.BytesIO(json_str.encode())

#         # Upload JSON data to OpenAI and store the file ID
#         file_response = client.files.create(file=file_stream, purpose='answers')
#         st.session_state.file_id = file_response.id
#         st.success("File uploaded successfully to OpenAI!")

#         # Optional: Display and Download JSON
#         st.text_area("JSON Output", json_str, height=300)
#         st.download_button(label="Download JSON", data=json_str, file_name="converted.json", mime="application/json")
    
#     except Exception as e:
#         st.error(f"An error occurred: {e}")

# # Initialize OpenAI assistant
# if "assistant" not in st.session_state:
#     openai.api_key = st.secrets["OPENAI_API_KEY"]
#     st.session_state.assistant = openai.beta.assistants.retrieve(st.secrets["OPENAI_ASSISTANT"])
#     st.session_state.thread = client.beta.threads.create(
#         metadata={'session_id': st.session_state.session_id}
#     )

# # Display chat messages
# elif hasattr(st.session_state.run, 'status') and st.session_state.run.status == "completed":
#     st.session_state.messages = client.beta.threads.messages.list(
#         thread_id=st.session_state.thread.id
#     )
#     for message in reversed(st.session_state.messages.data):
#         if message.role in ["user", "assistant"]:
#             with st.chat_message(message.role):
#                 for content_part in message.content:
#                     message_text = content_part.text.value
#                     st.markdown(message_text)

# # Chat input and message creation with file ID
# if prompt := st.chat_input("How can I help you?"):
#     with st.chat_message('user'):
#         st.write(prompt)

#     message_data = {
#         "thread_id": st.session_state.thread.id,
#         "role": "user",
#         "content": prompt
#     }

#     # Include file ID in the request if available
#     if "file_id" in st.session_state:
#         message_data["file_ids"] = [st.session_state.file_id]

#     st.session_state.messages = client.beta.threads.messages.create(**message_data)

#     st.session_state.run = client.beta.threads.runs.create(
#         thread_id=st.session_state.thread.id,
#         assistant_id=st.session_state.assistant.id,
#     )
#     if st.session_state.retry_error < 3:
#         time.sleep(1)
#         st.rerun()

# # Handle run status
# if hasattr(st.session_state.run, 'status'):
#     if st.session_state.run.status == "running":
#         with st.chat_message('assistant'):
#             st.write("Thinking ......")
#         if st.session_state.retry_error < 3:
#             time.sleep(1)
#             st.rerun()

#     elif st.session_state.run.status == "failed":
#         st.session_state.retry_error += 1
#         with st.chat_message('assistant'):
#             if st.session_state.retry_error < 3:
#                 st.write("Run failed, retrying ......")
#                 time.sleep(3)
#                 st.rerun()
#             else:
#                 st.error("FAILED: The OpenAI API is currently processing too many requests. Please try again later ......")

#     elif st.session_state.run.status != "completed":
#         st.session_state.run = client.beta.threads.runs.retrieve(
#             thread_id=st.session_state.thread.id,
#             run_id=st.session_state.run.id,
#         )
#         if st.session_state.retry_error < 3:
#             time.sleep(3)
#             st.rerun()


# Set up the client

# Import necessary libraries
import openai
import os
import streamlit as st

# Initialize OpenAI client with your API key
client = openai.OpenAI(
    api_key=("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")
)

# Streamlit app
def main():
    st.title("OpenAI Assistant Interaction")

    # Declare the Assistant's ID (Replace with your assistant's ID)
    assistant_id = "asst_dI7dY8RaoEmARWfNGhTcG8jy"

    # Streamlit input for user's question
    user_question = st.text_input("Enter your question:", "")

    if st.button("Submit"):
        # Fetch the assistant
        assistant = client.beta.assistants.retrieve(
            assistant_id=assistant_id
        )

        # Create a thread
        thread = client.beta.threads.create()

        # Prompt the model with the user's question
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions=user_question
        )

        # Wait for the run to complete (this is a simple check, might need more robust handling)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

        # Fetch and display the latest message
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        st.write("Response:", messages.data[0].content[0])

# Run the Streamlit app
if __name__ == "__main__":
    main()


# from openai import OpenAI
# import shelve
# from dotenv import load_dotenv
# import os
# import time

# load_dotenv()
# OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
# client = OpenAI(api_key=OPEN_AI_API_KEY)


# # --------------------------------------------------------------
# # Upload file
# # --------------------------------------------------------------
# def upload_file(path):
#     # Upload a file with an "assistants" purpose
#     file = client.files.create(file=open(path, "rb"), purpose="assistants")
#     return file


# file = upload_file("../data/airbnb-faq.pdf")


# # --------------------------------------------------------------
# # Create assistant
# # --------------------------------------------------------------
# def create_assistant(file):
#     """
#     You currently cannot set the temperature for Assistant via the API.
#     """
#     assistant = client.beta.assistants.create(
#         name="WhatsApp AirBnb Assistant",
#         instructions="You're a helpful WhatsApp assistant that can assist guests that are staying in our Paris AirBnb. Use your knowledge base to best respond to customer queries. If you don't know the answer, say simply that you cannot help with question and advice to contact the host directly. Be friendly and funny.",
#         tools=[{"type": "retrieval"}],
#         model="gpt-4-1106-preview",
#         file_ids=[file.id],
#     )
#     return assistant


# assistant = create_assistant(file)


# # --------------------------------------------------------------
# # Thread management
# # --------------------------------------------------------------
# def check_if_thread_exists(wa_id):
#     with shelve.open("threads_db") as threads_shelf:
#         return threads_shelf.get(wa_id, None)


# def store_thread(wa_id, thread_id):
#     with shelve.open("threads_db", writeback=True) as threads_shelf:
#         threads_shelf[wa_id] = thread_id


# # --------------------------------------------------------------
# # Generate response
# # --------------------------------------------------------------
# def generate_response(message_body, wa_id, name):
#     # Check if there is already a thread_id for the wa_id
#     thread_id = check_if_thread_exists(wa_id)

#     # If a thread doesn't exist, create one and store it
#     if thread_id is None:
#         print(f"Creating new thread for {name} with wa_id {wa_id}")
#         thread = client.beta.threads.create()
#         store_thread(wa_id, thread.id)
#         thread_id = thread.id

#     # Otherwise, retrieve the existing thread
#     else:
#         print(f"Retrieving existing thread for {name} with wa_id {wa_id}")
#         thread = client.beta.threads.retrieve(thread_id)

#     # Add message to thread
#     message = client.beta.threads.messages.create(
#         thread_id=thread_id,
#         role="user",
#         content=message_body,
#     )

#     # Run the assistant and get the new message
#     new_message = run_assistant(thread)
#     print(f"To {name}:", new_message)
#     return new_message


# # --------------------------------------------------------------
# # Run assistant
# # --------------------------------------------------------------
# def run_assistant(thread):
#     # Retrieve the Assistant
#     assistant = client.beta.assistants.retrieve("asst_7Wx2nQwoPWSf710jrdWTDlfE")

#     # Run the assistant
#     run = client.beta.threads.runs.create(
#         thread_id=thread.id,
#         assistant_id=assistant.id,
#     )

#     # Wait for completion
#     while run.status != "completed":
#         # Be nice to the API
#         time.sleep(0.5)
#         run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

#     # Retrieve the Messages
#     messages = client.beta.threads.messages.list(thread_id=thread.id)
#     new_message = messages.data[0].content[0].text.value
#     print(f"Generated message: {new_message}")
#     return new_message


# # --------------------------------------------------------------
# # Test assistant
# # --------------------------------------------------------------

# new_message = generate_response("What's the check in time?", "123", "John")

# new_message = generate_response("What's the pin for the lockbox?", "456", "Sarah")

# new_message = generate_response("What was my previous question?", "123", "John")

# new_message = generate_response("What was my previous question?", "456", "Sarah")