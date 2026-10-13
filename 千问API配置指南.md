# 下一步：开通千问 API（零基础）

你现在不需要自己写程序。财报下载、全文提取和关键词索引已经准备好；接下来给程序一个调用千问的权限。

1. 打开[阿里云百炼控制台](https://bailian.console.aliyun.com/)，注册或登录自己的阿里云账号。
2. 如果页面提示开通百炼模型服务，阅读页面的服务条款和计费说明，自行完成开通。建议使用华北2（北京）地域。
3. 在控制台找到「API Key／密钥管理」，创建用于这份作业的 API Key。API Key 不是阿里云 AccessKey，也不是千问聊天网页的登录密码。
4. 同时找到当前业务空间 ID 和对应的 OpenAI 兼容 Base URL。地域、业务空间、密钥应一致。以控制台显示的接入地址为准；新版北京地址形如 `https://你的业务空间ID.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`。
5. 打开本项目的 `.env` 文件，填在等号后面：

```dotenv
DASHSCOPE_API_KEY=在本机填入你的密钥
MODEL_BASE_URL=从控制台复制的完整BaseURL
EMBEDDING_MODEL=text-embedding-v4
CHAT_MODEL=qwen-plus
```

不要把密钥发到聊天里，也不要把 `.env` 提交到仓库；本项目已加入忽略规则。密钥填好后，只需要告诉我“已在本机填好”。

两个模型做不同的工作：
- `text-embedding-v4`：把财报片段和问题变成向量。
- `qwen-plus`：阅读检索出的财报片段，组织带引用的答案。

同一份密钥通常可用于这两个模型，但要以你账号的模型权限为准。无需购买服务器，也不用先建百炼托管知识库。

调用按实际用量计费，免费额度和余额以你的控制台为准。本项目分批建立索引，并缓存已完成批次，避免重复计算。

配置后执行：

```sh
python src/build.py --vectors
python src/evaluate.py --answers
python src/server.py
```

建好索引后重启页面服务；自动回答后仍需人工核对10道题，不能把检索成功率当成答案正确率。

官方文档（核对日期：2026-09-28）：
- [首次调用千问 API](https://help.aliyun.com/zh/model-studio/first-api-call-to-qwen)
- [获取与配置 API Key](https://help.aliyun.com/zh/model-studio/get-api-key)
- [向量接口](https://help.aliyun.com/zh/model-studio/embedding-interfaces-compatible-with-openai)
