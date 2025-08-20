from langchain_community.vectorstores import FAISS
import os
from app.components.embeddings import get_embedding_model

from app.common.logger import get_logger
from app.common.custom_exception import CustomException

from app.config.config import DB_FAISS_PATH

logger = get_logger(__name__)


# 目标：如果本地已经存在一个建好的向量数据库，就把它加载进来。

# === 步骤1：导入所有需要的“工具” ===
# 从 langchain_community.vectorstores 库中，导入 FAISS 这个“向量数据库管理员”
# 导入 os 工具，用来检查文件路径
# 导入我们之前写好的 get_embedding_model 函数
# 导入日志、自定义错误和配置文件中的数据库路径(DB_FAISS_PATH)


# === 步骤2：定义“加载向量数据库”函数 load_vector_store() ===
def load_vector_store():
    # === 步骤3：(健壮性) 用 try...except 包起来 ===
    try:
        # === 步骤4：先准备好我们的“坐标转换机” ===
        # 调用 get_embedding_model() 函数，拿到嵌入模型。
        # 因为加载一个已有的数据库，也需要用当初创建它时相同的模型来理解它的坐标体系。
        embedding_model = get_embedding_model()

        # === 步骤5：检查数据库文件是否存在 ===
        # 使用 os.path.exists() 检查 DB_FAISS_PATH 这个路径是否存在。
        if os.path.exists(DB_FAISS_PATH):
            # === 步骤6：如果存在，就加载它 ===
            # 打印一条日志，告诉用户正在加载
            logger.info(f"Loading vector store from {DB_FAISS_PATH}...")
            # 使用 FAISS.load_local() 这个静态方法来加载
            # 参数1：数据库的本地路径
            # 参数2：当初创建它时用的嵌入模型
            # 参数3 (重要): allow_dangerous_deserialization=True  
            # (这是 FAISS 加载本地文件时的一个安全选项，必须设置为True才能加载成功)
            return FAISS.load_local(
                DB_FAISS_PATH,
                embedding_model,
                allow_dangerous_deserialization=True
            )
        # === 步骤7：如果不存在... ===
        else:
            # ...就打印一条警告日志，告诉用户没找到数据库
            logger.waring("No vectore store found..")
            
    # === 步骤8：如果 try 过程中出错了... ===
    except Exception as e:
        error_message = CustomException("Failed to load vectorstore" , e)
        logger.error(str(error_message))


# 目标：接收文本块，将它们转换成向量，并创建一个全新的向量数据库保存到本地。

# === 步骤1：定义“保存向量数据库”函数 save_vector_store() ===
# 这个函数需要接收一个参数，也就是之前切分好的 text_chunks 列表
def save_vector_store(text_chunks):
    # === 步骤2：(健壮性) 用 try...except 包起来 ===
    try:
        # === 步骤3：检查输入 ===
        # 如果传入的 text_chunks 列表是空的...
        if not text_chunks:
            raise CustomException("No chunks were found..")
        
        # === 步骤4：打印日志，告诉用户我们开始创建新的向量数据库了 ===
        logger.info("Creating new vector store...")

        # === 步骤5：准备“坐标转换机” ===
        # 同样，调用 get_embedding_model() 获取嵌入模型
        embedding_model = get_embedding_model()

        # === 步骤6：创建向量数据库的核心步骤 ===
        # 使用 FAISS.from_documents() 这个静态方法
        # 它会自动完成两件事：
        # 1. 用 embedding_model 遍历所有 text_chunks，把它们都转换成向量。
        # 2. 将这些向量和原始文本块一起，构建成一个 FAISS 索引数据库。
        # 把创建好的数据库对象存入 db 变量。
        db = FAISS.from_documents(
            text_chunks,
            embedding_model,
            # allow_dangerous_deserialization=True
        )

        # === 步骤7：保存数据库到本地 ===
        # 打印日志，告诉用户正在保存
        logger.info(f"Saving vector store to {DB_FAISS_PATH}...")
        # 调用数据库对象的 .save_local() 方法，并传入要保存的路径 (DB_FAISS_PATH)
        db.save_local(DB_FAISS_PATH)

        # === 步骤8：打印成功日志 ===
        logger.info(f"Vector store saved to {DB_FAISS_PATH} successfully.")

        # === 步骤9：将创建好的数据库对象返回，方便程序继续使用 ===
        return db

    # === 步骤10：如果 try 过程中出错了... ===
    except Exception as e:
        # ...包装并记录错误日志
        error_message = CustomException("Failed to save vectorstore", e)
        logger.error(str(error_message))