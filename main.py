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
    "name": "Bruce Wayne",
    "email": "brucewayne@wayne.com",
    "context": "New car model details required that released recently. Provide me with options for more info"
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
        # Pydantic.model_dump() converts the Pydantic object to Dictionary
        # While dict() can help too, but, this method creates a deep copy.
        # dict() creates a shallow copy
        # Deep copy = nested objects are converted to dicts too
        # Shallow copy = only 1st depth attributes are converted to dict
        return RunnableLambda(lambda x: analysis_response.model_dump())
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
            You are an expert Information Analyzer.
            Determine if the user request has enough specific details to write a complete email.
            If details are missing, set needs_more_info to true and list short, precise questions.
            If details are complete, set needs_more_info to false.
        """,
    ),
    # Quick, lightweight example just for analysis logic
    (
        "human",
        "Recipient Name: Joyce Byers\nUser request: Tell me what new music albums you have."
    ),
    (
        "ai",
        '{{ "needs_more_info": true, "questions": [{{ "type": "single_line", "question": "Please share your name and email for the signature." }}] }}'
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
        
        CRITICAL PERSPECTIVE RULES:
        1. The 'User' is the SENDER (the person writing the email).
        2. The 'Recipient' is the RECEIVER (the person getting the email).
        3. ALWAYS write from the User's perspective addressed TO the Recipient. 
        4. NEVER write a customer service reply (e.g., Do NOT say "Thank you for your inquiry"). Write as the person asking/declaring the request.
        """
    ),
    # Just one clean example to show POV translation
    (
        "human",
        """
        Recipient name: Winnona Ryder
        Original request: Tell me what new music album gramophone discs do you have now in your shop.
        
        Messages History:
        Please share your name and email.
        Answer: Jhonny Depp, jhonnydepp@piratescarr.com
        """
    ),
    (
        "ai",
        """
        {{
            "subject": "Inquiry: Availability of New Music Album Gramophone Discs",
            "body": "Dear Winnona Ryder,\\n\\nI am writing to inquire about the new music album gramophone discs currently available in your shop. Could you please provide a list of the latest arrivals along with their prices?\\n\\nThank you for your assistance. I look forward to your reply.\\n\\nSincerely,\\nJhonny Depp\\njhonnydepp@piratescarr.com"
        }}
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

        # If a dict is returned, means we have to ask questions
        # else, a generator_chain was returned
        if isinstance(routing_chain_output, dict):
            print("\nMore information required.")
            print("Choose an option, enter custom answer, or press Enter to skip.")
            
            # We could've done this:
            # questions = routing_chain_output["questions"] or []
            # But, if in case the key isn't found, or not returned by AI,
            # The program will simply crash raising a KeyError
            # dict.get() returns the second parameter value if key doesn't exist
            # Safer.
            questions = routing_chain_output.get("questions", [])

            if questions:
                for q_num, q in enumerate(questions):
                    print(f"\nQ{q_num + 1}) {q.get('question')}")
                    ans = ""

                    if q.get('type') == "single_line":
                        ans = input("Ans: ")

                    elif q.get('type') == "date_range":
                        start = input("Start Date: ")
                        end = input("End Date: ")
                        if not start and not end: ans = "Not specified"
                        elif not start: ans = f"Ends on {end}"
                        elif not end: ans = f"Starts on {start}"
                        else: ans = f"from {start} to {end}"

                    elif q.get('type') == "multi_choice":
                        print_options(q.get('options', []))
                        choice = input("Option No. (or custom): ")
                        ans = parse_choice(choice, q.get('options', []))

                    elif q.get('type') == "multi_select":
                        print_options(q.get('options', []))
                        choice = input("Option Nos. (e.g. 1,3) or custom: ")
                        ans = parse_choice(choice, q.get('options', []))

                    if ans:
                        messages.append(("human", f"{q.get('question')}\nAnswer: {ans}"))
        else:
            final_results = routing_chain_output
                
            # Accessing it as the "." operator only, because:
            # 1. The analysis_chain returns a dict object,
            # 2. But we are using add_metadata, which returns a RunnableWithConfig,
            #    which behaves like a dict but also like an object,
            #    so it has both attributes and keys
            # 3. But it returns an Object, so the subject and body attributes are available
            # So, this is a bit of a mess, but it works.

            print("\n--- RESULTS ---")
            print("Subject:", final_results.subject)
            print("Body:\n", final_results.body)
            
            break

if __name__ == "__main__":
    main()