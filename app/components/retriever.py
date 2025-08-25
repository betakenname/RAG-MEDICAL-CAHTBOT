# 目标：将我们所有的“零件”（向量数据库、嵌入模型、大语言模型）组装成一条自动化的问答流水线。

# === 步骤1：导入所有需要的“工具” ===
# 从 langchain.chains 库中，导入 RetrievalQA 这个“总装配线”
# 从 langchain_core.prompts 库中，导入 PromptTemplate 这个“指令模板”工具
# 导入我们自己写的“LLM加载器” (load_llm) 和“向量数据库加载器” (load_vector_store)
# 导入日志、自定义错误和配置文件等
from langchain.chains import RetrievalQA,ConversationalRetrievalChain

from langchain_core.prompts import PromptTemplate
from app.components.llm import load_llm
from app.components.vetor_store import load_vector_store
from app.common.logger import get_logger
from app.common.custom_exception import CustomException
from app.config.config import HUGGINGFACE_REPO_ID,HF_TOKEN
logger = get_logger(__name__)
# === 步骤2：设计给AI的“考试指令” (Prompt Template) ===
# 定义一个多行字符串，作为我们的指令模板。
# 规定好AI的角色和限制，比如“只能用下面给的资料回答”。
# 使用两到三句回答，模板简洁有效
# 指令模板留下两个占位符：{context} 用来放从数据库里查到的资料，{question} 用来放用户的问题。
CUSTOM_PROMPT_TEMPLATE = """ 请仅使用上下文中提供的信息，用6行以内来回答以下医学问题，不要跟提问者说你用到了上下文，表现专业而精炼易懂。

上下文：
{context}

问题：
{question}

答案
"""
# === 步骤3：将指令模板包装成标准格式 ===
# 定义一个函数 set_custom_prompt()
def set_custom_prompt():
    # 在函数内部，使用 PromptTemplate 工具来包装我们上面定义的字符串模板。
    # 明确告诉 PromptTemplate，我们的模板里有两个变量需要后续填充，分别是 "context" 和 "question"。
    # 将创建好的模板对象返回。
    return PromptTemplate(
        template=CUSTOM_PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )

# === 步骤4：定义“总装配”函数 create_qa_chain() ===
#这个函数的目的和作用是把所有零件组装成一条完整的问答流水线。
def create_qa_chain():
    # === 步骤5：(健壮性) 用 try...except 把整个过程包起来 ===
    try:
        # === 步骤6：加载“向量图书馆” ===
        # 打印日志，告诉用户我们正在加载向量数据库
        logger.info("Loading vector store...")
        # 调用我们之前写的 load_vector_store() 函数，拿到数据库对象
        db = load_vector_store()

        # === 步骤7：检查数据库是否加载成功 ===
        # 如果返回的数据库对象是空的(None)...
        if db is None:
            # ...就抛出一个错误，因为没有知识库就无法问答
            raise CustomException("No vector store loaded, cannot create QA chain.")

        # === 步骤8：加载“答题专家” (LLM) ===
        # 调用我们自己写的 load_llm() 函数，拿到大语言模型对象
        # (这个函数你可能在其他文件里定义，作用是加载类似Qwen2.5这样的模型)
        # llm = load_llm(HF_TOKEN,HUGGINGFACE_REPO_ID)
        llm = load_llm()

        # === 步骤9：检查LLM是否加载成功 ===
        # 如果返回的LLM对象是空的(None)...
        if not llm:
            # ...就抛出一个错误
            raise CustomException("Failed to load LLM, cannot create QA chain.")

        # === 步骤10：开始组装“问答流水线” (RetrievalQA) ===
        # 调用 RetrievalQA.from_chain_type() 方法来创建问答链
        # qa_chain = RetrievalQA.from_chain_type(
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=db.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={'score_threshold': 0.5, 'k': 3}
            ),
            # 关键：使用 combine_docs_chain_kwargs 来传递自定义 Prompt
            combine_docs_chain_kwargs={'prompt': set_custom_prompt()},
            # 确保返回参考资料，方便我们调试
            return_source_documents=True
            # 注意：chain_type, chain_type_kwargs, verbose 参数在这里不再需要
        )

        # === 步骤11：打印成功日志 ===
        logger.info("QA chain created successfully.")

        # === 步骤12：返回组装好的问答链 ===
        return qa_chain

    # === 步骤13：如果 try 过程中出错了... ===
    except Exception as e:
        # ...包装并记录错误日志
        error_message = CustomException(f"Error creating QA chain: {str(e)}")
        logger.error(str(error_message))
        # ...明确地返回 None，表示创建失败
        return None