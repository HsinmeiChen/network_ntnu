import os
import asyncio
import pandas as pd
from dotenv import load_dotenv
import io

# AutoGen 相關匯入
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

load_dotenv()

async def process_chunk(chunk, start_idx, total_records, model_client, termination_condition):
    """
    處理客服查詢的批次：
      - 讀取客戶問題
      - 讓客服接待代理人分類問題
      - 轉給適當的代理人（技術支援、訂單管理等）
      - 若客戶情緒負面，轉真人客服
    """
    chunk_data = chunk.to_dict(orient='records')
    
    prompt = (
        f"正在處理第 {start_idx} 至 {start_idx + len(chunk) - 1} 筆客服問題（共 {total_records} 筆）。\n"
        f"以下為該批次的客戶查詢:\n{chunk_data}\n\n"
        "請各代理人依照以下步驟回應客戶：\n"
        "  1. 客服接待代理判斷問題類型（訂單、技術支援、一般詢問）\n"
        "  2. 若為技術問題，由技術支援代理回答\n"
        "  3. 若為訂單問題，由訂單處理代理回答\n"
        "  4. 情緒分析代理檢查客戶情緒，若情緒負面則轉真人客服\n"
        "請團隊協作提供完整的客服回應。"
    )
    
    # 建立智慧客服代理人
    local_front_desk_agent = AssistantAgent("front_desk", model_client)
    local_tech_support_agent = AssistantAgent("tech_support", model_client)
    local_order_agent = AssistantAgent("order_agent", model_client)
    local_sentiment_agent = AssistantAgent("sentiment_analyzer", model_client)
    local_user_proxy = UserProxyAgent("customer_proxy")
    
    # 設定客服團隊
    local_team = RoundRobinGroupChat(
        [local_front_desk_agent, local_tech_support_agent, local_order_agent, local_sentiment_agent, local_user_proxy],
        termination_condition=termination_condition
    )
    
    messages = []
    async for event in local_team.run_stream(task=prompt):
        if isinstance(event, TextMessage):
            print(f"[{event.source}] => {event.content}\n")
            messages.append({
                "batch_start": start_idx,
                "batch_end": start_idx + len(chunk) - 1,
                "source": event.source,
                "content": event.content,
                "type": event.type,
                "prompt_tokens": event.models_usage.prompt_tokens if event.models_usage else None,
                "completion_tokens": event.models_usage.completion_tokens if event.models_usage else None
            })
    return messages

async def main():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("請檢查 .env 檔案中的 GEMINI_API_KEY。")
        return

    # 初始化模型客戶端
    model_client = OpenAIChatCompletionClient(
        model="gemini-2.0-flash",
        api_key=gemini_api_key,
    )
    
    termination_condition = TextMentionTermination("exit")
    
    # 讀取客服記錄（每次讀取 1000 筆以提高效能）
    csv_file_path = "customer_queries.csv"
    chunk_size = 1000
    chunks = list(pd.read_csv(csv_file_path, chunksize=chunk_size))
    total_records = sum(chunk.shape[0] for chunk in chunks)
    
    # 以 asyncio.gather 並行處理客服問題
    tasks = list(map(
        lambda idx_chunk: process_chunk(
            idx_chunk[1],
            idx_chunk[0] * chunk_size,
            total_records,
            model_client,
            termination_condition
        ),
        enumerate(chunks)
    ))
    
    results = await asyncio.gather(*tasks)
    
    # 轉存客服對話紀錄
    all_messages = [msg for batch in results for msg in batch]
    df_log = pd.DataFrame(all_messages)
    output_file = "customer_service_log.csv"
    df_log.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"已將所有對話紀錄輸出為 {output_file}")

if __name__ == '__main__':
    asyncio.run(main())
