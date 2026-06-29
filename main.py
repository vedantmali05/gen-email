from datetime import date

DUM_DATA = True

from dotenv import load_dotenv

load_dotenv()

from typing import Annotated, Literal

# Prompting
from langchain_core.prompts import PromptTemplate
# Model
from langchain_google_genai import ChatGoogleGenerativeAI
# Structured Output
from pydantic import BaseModel, Field


class Question(BaseModel):
    type: Literal["single_line", "multi_choice", "multi_select", "date_range"]
    question: str
    options: Annotated[
        list[str],
        Field(min_length=2, max_length=5)
    ] | None = None

class AnalysisResponse(BaseModel):
    needs_more_info: bool
    questions: list[Question] | None = None


prompt = PromptTemplate.from_template(
    """
    The user wants to generate an email for the recipient {email_recipient_name} with an email address {email_recipient_email}.
    Current context: {email_body_context}
    Analyse whether the given information is enough to generate a complete and accurate email. Do not assume missing facts or invent details.
    If the information is missing, ask only the most important and relevant follow-up questions. Prefer quick questions:
    - Short-text (one line)
    - Multiple Choice Questions
    - Multiple Select Questions
    Ask only the minimum number of questions required before generating the email. Keep questions short.
    No greetings. No filler. Example: "Leave dates?" not "Could you please provide...".
    The user may skip any question or provide an answer outside the suggested options.
    Today's date: {today}
    """
)

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
structured_model = model.with_structured_output(AnalysisResponse)

# Vars
email_input = {}
analysis_response = {}
updated_info = []
final_results = {}

# UI

if DUM_DATA:
    email_input["name"] = "Charles Xavier"
    email_input["email"] = "principal@college.com"
    email_input["context"] = "I want a 3 days leave from college as I have a Job Interview scheduled."
else: 
    email_input["name"] = input("Recipient Name: ")
    email_input["email"] = input("Recipient Email: ")
    email_input["context"] = input("What would you like to type?\n")

formatted_prompt = prompt.format(
    email_recipient_name=email_input["name"],
    email_recipient_email=email_input["email"],
    email_body_context=email_input["context"],
    today=date.today().isoformat()
)

# FIXME: Some responses are including to ask the user his full name, but some are not.

analysis_response = structured_model.invoke(formatted_prompt) if not DUM_DATA else {
    "needs_more_info": True,
    "questions": [
        {
            "type": "date_range",
            "question": "Leave dates?"
        },
        {
            "type": "single_line",
            "question": "Reason for leave?"
        },
        {
            "type": "multi_choice",
            "question": "Email tone?",
            "options": [
                "Professional",
                "Friendly",
                "Formal",
                "Casual"
            ]
        },
        {
            "type": "multi_choice",
            "question": "Need attachment?",
            "options": [
                "Resume",
                "Portfolio",
                "Medical Certificate",
                "None"
            ]
        },
        {
            "type": "multi_select",
            "question": "Include?",
            "options": [
                "Signature",
                "Contact Number",
                "Address",
                "LinkedIn",
                "Portfolio"
            ]
        },
        {
            "type": "multi_select",
            "question": "Mention achievements?",
            "options": [
                "Research Paper",
                "Patent",
                "Hackathon Win",
                "Internship"
            ]
        }
    ]
}
    

if (not analysis_response["needs_more_info"]):
    pass

# FIXME: Use ChatPromptTemplate as we are now interacting with the AI
ques = analysis_response["questions"]

if (ques and len(ques) > 0):
    for i, q in enumerate(ques):
        updated_info.append((q["question"], input(q["question"] + ": ")))
        
        
print(updated_info)