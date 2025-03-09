# Network_ntnu
不同的 AI 代理人各自負責不同的任務，並透過協作來提供最佳的客服回應

	0.客戶 (Customer)：提出問題，並將查詢存入 客戶查詢記錄 (customer_queries.csv)。
	1.客服接待代理 (FrontDesk Agent)：分類問題，決定應由哪個代理人處理：
	2.技術支援代理 (Tech Support Agent)：處理技術問題
	3.訂單處理代理 (Order Agent)：查詢/管理訂單
	4.一般客服問題 直接由 AI 產生回應 (AI Response)
	5.情緒分析代理 (Sentiment Agent)：分析客戶情緒，若發現情緒負面，則轉真人客服。
