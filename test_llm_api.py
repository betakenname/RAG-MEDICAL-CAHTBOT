# test_llm_api.py

import os
from dotenv import load_dotenv
# 确保您的 llm.py 文件已经更新为调用 API 的版本
from app.components.llm import load_llm 
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
print(f"正在从路径: {dotenv_path} 加载 .env 文件...")
load_dotenv(dotenv_path=dotenv_path)
def main():
    """
    一个简单的脚本，用于在本地测试 LLM API 的连接，并带有调试信息。
    """
    # 1. 从 .env 文件加载环境变量
    print("--- 步骤 1: 加载环境变量 ---")
    load_successful = load_dotenv()
    
    if load_successful:
        print("✅ .env 文件已找到并加载。")
    else:
        print("⚠️ 未找到 .env 文件。请确保它与 test_llm_api.py 在同一个目录下。")

    # 打印加载到的环境变量，用于调试
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    
    print(f"读取到的 LLM_API_KEY: {'********' if api_key else '未设置'}")
    print(f"读取到的 LLM_BASE_URL: {base_url if base_url else '未设置'}")
    print("--------------------------\n")

    # 2. 尝试加载 LLM
    print("--- 步骤 2: 初始化 LLM ---")
    llm = load_llm()
    print("--------------------------\n")

    # 3. 检查并测试
    print("--- 步骤 3: 发送测试请求 ---")
    if llm:
        print("✅ LLM 加载成功！")
        print("正在发送一个测试请求...")
        try:
            # 发送一个简单的测试查询
            response = llm.invoke("你好，请用中文写一句问候。")
            
            print("\n--- DeepSeek API 响应 ---")
            print(response.content)
            print("------------------------")
            print("\n🎉 测试成功！API 连接和密钥均有效。")

        except Exception as e:
            print(f"\n❌ 在调用 LLM 时发生错误: {e}")
            print("请检查您的网络连接或 API Key 权限。")
    else:
        print("❌ LLM 加载失败。")
        print("请再次检查环境变量是否已正确加载。")
    print("--------------------------")


if __name__ == "__main__":
    main()

