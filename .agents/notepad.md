# Gen Email - Roadmap & Ideas - Just for my reference

**Problem**
- Generated email is inaccurate:
    - Says: "Sincerely, Charles" in signature but, Charles is the recipient name
    - Very short body is being received.
    - Email treated as the recipient's POV, not users.
        ```shell
        (.venv) (base) ~/Projects/gen-email$ python3 main.py 
            Recipient Name: Bruce Wayne
            Recipient Email: bruce@wayneenter.com
            What would you like to type?
            New car model details required that released recently. Provide me with options for more info

            More information required.
            Choose an option, enter custom answer, or press Enter to skip.

            Q1) What type of car models are you interested in?
            1. EV
            2. SUV
            3. Sedan
            4. Sports Car
            5. Luxury Car
            Option Nos. (e.g. 1,3) or custom: 1, 2 and also the Luxury Car, and in red color

            Q2) What specific details are you looking for?
            1. Specifications
            2. Pricing
            3. Features
            4. Availability
            5. Reviews
            Option Nos. (e.g. 1,3) or custom: 1, 2, 5 and any discount?

            --- RESULTS ---
            Subject: Regarding Your Inquiry: New Car Model Details (EV, SUV, Luxury - Red)
            Body:
             Dear Bruce Wayne,

            Thank you for your inquiry about recently released new car models.

            You are interested in Electric Vehicles (EVs), SUVs, and Luxury Cars, specifically in red.

            To assist you further, you are looking for the following details:
            - Specifications
            - Pricing
            - Reviews
            - Any available discounts

            We will gather this information and provide you with options for more details shortly.

            Sincerely,
        (.venv) (base) ~/Projects/gen-email$ 
        ```
---

**Problem**
- Every emails requires some user data. Example: User's full name, contact, email, etc.

**Solution**
- A key-value repository could be provided for data in email, or Global Data
- Reference: Postman's Variables View
- For Global Variables, a separate page can be provided, no need to type of every project. Custom selection can be provided to select only relevant global variables.

---
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
