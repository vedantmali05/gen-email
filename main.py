import re
from datetime import date
from typing import Annotated, Literal

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
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
def get_mock_analysis():
    analysis_res = AnalysisResponse(
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
    return lambda x: {"status": "ask_questions", "data": analysis_res}

# --- HELPER FUNCTIONS ---
def add_metadata(inputs: dict):
    """Feeds metadata to prompt automatically via a chain"""
    inputs['today'] = date.today().isoformat()
    return inputs

def print_options(options: list[str]) -> None:
    """Print numbered list of options."""
    for i, opt in enumerate(options, 1):
        print(f"{i}. {opt}")
        
def parse_choice(choice: str, options: list[str]) -> str:    
    """Convert numeric input string to text value if valid."""
    all_nums = re.findall(r'\d+', choice)
    clean_text = re.sub(r'[\d,]', '', choice)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    sel_list = []
    for num in all_nums:
        idx = int(num) - 1
        if 0 <= idx < len(options):
            sel_list.append(options[idx])
    
    # 🔥 Refactored tracking to use a list and join cleanly with no trailing commas
    sel_options = ", ".join(sel_list)
    if clean_text:
        return f"{sel_options} and {clean_text}".strip() if sel_options else clean_text
    return sel_options

def route_by_status(inputs: dict):
    """If info is required, take inputs, if not required, move to generator chain"""
    analysis_response = inputs["analysis"]
    
    if analysis_response.needs_more_info:
        return RunnableLambda(lambda x: {"status": "ask_questions", "data": analysis_response})
    else:
        return generator_chain
    

# --- CORE LLM INITIALIZATION ---
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
analysis_llm = model.with_structured_output(AnalysisResponse)
generator_llm = model.with_structured_output(Email)

# --- PROMPT TEMPLATES ---
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

# --- CHAINS ----
analysis_chain = add_metadata | analysis_prompt | analysis_llm
generator_chain = generator_prompt | generator_llm
routing_chain = (
    RunnablePassthrough.assign(analysis=analysis_chain)
    | route_by_status
)

# --- MAIN EXECUTION ---
def main():
    email_input = {}
    messages = []

    if DEV_MODE:
        email_input = MOCK_INPUT.copy()
    else: 
        email_input["name"] = input("Recipient Name: ")
        email_input["email"] = input("Recipient Email: ")
        email_input["context"] = input("What would you like to type?\n")

    while True:
        if DEV_MODE:
            routing_chain_output = get_mock_analysis()(None)
        else:
            routing_chain_output = routing_chain.invoke({
                "email_recipient_name": email_input["name"],
                "email_recipient_email": email_input["email"],
                "email_body_context": email_input["context"],
                "messages": messages
            })

        if isinstance(routing_chain_output, dict) and routing_chain_output.get("status") == "ask_questions":
            analysis_response = routing_chain_output["data"]
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
        else:
            final_results = routing_chain_output
                
            print("\n--- RESULTS ---")
            print("Subject:", final_results.subject)
            print("Body:\n", final_results.body)
            
            break

if __name__ == "__main__":
    main()