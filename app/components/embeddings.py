# app/components/embeddings.py

from langchain_huggingface import HuggingFaceEmbeddings
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

def get_embedding_model():
    """
    Initializes and loads a Hugging Face embedding model from a LOCAL directory.
    The library will automatically detect and use the best available device (CPU if no GPU is found).
    """
    try:
        # --- 核心修改在这里 ---
        # 我们将 model_name 从一个网络地址 
        # 修改为了一个本地文件夹的路径。
        # "./all-MiniLM-L6-v2" 表示在当前项目根目录下寻找这个文件夹。
        # local_model_path = "./all-MiniLM-L6-v2"
        local_model_path = "./Qwen3-Embedding-0.6B"
        logger.info(f"Initializing Hugging Face embedding model from local path: {local_model_path}...")

        # 使用修改后的本地路径来加载模型
        model = HuggingFaceEmbeddings(
            model_name=local_model_path
        )
        # 移除了 model_kwargs，让库自动检测CPU/GPU，这样更稳定。

        logger.info("Hugging Face embedding model initialized successfully from local path.")
        return model

    except Exception as e:
        # 添加了更具体的错误提示，如果文件夹不存在会更容易排查
        logger.error(f"Failed to load model from local path '{local_model_path}'. "
                     f"Please ensure the '{local_model_path}' folder exists in your project's root directory.")
        error_message = CustomException(f"Error initializing Hugging Face embedding model: {str(e)}")
        logger.error(error_message)
        raise error_message