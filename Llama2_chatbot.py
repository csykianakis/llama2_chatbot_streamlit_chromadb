import streamlit as st
import streamlit as st
from streamlit_jupyter import StreamlitPatcher, tqdm
import requests
import os
import chromadb

StreamlitPatcher().jupyter()  # register streamlit with jupyter-compatible wrappers

#Backend
client = chromadb.Client()
collection = client.create_collection("test1")

def read_files_from_folder(folder_path):
    file_data = []

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith(".txt"):
                file_path = os.path.join(root, file_name)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        file_data.append({"file_name": file_name, "content": content})
                except UnicodeDecodeError:
                    print(f"Unable to read {file_name} due to encoding issues.")

    return file_data

folder_path = "C:/Users/xaris/Desktop/Kprojects/IOLO chatbot/data/solutions"
file_data = read_files_from_folder(folder_path)

documents = []
metadatas = []
ids = []

for index, data in enumerate(file_data):
    documents.append(data['content'])
    metadatas.append({'source': data['file_name']})
    ids.append(str(index + 1))

chat_collection = client.create_collection("chat_collection")

chat_collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids)

def result(question):
    results = chat_collection.query(
    query_texts=[question],
    n_results=1)
    
    result_documents = (results['documents'][0][0]).replace('\n', ' ')
    
    question = question
    prompt = f"""<s>[INST] <<SYS>>
             You are a helpful, respectful and honest assistant for IOLO. Always answer as helpfully as possible.
             You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'.

             You must answer all the question based on the given information.
             <</SYS>>

             Based on that information:{result_documents}, answer me this: {question} [/INST]"""
             
#f"""You are a helpful, respectful and honest assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."""
#Answer me this question: {question}."""

    url = "https://2jsbd50vvqnmtt-8000.proxy.runpod.net/v1/completions"
    json = {"model" : "meta-llama/Llama-2-13b-chat-hf",
            "prompt": prompt,
            "max_tokens" : max_length,
            "temperature" : temperature}
    
    response = requests.post(url, json=json)
    if response.status_code == 200:
        response_data = response.json()
        generated_answer = response_data["choices"][0]["text"]
        print(generated_answer)
    else:
        print("Failed code:", response.status_code)
        print("Content:", response.text)

    return(generated_answer)



st.set_page_config(page_title="🦙💬 Llama 2 Chatbot with Streamlit")

with st.sidebar:
    st.title("🦙💬 Llama 2 Chatbot")
    st.header("Settings")
    st.subheader("Models and Parameters")

    temperature=st.slider('temperature', min_value=0.00, max_value=1.0, value=0.0, step=0.01)
    #top_p=st.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length=st.slider('max_length', min_value=32, max_value=256, value=64, step=32)

if "messages" not in st.session_state.keys():
    st.session_state.messages=[{"role": "assistant", "content":"How may I assist you today?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages=[{"role":"assistant", "content": "How may I assist you today"}]

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

if prompt := st.chat_input(disabled=not input):
    st.session_state.messages.append({"role": "user", "content":prompt})
    with st.chat_message("user"):
        st.write(prompt)

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = result(prompt)
            placeholder=st.empty()
            full_response=''
            for item in response:
                full_response+=item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)

    message= {"role":"assistant", "content":full_response}
    st.session_state.messages.append(message)
