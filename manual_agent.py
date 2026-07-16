import time
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

_embeddings = None
_db = None

def get_db():
    global _embeddings, _db
    if _db is None:
        print("Loading embedding model on CPU...")
        try:
            # Force cpu to avoid CUDA driver loader hangs
            _embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"}
            )
            print("Loading FAISS vector database...")
            _db = FAISS.load_local(
                "vectorstore",
                _embeddings,
                allow_dangerous_deserialization=True
            )
            print("Manual Agent Ready")
        except Exception as e:
            print("Error loading manual database:", e)
            _db = "FAILED"
    return _db



def retrieve_manual_info(query):

    print("\n========== Manual Agent ==========")
    print("Query:", query)

    start = time.time()

    db = get_db()
    if db == "FAILED" or db is None:
        print("Manual database is unavailable.")
        return "Unable to retrieve information from the vehicle manual."

    try:

        docs = db.similarity_search(query, k=5)

        print(f"Retrieved {len(docs)} relevant chunks.")

        context = "\n\n".join(
            doc.page_content for doc in docs
        )

        end = time.time()

        print(f"Manual Retrieval Time: {end-start:.2f} sec")
        print("==================================\n")

        return context

    except Exception as e:

        print("Manual Agent Error:", e)

        return "Unable to retrieve information from the vehicle manual."