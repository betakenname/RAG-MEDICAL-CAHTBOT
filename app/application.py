# app.py (最终修正版)

import os
import traceback  # <--- 导入 traceback 模块，用于详细的错误追踪
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for
from markupsafe import Markup

# 导入你自己的模块
from app.components.retriever import create_qa_chain
from app.common.logger import get_logger

# --- 准备工作 ---
# 删除了顶部的调试代码，因为我们已经确认环境变量加载成功
load_dotenv()
logger = get_logger(__name__)

# --- 初始化 Flask 应用 ---
app = Flask(__name__)
app.secret_key = os.urandom(24)


# --- 注册自定义过滤器 ---
def nl2br(value):
    return Markup(value.replace("\n", "<br>\n"))


app.jinja_env.filters['nl2br'] = nl2br

# --- 应用启动时预加载模型和问答链 ---
logger.info("Loading QA chain at application startup...")
qa_chain = create_qa_chain()
if qa_chain:
    logger.info("QA chain loaded successfully. Application is ready.")
else:
    logger.error("FATAL: Could not load QA chain. The application might not work correctly.")


@app.route("/", methods=["GET", "POST"])
def index():
    if "messages" not in session:
        session["messages"] = []

    if request.method == "POST":
        user_input = request.form.get("prompt")

        if user_input:
            messages = session["messages"]
            messages.append({"role": "user", "content": user_input})
            session["messages"] = messages  # 先保存用户输入，确保它能显示

            try:
                if qa_chain:
                    # 调用问答链
                    response = qa_chain.invoke({"query": user_input})

                    # ================ 核心修改：处理返回结果 ================
                    # 对于 RetrievalQA，结果通常在 'result' 键中。
                    # 我们增加一个检查，如果 'result' 不存在，就检查 response 本身是不是字符串。
                    if isinstance(response, dict):
                        result = response.get("result", "Sorry, the model returned an unexpected format.")
                    elif isinstance(response, str):
                        result = response
                    else:
                        result = "Sorry, the model's response could not be understood."
                    # =======================================================

                else:
                    result = "Error: The QA system is not available. Please check the server logs."

                messages.append({"role": "assistant", "content": result})
                session["messages"] = messages

            except Exception:  # <--- 核心修改：捕获任何异常
                # ================ 核心修改：记录详细的错误信息 ================
                # 使用 traceback.format_exc() 可以捕获完整的错误堆栈信息
                detailed_error = traceback.format_exc()
                error_msg = f"An unexpected error occurred. Please check the server logs."
                logger.error(f"--- DETAILED ERROR --- \n{detailed_error}\n--- END OF ERROR ---")
                # =======================================================

                messages.append({"role": "assistant", "content": error_msg})
                session["messages"] = messages

        return redirect(url_for("index"))

    return render_template("index.html", messages=session.get("messages", []))


@app.route("/clear")
def clear():
    session.pop("messages", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    # 开启 debug=True 可以在开发时看到更详细的网页报错
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)