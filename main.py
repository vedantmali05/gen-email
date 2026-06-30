import re
from datetime import date
from typing import Annotated, Literal

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

# --- CONFIG & ENVIRONMENT ---
load_dotenv()

# Toggle production mode
DEV_MODE = False

# --- ISOLATED DEV MOCK DATA (Remove in Production) ---
MOCK_INPUT = {
    "name": "Charles Xavier",
    "email": "principal@college.com",
    "context": "I want a 3 days leave from college as I have a Job Interview scheduled."
}

# --- SCHEMAS ---
class AnalysisQuestion(BaseModel):
    type: Literal["single_line", "multi_choice", "multi_select", "date_range"]
    question: str
    options: Annotated[list[str], Field(min_length=2, max_length=5)] | None = None

class AnalysisResponse(BaseModel):
    needs_more_info: bool
    questions: list[AnalysisQuestion] | None = None

class Email(BaseModel):
    subject: str
    body: str

# Mock generator for fast testing
def get_mock_analysis() -> AnalysisResponse:
    return AnalysisResponse(
        needs_more_info=True,
        questions=[
            AnalysisQuestion(type="date_range", question="Leave dates?"),
            AnalysisQuestion(type="single_line", question="Reason for leave?"),
            AnalysisQuestion(type="multi_choice", question="Email tone?", options=["Professional", "Friendly", "Formal", "Casual"]),
            AnalysisQuestion(type="multi_choice", question="Need attachment?", options=["Resume", "Portfolio", "Medical Certificate", "None"]),
            AnalysisQuestion(type="multi_select", question="Include?", options=["Signature", "Contact Number", "Address", "LinkedIn", "Portfolio"]),
            AnalysisQuestion(type="multi_select", question="Mention achievements?", options=["Research Paper", "Patent", "Hackathon Win", "Internship"])
        ]
    )

# --- HELPER FUNCTIONS ---
def print_options(options: list[str]) -> None:
    """Print numbered list of options."""
    for i, opt in enumerate(options, 1):
        print(f"{i}. {opt}")
        
def parse_choice(choice: str, options: list[str]) -> str:    
    """Convert numeric input string to text value if valid."""
    all_nums = re.findall(r'\d+', choice)
    clean_text = re.sub(r'[\d,]', '', choice)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    sel_options = ""
    
    for num in all_nums:
        idx = int(num) - 1
        if 0 <= idx <= len(options):
            sel_options += f" {options[idx]},"
    
    return f"{sel_options} and {clean_text}".strip()

# --- CORE LLM INITIALIZATION ---
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
analysis_llm = model.with_structured_output(AnalysisResponse)
email_llm = model.with_structured_output(Email)

# --- PROMPT TEMPLATES ---
# --- PROMPT TEMPLATES ---

# Checks if info enough. Asks short follow-up questions.
analysis_prompt = ChatPromptTemplate.from_messages([
    (
        "system", 
        """
            You are an expert Email Generator AI model.
            Determine whether the information given by the user is enough to generate a complete and accurate email.
            Don't assume missing facts or invent details.
            Ask only the minimum number of questions required before generating the email. Keep questions short.
            May need to ask user's preferences, required data, etc. to include in the email.
            No greetings. No filler. Example: "Dates of absentee?" not "Could you please provide leave dates".
            The user may skip any question or provide an answer outside the suggested options.
        """,
    ),
    (
        "human",
        """
            Recipient name: '{email_recipient_name}'
            Recipient email address: '{email_recipient_email}'
            User request: '{email_body_context}'
            Today's date: '{today}'
        """
    ),
    MessagesPlaceholder("messages")
])

# Writes final email. Uses only verified facts.
generator_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are an expert email writer.
        Generate a complete email.
        Do not invent facts.
        Use only the information provided.
        """
    ),
    (
        "human",
        """
        Recipient name: {email_recipient_name}
        Recipient email: {email_recipient_email}
        Original request:
        {email_body_context}
        """
    ),
    MessagesPlaceholder("messages")
])

# --- MAIN EXECUTION ---
def main():
    email_input = {}
    messages = []

    # 1. Gather Inputs
    if DEV_MODE:
        email_input = MOCK_INPUT.copy()
    else: 
        email_input["name"] = input("Recipient Name: ")
        email_input["email"] = input("Recipient Email: ")
        email_input["context"] = input("What would you like to type?\n")

    # 2. Map input values to prompt vars
    formatted_analysis_prompt = analysis_prompt.invoke({
        "email_recipient_name": email_input["name"],
        "email_recipient_email": email_input["email"],
        "email_body_context": email_input["context"],
        "today": date.today().isoformat(),
        "messages": messages
    })

    # 3. Call the AI
    if DEV_MODE:
        analysis_response = get_mock_analysis()
    else:
        analysis_response = analysis_llm.invoke(formatted_analysis_prompt)

    # 2. Process Questions loop
    if analysis_response.needs_more_info:
        print("\nMore information required.")
        print("Choose an option, enter custom answer, or press Enter to skip.")

    if analysis_response.questions:
        for q_num, q in enumerate(analysis_response.questions):
            print(f"\nQ{q_num + 1}) {q.question}")
            ans = ""

            if q.type == "single_line":
                ans = input("Ans: ")

            elif q.type == "date_range":
                start = input("Start Date: ")
                end = input("End Date: ")
                if not start and not end: ans = "Not specified"
                elif not start: ans = f"Ends on {end}"
                elif not end: ans = f"Starts on {start}"
                else: ans = f"from {start} to {end}"

            elif q.type == "multi_choice":
                print_options(q.options or [])
                choice = input("Option No. (or custom): ")
                ans = parse_choice(choice, q.options or [])

            elif q.type == "multi_select":
                print_options(q.options or [])
                choice = input("Option Nos. (e.g. 1,3) or custom: ")
                ans = parse_choice(choice, q.options or [])

            if ans:
                messages.append(("human", f"{q.question}\nAnswer: {ans}"))

    # 4. Generate Final Email
    final_prompt = generator_prompt.invoke({
        "email_recipient_name": email_input["name"],
        "email_recipient_email": email_input["email"],
        "email_body_context": email_input["context"],
        "messages": messages,
    })

    if DEV_MODE:
        final_results = Email(subject="Sample Subject", body="Sample Body")
    else:
        final_results = email_llm.invoke(final_prompt)

    print("\n--- RESULTS ---")
    print("Subject:", final_results.subject)
    print("Body:\n", final_results.body)

if __name__ == "__main__":
    main()