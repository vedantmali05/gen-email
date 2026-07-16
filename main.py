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
    
class Flow(BaseModel):
    flow: list[str] = Field(
        description="Chronological steps/points representing a logical flow of the email based on the request."
    )

class Improvisations(BaseModel):
    original: str | None = None
    improved: str
    reason: str = Field(
        max_length=60, 
        description="Max 60 chars. Mechanical change only, e.g., 'Added polite adverb' or 'Changed date layout'."
    )

class Email(BaseModel):
    subject: str
    body: str
    improvisations: list[Improvisations] | None = None

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
# Feeds metadata to prompt automatically via a chain
def add_metadata(inputs: dict):
    inputs['today'] = date.today().isoformat()
    return inputs

# Print numbered list of options.
def print_options(options: list[str]) -> None:
    for i, opt in enumerate(options, 1):
        print(f"{i}. {opt}")
        
# Convert numeric input string to text value if valid.
def parse_choice(choice: str, options: list[str]) -> str:    
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

# If info is required, take inputs, if not required, move to generator chain
def route_by_status(inputs: dict):
    analysis_response = inputs["analysis"]
    
    if analysis_response.needs_more_info:
        # Pydantic.model_dump() converts the Pydantic object to Dictionary
        # While dict() can help too, but, this method creates a deep copy.
        # dict() creates a shallow copy
        # Deep copy = nested objects are converted to dicts too
        # Shallow copy = only 1st depth attributes are converted to dict
        return RunnableLambda(lambda x: analysis_response.model_dump())
    else:
        return full_generator_chain
    

# --- CORE LLM INITIALIZATION ---
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
analysis_llm = model.with_structured_output(AnalysisResponse)
flow_llm = model.with_structured_output(Flow)
generator_llm = model.with_structured_output(Email)

# --- PROMPT TEMPLATES ---
# Analysis Prompt
analysis_prompt = ChatPromptTemplate.from_messages([
    (
        "system", 
        """
            You are an expert Information Analyzer.
            Determine if the user request has enough specific details to write a complete email.
            If details are missing, set needs_more_info to true and list short, precise questions.
            If details are complete, set needs_more_info to false.
            DO NOT ask the user for stylistic preferences, tone options, or subject lines. You must figure those out yourself later.
        """,
    ),
    # Few shot prompting - Analysis Prompt
    (
        "human",
        """
            Recipient name: 'Joyce Byers'
            Recipient email address: 'joycebyers@hawkins.com'
            User request: 'Tell me what new music albums you have.'
            Today's date: '2026-07-16'
        """
    ),
    (
        "ai",
        '{{"needs_more_info": true, "questions": [{{"type": "single_line", "question": "Please share your name and email for the signature."}}]}}'
    ),
    # Human message
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

# Flow Prompt
flow_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
            You are an expert email architect.
            Analyse the recipient information, user request, and answers provided in the message history.
            Create concise bullet points representing the logical flow of events in the email.
            Do NOT write the email body yet. Just map the sequence of information.
        """
    ),
    # Few shot prompting - Flow Prompt
    (
    "human",
    """
    Recipient name: 'Joyce Byers'
    Recipient email address: 'joycebyers@hawkins.com'
    User request: 'Tell me what new music albums you have.'
    
    Messages History:
    Please share your name and email for the signature.
    Answer: Jim Hopper, jimhopper@hawkins.com
    """
    ),
    (
        "ai",
        '"flow": ["Formally greet Joyce Byers.", "Inquire about the availability of recent music album arrivals.", "Provide sender contact details (Jim Hopper) and request a catalog.", "Sign off professionally."]'
    ),
    # Human message
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

        CRITICAL STYLE & SENIOR RESPECT RULES:
        5. NO CONDESCENDING FLUFF: When addressing senior officials, executives, or elders, NEVER use phrases like "do not hesitate to let me know". It sounds presumptive or informal. Use direct, highly respectful requests like "Kindly let me know if you need any further details."
        6. KEEP SENDER'S VOICE: Do not overcomplicate simple expressions into robotic corporate filler. Keep polished text direct and clean.

        IMPROVISATION TRACKING:
        If you change, format, or improve any names, context details, or text provided by the user, you MUST log it in the 'improvisations' list. 
        CRITICAL: If the information was explicitly provided in the request text (like a name or city), do NOT set 'original' to null or None. Use the exact phrase the user typed as the 'original' value.
        The 'reason' field MUST be strictly short (under 60 characters) and mechanical.
        """
    ),
    # Few shot prompting - Generator Prompt
    (
        "human",
        """
        Recipient name: Winnona Ryder
        Original request: Tell me what new music album gramophone discs do you have now in your shop.

        Flow Blueprint:
        - Formally greet Winnona Ryder.
        - Inquire about new music album gramophone discs.
        - Provide sender contact details (Jim Hopper) and request a catalog.
        - Sign off professionally.
        
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
    # Few shot prompting - Generator Prompt
    (
        "human",
        """
        Recipient name: J. Jonah Jameson
        Original request: I am Peter Parker, peterparker@nyc.com, and I am seeking to meet you and show my photography skills at Daily Bugle Office. I am free anytime after 6th July (tomorrow), please reply me with a suitable time. This should be a formal and convincing email.
        """
    ),
    (
        "ai",
        """
        {{
            "subject": "Meeting Request - Peter Parker",
            "body": "Dear Mr. Jameson,\\n\\nI am writing to request a meeting with you at the Daily Bugle office to showcase my photography skills. I am available to meet anytime after July 6th. Kindly let me know what time works best for your schedule.\\n\\nThank you for your consideration.\\n\\nSincerely,\\nPeter Parker\\npeterparker@nyc.com",
            "improvisations": [
                {{
                    "original": "J. Jonah Jameson",
                    "improved": "Mr. Jameson",
                    "reason": "Added 'Mr.' and used surname for formal salutation."
                }},
                {{
                    "original": "6th July",
                    "improved": "July 6th",
                    "reason": "Reordered date layout to standard business format."
                }},
                {{
                    "original": "please reply me with a suitable time",
                    "improved": "Kindly let me know what time works best for your schedule.",
                    "reason": "Swapped command for polite adverb and formal request."
                }}
            ]
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
        
        Flow blueprint:
        {flow_list}
        """
    ),
    MessagesPlaceholder("messages")
])

# --- CHAINS ----
analysis_chain = add_metadata | analysis_prompt | analysis_llm
flow_chain = flow_prompt | flow_llm
generator_chain = generator_prompt | generator_llm

full_generator_chain = (
    RunnablePassthrough.assign(
        flow_list=flow_chain
        | RunnableLambda(lambda x: "\n ->".join(x.flow))
    ) 
    | generator_chain
)

routing_chain = (
    # Takes the incoming dictionary, processes it, and adds the output to a new key in that same dictionary.
    # <- dict(analysis), is forwared to the next node in the chain
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

            if final_results.improvisations:
                print("\n--- IMPROVISATIONS ---")
                for i, imp in enumerate(final_results.improvisations):
                    print(f"Revision {i + 1})")
                    print(f"Original: {imp.original}")
                    print(f"Improved: {imp.improved}")
                    print(f"Reason: {imp.reason}")
                    print()
            
            break

if __name__ == "__main__":
    main()