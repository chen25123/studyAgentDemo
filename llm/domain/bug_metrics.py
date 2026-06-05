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