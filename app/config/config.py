import os
HF_TOKEN = os.environ.get("HF_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

HUGGINGFACE_REPO_ID="google/gemma-1.1-7b-it"
DB_FAISS_PATH="vectorstore/db_faiss"
DATA_PATH = "./data"  # 相对于项目根目录的路径
CHUNK_SIZE=500
CHUNK_OVERLAP=50