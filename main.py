import time
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template(
    """
    Write an email for sending to {recipient_name} whose email address is {recipient_email}.
        Include following details while drafting the email body: {body_context}
    """
)


model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

st.title("Email Generator")

email_result = {}
formatted_prompt = ""

col1, col2 = st.columns(2, gap="large")
with col1:
    email = st.text_input("Recipient Email", value="dev@dum.com")
    name = st.text_input("Recipient Name", value="Dev Dummy")
    body_context = st.text_area("What would you like to type?", value="I want the leave of 3 days from college please grant me.")
    formatted_prompt = prompt.format(recipient_name=name, recipient_email=email, body_context=body_context)
    generate_btn = st.button("Generate", type="primary", width="stretch")

if generate_btn:
    with col2:
        with st.spinner("Generating..."):
            email_result["body"] = model.invoke(formatted_prompt).content
        # st.write("**Subject:**" + (email_result["subject"] or "No subject given"))
        st.markdown(email_result["body"] or "Error")
        st.toast("Generated!", icon="🎉")
