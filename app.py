import streamlit as st
import requests
import uuid

st.set_page_config(page_title="n8n Chat Agent", page_icon="🤖")

st.title("n8n Chat Agent")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    webhook_url = st.text_input("n8n Webhook URL", placeholder="https://your-n8n-instance.com/webhook/...")
    st.caption("Enter the URL of your n8n Webhook node (POST).")
    if not webhook_url:
        st.warning("Please enter your n8n Webhook URL to start chatting.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    if webhook_url:
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            try:
                # Prepare payload
                # We send chatInput and sessionId which are common patterns for n8n chat workflows
                payload = {
                    "chatInput": prompt,
                    "sessionId": st.session_state.session_id
                }
                
                with st.spinner("Waiting for n8n..."):
                    response = requests.post(webhook_url, json=payload)
                    
                    if response.status_code == 200:
                        # Try to parse JSON response
                        try:
                            data = response.json()
                            # Flexible response handling: check for 'output', 'text', 'message', or just use the whole JSON
                            if isinstance(data, dict):
                                full_response = data.get("output", data.get("text", data.get("message", str(data))))
                            elif isinstance(data, list) and len(data) > 0:
                                # n8n often returns a list of items
                                item = data[0]
                                if isinstance(item, dict):
                                    full_response = item.get("output", item.get("text", str(item)))
                                else:
                                    full_response = str(item)
                            else:
                                full_response = str(data)
                        except ValueError:
                            # If not JSON, use raw text
                            full_response = response.text
                            
                        message_placeholder.markdown(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    else:
                        error_msg = f"Error: {response.status_code} - {response.text}"
                        message_placeholder.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"Connection Error: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
    else:
        st.error("Please configure the Webhook URL in the sidebar.")
