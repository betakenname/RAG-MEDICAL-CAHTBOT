#pdf 读取器，读取pdf 功能并处理
import os
from langchain_community.document_loaders import DirectoryLoader,UnstructuredPDFLoader,PyPDFLoader,PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.common.logger import get_logger
from app.common.custom_exception import CustomException

from app.config.config import DATA_PATH,CHUNK_SIZE,CHUNK_OVERLAP

logger = get_logger(__name__)
# 目标：找到指定文件夹里的所有PDF文件，并读取它们的内容。

# === 步骤1：导入所有需要的“工具” ===
# OS工具，用来检查文件夹是否存在
# 从LangChain库里，导入“文件夹加载器”和“PDF加载器”
# 导入我们自己写的日志工具、自定义错误工具
# 导入配置文件里的数据路径(DATA_PATH)等变量

# === 步骤2：定义“图书管理员”函数 load_pdf_files() ===
def load_pdf_files():
    # === 步骤3：(健壮性) 用 try...except 把整个过程包起来，防止程序因意外错误而崩溃 ===
    try:
        # === 步骤4：检查存放PDF的书架（DATA_PATH）是否存在 ===
        # 如果路径不存在...
        if not os.path.exists(DATA_PATH):
            # === 步骤5：就抛出一个自定义的错误，告诉用户“数据路径不存在” ===
            raise CustomException

        # === 步骤6：如果路径存在，打印一条日志，告诉用户我们开始从哪里加载文件了 ===
        logger.info("Loding file from {DataPath}")

        # === 步骤7：配置“文件夹加载器” ===
        # 告诉它要去哪个文件夹(DATA_PATH)
        # 告诉它只找后缀是.pdf的文件(glob="*.pdf")
        # 告诉它找到PDF文件后，要用“PDF加载器”(loader_cls=PyPDFLoader)去处理
        
        loader = DirectoryLoader(
            DATA_PATH,
            glob="*.pdf",  # 告诉它只找后缀是.pdf的文件
            loader_cls=PyMuPDFLoader   # 告诉它找到PDF文件后，要用“PDF加载器”去处理
        )
        


        # === 步骤8：执行加载 ===
        # 调用加载器的.load()方法，正式开始工作，把加载好的所有文档内容存入 documents 变量
        documents = loader.load()
        if documents:
            print("--- PDF加载器提取的原始文本（前500字符） ---")
            print(documents[0].page_content[:1000])
            print(documents[0])
            print("------------------------------------------")
        # === 步骤9：检查加载结果，并打印日志 ===
        # 如果 documents 列表是空的 (说明没找到任何PDF)...
        
            # ...就打印一条警告日志
        if not documents:
            logger.warning("No documents found in the specified directory.")
        # 否则 (如果找到了文件)...
        else:
            # ...就打印一条成功日志，告诉用户找到了多少个文档
            logger.info(f"Loaded {len(documents)} documents from {DATA_PATH}")

        # === 步骤10：返回加载好的文档列表 ===
        return documents

        # === 步骤10：返回加载好的文档列表 ===
        

    # === 步骤11：如果 try 过程中的任何一步出错了... ===
    except Exception as e:
        # ...把原始错误(e)包装成我们自定义的错误信息
        error_message = CustomException(f"Error loading PDF files: {str(e)}")
        # ...用日志记录下这个错误
        logger.error(error_message)
        # ...返回一个空列表，让程序能继续往下走而不是崩溃
        return []

# 目标：把加载好的、大段的文档内容，切成小的、带有重叠部分的文本块。

# === 步骤1：导入所有需要的“工具” ===
# 从LangChain库里，导入“递归字符文本分割器”
# (其他如日志、配置等工具在上面已经导入过了)

# === 步骤2：定义“复印员”函数 create_text_chunks() ===
# 这个函数需要接收一个参数，也就是上面加载好的 documents 列表
def create_text_chunks(documents):
    # === 步骤3：(健壮性) 同样用 try...except 包起来 ===
    try:
        # === 步骤4：检查输入 ===
        # 如果传入的 documents 列表是空的...
        if not documents:
            # === 步骤5：就抛出一个错误，告诉用户“没有文档可以切分” ===
            raise CustomException("No documents to split into text chunks.")

        # === 步骤6：打印日志，告诉用户我们开始切分了 ===
        logger.info("Splitting documents into text chunks...")

        # === 步骤7：配置“文本分割器” ===
        # 使用 RecursiveCharacterTextSplitter
        # 告诉它每张“卡片”的大小 (chunk_size=CHUNK_SIZE)
        # 告诉它每两张“卡片”之间内容的重叠大小 (chunk_overlap=CHUNK_OVERLAP)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        # === 步骤8：执行切分 ===
        # 调用分割器的 .split_documents() 方法，对文档列表进行切分，结果存入 text_chunks 变量
        text_chunks = text_splitter.split_documents(documents)

        # === 步骤9：打印日志，告诉用户成功生成了多少个文本块 ===
        logger.info(f"Created {len(text_chunks)} text chunks.")

        # === 步骤10：返回切分好的文本块列表 ===
        return text_chunks

    # === 步骤11：如果 try 过程中出错了... ===
    except Exception as e:
        # ...包装错误信息
        error_message = CustomException(f"Error creating text chunks: {str(e)}")
        # ...记录错误日志
        logger.error(error_message)
        # ...返回一个空列表
        return []