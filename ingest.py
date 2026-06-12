# THIS SCRIPT 
# 1.READS THE PDF
# 2.SPLITS IT INTO CHUNKS
# 3.CREATES EMBEDDINGS
# 4.STORES EMBEDDINGS IN FAISS

from dotenv import load_dotenv
load_dotenv()

import os

print(os.getenv("GEMINI_API_KEY"))

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import FAISS

from langchain_community.embeddings import HuggingFaceEmbeddings

#load pdf
loader = PyPDFLoader("Vehicle-copilot/data/toyota_manual.pdf")
documents = loader.load()
print("Pages Loaded:", len(documents))

#split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

docs = splitter.split_documents(documents)
print("Chunks Created:", len(docs))

#Embedding model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

#create faiss
vectorstore = FAISS.from_documents(
    docs,
    embeddings
)

#save locally
vectorstore.save_local("vectorstore")
print("Vector store saved")