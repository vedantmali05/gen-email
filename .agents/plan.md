# Gen Email - Roadmap & Ideas

**Problem**
- Generated email has lines which were never given in the input.

**Solution**
- Input basic details like rescipient name & email, and context
- System shall reason the context and ask follow up questions (multiple choice, multiple select, extra general input, etc. - like Claude)
- This will help AI to stay on the point, having proper information, and no extras.

---

**Problem**
- Every emails requires some user data. Example: User's full name, contact, email, etc.

**Solution**
- A key-value repository could be provided for data in email, or Global Data
- Reference: Postman's Variables View
- For Global Variables, a separate page can be provided, no need to type of every project. Custom selection can be provided to select only relevant global variables.

---
**Prompt Rules**

- Never invent facts.
- Never assume actions.
- Ask for missing information.
- Use only supplied data.

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
