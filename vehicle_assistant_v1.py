import os
from dotenv import load_dotenv

load_dotenv()

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_google_genai import ChatGoogleGenerativeAI

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

#load vectorstore
db = FAISS.load_local(
    "vectorstore",
    embeddings,
    allow_dangerous_deserialization=True
)

query = input("Ask about your vehicle: ")

retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,
        "fetch_k": 20
    }
)

docs = retriever.invoke(query)
context = "\n\n".join(
    [doc.page_content for doc in docs]
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

print("\n\n===== RETRIEVED DOCUMENTS =====\n")

for i, doc in enumerate(docs):
    print(f"\n--- Document {i+1} ---\n")
    print(doc.page_content[:1000])

prompt = f"""
You are a vehicle safety assistant.

Use ONLY the vehicle manual context below.

Vehicle Manual Context:
{context}

User Question:
{query}

Provide:
1.Issue Summary
2.Severity (Low/Medium/High/Critical)
3.Recommended action
4.Safety Advice

If information is unavailable, clearly say so.

"""

response = llm.invoke(prompt)

print("\n")
print("="*50)
print("VEHICLE COPILOT RESPONSE")
print("="*50)
print(response.content)