# app/components/llm.py

import os
from langchain_openai import ChatOpenAI
from app.common.logger import get_logger
from app.common.custom_exception import CustomException
from dotenv import load_dotenv # 引入 load_dotenv 以便直接测试

logger = get_logger(__name__)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)
logger.info(" 加载 .env 文件成功")
# 从环境变量中安全地获取 API Key 和 Base URL
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL") # 例如: "https://api.deepseek.com"
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "deepseek-chat") # 默认使用 deepseek-chat 模型

def load_llm():
    """
    通过连接到云端 LLM API 来初始化 LLM。
    """
    # 检查必要的环境变量是否已设置
    if not LLM_API_KEY or not LLM_BASE_URL:
        error_message = CustomException("LLM_API_KEY or LLM_BASE_URL environment variable not set.")
        logger.error(error_message)
        return None

    try:
        logger.info(f"Initializing LLM from API at {LLM_BASE_URL} with model {LLM_MODEL_NAME}...")

        llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            temperature=0.3,
            max_tokens=256,
        )

        logger.info("Cloud LLM initialized successfully.")
        return llm

    except Exception as e:
        error_message = CustomException(f"Error initializing Cloud LLM: {str(e)}")
        logger.error(error_message)
        return None
if __name__ == "__main__":
    # 直接运行此文件时，测试 LLM 初始化
    llm = load_llm()
    if llm:
        print("LLM loaded successfully.")
    else:
        print("Failed to load LLM.")