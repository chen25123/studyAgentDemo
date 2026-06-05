# 启动mysql
    Start-Process -FilePath "E:\mysql\mysql-8.4.6-winx64\bin\mysqld.exe" -ArgumentList "--defaults-file=E:\mysql\my.ini" -WindowStyle Hidden

# 启动py
    python -m uvicorn llm.api.app:app --host 127.0.0.1 --port 8010 --reload

# git链接不上的时候怎么办？
    git config --global http.proxy http://127.0.0.1:7890
    git config --global https.proxy http://127.0.0.1:7890                

    找到科学上网工具，查看当前端口之后，然后将以上两个端口改成对应的端口。
    执行以上两个命令。为git配置代理。
    之后就可以了                                                                               

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

# 工具设计
    工具应该是处理某一类的场景问题，而不是处理单一问题。

    上个月有多少新建bug。为了实现这个功能，我写了一个工具， 输入是时间范围，通过 时间范围 和 状态类型，统计bug数量。
    这样做流程完全可以跑通，结果也没有问题。
    但是，如果我问 在上个月关闭了多少个bug。 那么我是不是又要写一个工具来实现呢？ 那么以后换一个维度，某个人某个时间段，某种状态的bug数量。怎么办？？

    这里，我看了网上的案例，是设计一个 queryPlan的模式，让llm输出 queryPlan，然后 后端拿到 queryPlan之后呢，生成 sql。

    ```
        SUPPORTED_BUG_METRICS = {
            "created_bug_count": {
                "label": "创建 Bug 数",
                "sql": "COUNT(*)",
            },
            "closed_bug_count": {
                "label": "已关闭 Bug 数",
                "sql": "SUM(CASE WHEN bugs.status = 'closed' THEN 1 ELSE 0 END)",
            },
            "close_rate": {
                "label": "关闭率",
                "sql": (
                    "ROUND("
                    "SUM(CASE WHEN bugs.status = 'closed' THEN 1 ELSE 0 END) "
                    "/ NULLIF(COUNT(*), 0) * 100, 2"
                    ")"
                ),
            },
            "reopened_bug_count": {
                "label": "重开 Bug 数",
                "sql": "SUM(CASE WHEN bugs.reopened_count > 0 THEN 1 ELSE 0 END)",
            },
            "suspended_bug_count": {
                "label": "挂起 Bug 数",
                "sql": "SUM(CASE WHEN bugs.status = 'suspended' THEN 1 ELSE 0 END)",
            },
        }


        SUPPORTED_BUG_FILTERS = {
            "status": "bugs.status",
            "assignee_id": "bugs.assignee_id",
            "reporter_id": "bugs.reporter_id",
            "verifier_id": "bugs.verifier_id",
            "module_name": "bugs.module_name",
            "product_line": "bugs.product_line",
            "severity": "bugs.severity",
            "priority": "bugs.priority",
            "requirement_id": "bugs.requirement_id",
        }


        SUPPORTED_BUG_GROUP_BY = {
            "status": "bugs.status",
            "assignee_id": "bugs.assignee_id",
            "reporter_id": "bugs.reporter_id",
            "module_name": "bugs.module_name",
            "product_line": "bugs.product_line",
            "severity": "bugs.severity",
            "priority": "bugs.priority",
        }
    ```

