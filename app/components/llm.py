# app/components/llm.py

from langchain_community.llms import Ollama
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)


def load_llm():
    """
    通过连接到本地运行的 Ollama 实例来初始化 LLM。
    """
    try:
        # 确保这里的模型名 "qwen3:8b" 和你 `ollama list` 中的名字完全一致
        logger.info("Initializing local LLM with Ollama (Model: qwen3:8b)...")

        llm = Ollama(model="qwen3:8b")  # <--- 确认模型名称为这个

        logger.info("Ollama LLM initialized successfully.")
        return llm

    except Exception as e:
        error_message = CustomException(f"Error initializing Ollama LLM: {str(e)}")
        logger.error(error_message)
        return None