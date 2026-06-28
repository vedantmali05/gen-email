# Gen Email - Roadmap & Ideas

## Goal

Learn GenAI by building an AI Email Assistant.

## Phase 1

-   Generate email
-   Streamlit UI
-   Gemini + LangChain

## Current Problems

-   Too many hardcoded inputs.
-   LLM hallucinates missing details.

## Better Flow

User gives intent.

Agent asks follow-up questions until enough information is collected.

Then generates email.

## Your Data

Key-Value editor.

Examples: - Full Name - Roll Number - Course - Company - Phone -
LinkedIn

User selects variables to inject into prompt.

## Global Variables

Separate page.

Reusable profile information.

No need to type every email.

## Hallucination Control

Prompt rules: - Never invent facts. - Never assume actions. - Ask for
missing information. - Use only supplied data.

## Future Scope

-   Reply generation
-   Follow-up generation
-   Email history
-   Drafts
-   PDF upload
-   RAG
-   Attachments
-   Email sending
-   Memory
-   AI Agent
-   Templates
-   Multi-language
