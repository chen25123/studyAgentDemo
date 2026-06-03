from datetime import datetime
from langchain_core.tools import tool

@tool
def get_now_date() -> str:
    """查询当前时间

    当你需要回答或者使用时间（比如这个月，上个月，三年前等）时调用。
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M")  # "2026-06-03 14:30"