import os
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

# =========================
# LOAD ENV VARIABLES
# =========================

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# =========================
# GET PROJECT ROOT PATH
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

data_path = os.path.join(BASE_DIR, "data")

output_file = os.path.join(
    BASE_DIR,
    "support_issues",
    "output.csv"
)

# =========================
# LOAD ALL CSV FILES
# =========================

all_dataframes = []

for folder in os.listdir(data_path):

    folder_path = os.path.join(data_path, folder)

    if os.path.isdir(folder_path):

        for file in os.listdir(folder_path):

            if file.endswith(".csv"):

                file_path = os.path.join(folder_path, file)

                try:

                    df = pd.read_csv(file_path)

                    # Basic cleaning
                    df.drop_duplicates(inplace=True)
                    df.fillna("Not Available", inplace=True)

                    all_dataframes.append(df)

                    print(f"Loaded: {file}")

                except Exception as e:
                    print(f"Error loading {file}: {e}")

# =========================
# CHECK IF DATA EXISTS
# =========================

if len(all_dataframes) == 0:
    print("No CSV files found in data folders.")
    exit()

# =========================
# COMBINE DATA
# =========================

combined_df = pd.concat(all_dataframes, ignore_index=True)

# =========================
# CREATE KNOWLEDGE BASE
# =========================

knowledge_base = combined_df.to_string()

print("\nDataset Analysis Completed.\n")

# =========================
# CREATE OUTPUT CSV
# =========================

if not os.path.exists(output_file):

    output_df = pd.DataFrame(columns=[
        "issue",
        "subject",
        "company",
        "response",
        "product_area",
        "status",
        "request_type",
        "justification"
    ])

    output_df.to_csv(output_file, index=False)

# =========================
# USER QUERY LOOP
# =========================

while True:

    user_query = input("Ask your issue (type exit to quit): ")

    if user_query.lower() == "exit":
        print("Exiting Support Agent...")
        break

    prompt = f"""
    You are a professional customer support assistant.

    Below is historical support issue data and resolutions.

    Support Data:
    {knowledge_base}

    User Question:
    {user_query}

    Instructions:
    - Reply like a real support assistant
    - Give direct helpful answers
    - Keep answers short and clear
    - Do not mention datasets
    - If answer is unavailable say:
      "I could not find relevant support information."

    Also classify the query into:
    - subject
    - company
    - product_area
    - status
    - request_type
    - justification

    Return response ONLY in this format:

    RESPONSE: <answer>

    SUBJECT: <subject>

    COMPANY: <company>

    PRODUCT_AREA: <product_area>

    STATUS: <status>

    REQUEST_TYPE: <request_type>

    JUSTIFICATION: <justification>
    """

    try:

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]

        )

        answer = response.choices[0].message.content

        print("\nAI Response:\n")
        print(answer)

        # =========================
        # PARSE RESPONSE
        # =========================

        lines = answer.split("\n")

        parsed_data = {
            "issue": user_query,
            "subject": "",
            "company": "",
            "response": "",
            "product_area": "",
            "status": "",
            "request_type": "",
            "justification": ""
        }

        for line in lines:

            if line.startswith("RESPONSE:"):
                parsed_data["response"] = line.replace("RESPONSE:", "").strip()

            elif line.startswith("SUBJECT:"):
                parsed_data["subject"] = line.replace("SUBJECT:", "").strip()

            elif line.startswith("COMPANY:"):
                parsed_data["company"] = line.replace("COMPANY:", "").strip()

            elif line.startswith("PRODUCT_AREA:"):
                parsed_data["product_area"] = line.replace("PRODUCT_AREA:", "").strip()

            elif line.startswith("STATUS:"):
                parsed_data["status"] = line.replace("STATUS:", "").strip()

            elif line.startswith("REQUEST_TYPE:"):
                parsed_data["request_type"] = line.replace("REQUEST_TYPE:", "").strip()

            elif line.startswith("JUSTIFICATION:"):
                parsed_data["justification"] = line.replace("JUSTIFICATION:", "").strip()

        # =========================
        # SAVE TO CSV
        # =========================

        new_row = pd.DataFrame([parsed_data])

        new_row.to_csv(
            output_file,
            mode="a",
            header=False,
            index=False
        )

        print("\nSaved to output.csv")

    except Exception as e:
        print(f"\nError: {e}")