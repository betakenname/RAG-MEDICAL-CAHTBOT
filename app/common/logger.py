# app/common/logger.py

import logging
import sys
import os
from datetime import datetime

def get_logger(name: str = "RAG_MEDICAL_CHATBOT_LOGGER"):
    """
    配置并返回一个日志记录器。
    这个版本会同时将日志输出到控制台和按日期命名的日志文件中，
    并确保中文在两个地方都能正确显示。
    """
    # 获取 logger 实例
    logger = logging.getLogger(name)
    
    # --- 关键修改 ---
    # 检查 logger 是否已经有处理器，如果没有，才进行配置。
    # 这可以防止因重复调用而导致日志打印多次。
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # 创建一个统一的日志格式
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s"
        )

        # --- 处理器1: 输出到控制台 (解决乱码问题) ---
        console_handler = logging.StreamHandler(sys.stdout)
        # StreamHandler 默认会使用系统编码，我们在这里依赖 Python 3 的默认 UTF-8 处理能力
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # --- 处理器2: 输出到文件 (您的原有功能) ---
        # 创建 logs 目录 (如果不存在)
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)

        # 按日期创建日志文件
        log_file_path = os.path.join(logs_dir, f"log_{datetime.now().strftime('%Y-%m-%d')}.log")
        
        # 创建文件处理器，并明确指定使用 utf-8 编码
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

