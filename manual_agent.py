from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = FAISS.load_local(
    "vectorstore",
    embeddings,
    allow_dangerous_deserialization=True
)

def retrieve_manual_info(query):
    docs = db.similarity_search(query, k=3)
    
    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )
    
    return context