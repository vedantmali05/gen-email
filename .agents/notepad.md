# Gen Email - Roadmap & Ideas - Just for my reference

**Problem**
- Generated email is inaccurate:
    - Says: "Sincerely, Charles" in signature but, Charles is the recipient name
    - Very short body is being received.
    - I have intentionally gave complex context to the model, having events, and queries in wrong logical order. The model shall suggest a right order before generating email, and wait for user to confirm it or suggest new order.
    ```shell
        (.venv) (base) ~/Projects/gen-email$ python main.py 
            Recipient Name: Alice Boyd
            Recipient Email: aliceboyd@summersea.com
            What would you like to type?
            I want to know the current prices of boats available at your store, along with their prices. I am Krissy Tideman, krissytideman@email.com, and I am loooking for renting the boats, not buying them. I will rent it for 7 days from 10th July. I am available to meet at 7 or 8th July. Please tell me the above things and also your availability.

            --- RESULTS ---
            Subject: Inquiry: Boat Rental Availability and Pricing - Krissy Tideman
            Body:
            Dear Alice Boyd,

            I hope this email finds you well. I am writing to inquire about the current prices and availability of boats for rent at your store.

            I am interested in renting a boat for 7 days, starting from July 10th. Could you please provide details on the types of boats available for rent during that period, along with their respective rental prices?

            Additionally, I would like to arrange a meeting to discuss this further. I am available to meet on either July 7th or July 8th. Please let me know your availability on those dates.

            Thank you for your time and assistance. I look forward to hearing from you soon.

            Sincerely,
            Krissy Tideman
            krissytideman@email.com
        (.venv) (base) ~/Projects/gen-email$
    ```
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

-   Email correction: Iterative email improvement with new information
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
-   Error handling and fallback mechanisms

# Sample Testing Inputs

- Formal, sincere - To a senior person like Sushant Bansal, DRDO Secretary
``` 
Write a very formal email having a proper flow of information. I am pleased that Sushant Bansal, secretary of DRDO and a very important person contacted me recently. I want to reply. Thank you for their contact about the new Job opportunity. I accept it. Please suggest a time to meet in office. I am free 6th July onwards anytime. My details: Jaskirat Singh Rangi, jaskiratrangi@email.com, from Pathankot, Punjab. Make sure to add these details in email signature. Also add, please let me know if you need any of my details.
```
- Formal, casual - To request boat rental details
```
Please tell me the new boats available at your store. I am Krissy Tideman, krissytideman@email.com, I will rent it for 7 days from 10th July. I am available to meet at 7 or 8th July. Please tell me the above things and also your availability.
```

- Formal, casual, without enough information - Requesting details for new car model
```
Please send me new car details that released recently. Provide the specs and prices.
```

- Informal, sincere - To invite for a birthday party to Aunt May
```
We are hosting a birthday party of Harry Osborn. You're invited.
```

- Informal, casual - Invitation to a friend for a party
```
You're invited for my birthday on 10th July.