#retrievs manual information
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

#load vector store
db = FAISS.load_local(
    "vectorstore",
    embeddings,
    allow_dangerous_deserialization=True
)

query = "engine overheating"


retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={"k":5}
)

docs = retriever.invoke(query)

for i, doc in enumerate(docs):
    print(f"\nDocument {i+1}")
    print("-" * 50)
    print(doc.page_content[:1000])