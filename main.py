# Env
from dotenv import load_dotenv
load_dotenv()

# Model
from langchain_google_genai import ChatGoogleGenerativeAI
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# Prompting
from datetime import date
from langchain_core.prompts import PromptTemplate

# Structured Output
from typing import Annotated, Literal
from pydantic import BaseModel, Field

# DEV_MODE flag & other variables
DEV_MODE = False

email_input = {}
analysis_response = {}
updated_info = []
final_results = {}


# Setting analysis: Prompt Template, Structured Output
analysis_prompt = PromptTemplate.from_template(
    """
    The user wants to generate an email for the recipient '{email_recipient_name}' with an email address '{email_recipient_email}'.
    Current context: '{email_body_context}'
    Analyse whether the given information is enough to generate a complete and accurate email. Do not assume missing facts or invent details.
    If the information is missing, ask only the most important and relevant follow-up questions. Prefer quick questions:
        - Short-text (one line)
        - Multiple Choice Questions
        - Multiple Select Questions
    Ask only the minimum number of questions required before generating the email. Keep questions short.
    No greetings. No filler. Example: "Dates of absentee?" not "Could you please provide leave dates".
    The user may skip any question or provide an answer outside the suggested options.
    Today's date: '{today}'
    """
)

class AnalysisQuestion(BaseModel):
    type: Literal["single_line", "multi_choice", "multi_select", "date_range"]
    question: str
    options: Annotated[
        list[str],
        Field(min_length=2, max_length=5)
    ] | None = None

class AnalysisResponse(BaseModel):
    needs_more_info: bool
    questions: list[AnalysisQuestion] | None = None


analysis_model = model.with_structured_output(AnalysisResponse)

if DEV_MODE:
    email_input["name"] = "Charles Xavier"
    email_input["email"] = "principal@college.com"
    email_input["context"] = "I want a 3 days leave from college as I have a Job Interview scheduled."
else: 
    email_input["name"] = input("Recipient Name: ")
    email_input["email"] = input("Recipient Email: ")
    email_input["context"] = input("What would you like to type?\n")

formatted_prompt = analysis_prompt.format(
    email_recipient_name=email_input["name"],
    email_recipient_email=email_input["email"],
    email_body_context=email_input["context"],
    today=date.today().isoformat()
)

# FIXME: Some responses are including to ask the user his full name, but some are not.

analysis_response = analysis_model.invoke(formatted_prompt) if not DEV_MODE else {
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

print("More information required. Please input below: ")
print("You may choose from given options, enter custom answer or skip to answer.")

# FIXME: Use ChatPromptTemplate as we are now interacting with the AI
ques = analysis_response.questions

# Func to print options
def print_options(options):
    for i, opt in enumerate(options, 1):
        print(f"{i}. {opt}")
        
# Func to save cleaned option
def return_valid_choice(choice, options):    
    choice = choice.strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(options):
            return options[idx]
        else:
            return choice
    else: 
        return choice

if ques:
    for q_num, q in enumerate(ques):

        print(f"\nQ{q_num + 1}) {q.question}")
        ans = ""

        # Single line
        if q.type == "single_line":
            ans = input("Ans: ")

        # Date range
        elif q.type == "date_range":
            start = input("Start Date: ")
            end = input("End Date: ")
            
            if not start and not end:
                ans = "Not specified"
            elif not start:
                ans = f"Ends on {end}"
            elif not end:
                ans = f"Starts on {start}"
            else: 
                ans = f"from {start} to {end}"

        # Single choice
        elif q.type == "multi_choice":
            print_options(q.options)
            choice = input("Option No. (or custom): ")
            ans = return_valid_choice(choice, q.options)

        # Multi select
        elif q.type == "multi_select":
            print_options(q.options)
            choice = input("Option Nos. (e.g. 1,3) or custom: ")
            ans = []
            for num in choice.split(","):
                ans.append(return_valid_choice(num, q.options))

        updated_info.append({
            "que": q.question,
            "ans": ans
        })
        

# Merging original prompt + updated info
def merge_context(email_input, updated_info):
    merged = ""
    for key, value in email_input.items():
        merged += f"{key}: {value}\n"
        
    merged+="\n"
    
    for item in updated_info:
        ans = item["ans"]
        if (type(ans) == list):
            ans = ", ".join(ans)
            
        merged += f"{item['que']}: {ans or 'NA'}\n"
    
    return merged

# Building a prompt with final context, to generate final results
generator_prompt = PromptTemplate.from_template(
    """
    The user wants to generate an email with following details:
    {email_context}
    Rules:
        - Don't invent details
        - Don't include missing facts
        - Only stay limited to the given information
    """
)

formatted_prompt = generator_prompt.format(email_context=merge_context(email_input, updated_info))

class Email(BaseModel):
    subject: str
    body: str
    
analysis_model = model.with_structured_output(Email)

final_results = analysis_model.invoke(formatted_prompt)

print("Subject: ", final_results.subject)
print("Body: ", final_results.body)