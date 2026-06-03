# 启动mysql
    Start-Process -FilePath "E:\mysql\mysql-8.4.6-winx64\bin\mysqld.exe" -ArgumentList "--defaults-file=E:\mysql\my.ini" -WindowStyle Hidden

# 启动py
    python -m uvicorn llm.api.app:app --host 127.0.0.1 --port 8010 --reload                                                                                                   

# 关联我的git仓库
    git remote add origin https://github.com/chen25123/studyAgentDemo.git

# 安装openai
    pip install openai
    OpenAI 官方提供的 Python SDK，主要作用是：

    让你在 Python 代码中方便地调用 OpenAI 的 API（如 GPT-4、GPT-3.5、DALL-E、Whisper 等）
    封装了 HTTP 请求，不需要手动写 requests 代码。
    很多非 OpenAI 的服务（包括部分国内 AI 平台）也兼容 OpenAI 的接口格式，所以这个 SDK 也可以通过修改 base_url 来调用其他服务，

# 先建立一个简单的会话。

    会话中，我发现的问题是，如果我使用中转站的 apikey和url的话， 是会报错的， 换了模型官网的 api和url之后，就ok了。

# agent 比较重要的一个点，记忆。

    agent通过记忆变聪明，但是 记忆不可能无限增加， 考虑到token消耗，以及模型的上线文现在，都不允许我们的记忆无限叠加。
    所以，需要一个很重要的东西，记忆管理。

    ## 一个简单的记忆管理设计
    对话长度窗口：设置每次只取最近的20条对话内容作为记忆，超出窗口范围的则丢弃。

    进一步优化， 当超出窗口长度的时候，交给大模型总计一次，对历史对话进行一次压缩。
    以上，都只能解决短期记忆，或者聊天主题一致的情况。
    如果是随机聊天内容，摘要或者压缩，无法正确处理的时候，就需要一个 向量数据库来做一些长期处理了。


# 在python中定义 数据格式，并且可以检验格式
    使用 from pydantic import BaseModel

