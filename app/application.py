# app.py (或者 application.py)
from dotenv import load_dotenv
from datetime import datetime
import os
import re  # <-- 【修改1】确保导入 re 模块
from flask import Flask, render_template, request, session, redirect, url_for
from markupsafe import Markup
from flask_cors import CORS

# 从 langchain_core.messages 导入 HumanMessage 和 AIMessage
from langchain_core.messages import HumanMessage, AIMessage

# 导入你自己的模块
from app.components.retriever import create_qa_chain
from app.common.logger import get_logger

# --- 准备工作 ---
load_dotenv()
logger = get_logger(__name__)

# --- 初始化 Flask 应用 ---
app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# --- 【修改2】定义并注册 nl2br 自定义过滤器 ---
def nl2br_filter(value):
    """一个 Jinja2 过滤器，将换行符 (\n) 转换为 HTML 的 <br> 标签。"""
    if not isinstance(value, str):
        value = str(value)
    # 使用 re.sub 替换所有换行符，并用 Markup 包装以防止 HTML 被转义
    return Markup(re.sub(r'\n', '<br>\n', value))

# 将我们定义的函数注册到 Jinja2 的过滤器列表中，并命名为 'nl2br'
app.jinja_env.filters['nl2br'] = nl2br_filter

# --- 修改结束 ---

# --- 在应用启动时，预先创建好带记忆的问答链 ---
logger.info("Loading Conversational QA chain at application startup...")
qa_chain = create_qa_chain()
if qa_chain:
    logger.info("QA chain loaded successfully. Application is ready.")
else:
    logger.error("FATAL: Could not load QA chain. The application might not work correctly.")

# --- API 路由 (这部分代码保持不变) ---
@app.route("/", methods=["GET", "POST"])
def index():
    if "messages" not in session:
        session["messages"] = []

    if request.method == "POST":
        user_input = request.form.get("prompt")

        if user_input:
            chat_history_from_session = session.get("messages", [])
            formatted_chat_history = []
            for msg in chat_history_from_session:
                if msg["role"] == "user":
                    formatted_chat_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    formatted_chat_history.append(AIMessage(content=msg["content"]))

            messages = session["messages"]
            messages.append({"role": "user", "content": user_input})
            
            try:
                if qa_chain:
                    logger.info("Invoking conversational chain with history...")
                    response = qa_chain.invoke({
                        "question": user_input,
                        "chat_history": formatted_chat_history
                    })
                    result = response.get("answer", "抱歉，处理时遇到错误。")
                else:
                    result = "错误: 问答系统未初始化。"

                messages.append({"role": "assistant", "content": result})
                session["messages"] = messages
            
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                logger.error(error_msg)
                messages.append({"role": "assistant", "content": error_msg})
                session["messages"] = messages

            return redirect(url_for("index"))
    return render_template("index.html", messages=session.get("messages", []))


@app.route("/clear")
def clear():
    session.pop("messages", None)
    return redirect(url_for("index"))


@app.route("/health")
def health_check():
    """健康检查端点 - 增强版本"""
    import os
    # 定义在容器内的绝对路径
    APP_ROOT = '/app'
    MODEL_PATH = os.path.join(APP_ROOT, 'Qwen3-Embedding-0.6B')
    VECTORSTORE_PATH = os.path.join(APP_ROOT, 'vectorstore', 'db_faiss')

    try:
        # 使用绝对路径进行检查，确保万无一失
        model_exists = os.path.exists(MODEL_PATH)
        vectorstore_exists = os.path.exists(VECTORSTORE_PATH)
        qa_chain_ready = qa_chain is not None
        
        # 更详细的日志记录
        logger.info(f"Health check - Model exists: {model_exists}")
        logger.info(f"Health check - Vectorstore exists: {vectorstore_exists}")  
        logger.info(f"Health check - QA chain ready: {qa_chain_ready}")
        
        status = {
            'status': 'healthy' if all([model_exists, vectorstore_exists, qa_chain_ready]) else 'unhealthy',
            'model_loaded': model_exists,
            'vectorstore_loaded': vectorstore_exists,
            'qa_chain_ready': qa_chain_ready,
            'timestamp': datetime.now().isoformat(),
            'model_path': MODEL_PATH,
            'vectorstore_path': VECTORSTORE_PATH
        }
        
        return status, 200 if status['status'] == 'healthy' else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {'status': 'error', 'error': str(e)}, 503

if __name__ == "__main__":
    # 【关键修复】根据环境变量决定是否启用 debug 模式
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']
    logger.info(f"Starting Flask app with debug mode: {debug_mode}")
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)