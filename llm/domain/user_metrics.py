SUPPORTED_USER_METRICS = {
    "user_count": {
        "label": "员工总数",
        "sql": "COUNT(DISTINCT users.id)",
    },
    "active_user_count": {
        "label": "在职员工数",
        "sql": "SUM(CASE WHEN users.status = 'active' THEN 1 ELSE 0 END)",
    },
    "disabled_user_count": {
        "label": "禁用员工数",
        "sql": "SUM(CASE WHEN users.status = 'disabled' THEN 1 ELSE 0 END)",
    },
    "org_unit_count": {
        "label": "组织节点数",
        "sql": "COUNT(DISTINCT org_units.id)",
    },
}

# ----- 过滤条件 -----
# requires_join 为空 = 只查 users 表
# requires_join = ["membership", "org"] = 需要 JOIN user_org_memberships + org_units

SUPPORTED_USER_FILTERS = {
    "department": {
        "sql_column": "users.department",
        "requires_join": [],
    },
    "job_title": {
        "sql_column": "users.job_title",
        "requires_join": [],
    },
    "role_code": {
        "sql_column": "users.role_code",
        "requires_join": [],
    },
    "status": {
        "sql_column": "users.status",
        "requires_join": [],
    },
    "display_name": {
        "sql_column": "users.display_name",
        "requires_join": [],
        "operator": "like",
    },
    # --- 组织架构字段（需要 JOIN）---
    "org_name": {
        "sql_column": "org_units.org_name",
        "requires_join": ["membership", "org"],
        "operator": "like",
    },
    "org_type": {
        "sql_column": "org_units.org_type",
        "requires_join": ["membership", "org"],
    },
    "parent_org_id": {
        "sql_column": "org_units.parent_id",
        "requires_join": ["membership", "org"],
    },
    "org_level": {
        "sql_column": "org_units.level",
        "requires_join": ["membership", "org"],
    },
    "position_title": {
        "sql_column": "user_org_memberships.position_title",
        "requires_join": ["membership"],
        "operator": "like",
    },
    "is_manager": {
        "sql_column": "user_org_memberships.is_manager",
        "requires_join": ["membership"],
    },
    "relation_type": {
        "sql_column": "user_org_memberships.relation_type",
        "requires_join": ["membership"],
    },
}

# ----- 分组维度 -----

SUPPORTED_USER_GROUP_BY = {
    "department": {
        "sql_column": "users.department",
        "requires_join": [],
    },
    "job_title": {
        "sql_column": "users.job_title",
        "requires_join": [],
    },
    "role_code": {
        "sql_column": "users.role_code",
        "requires_join": [],
    },
    "status": {
        "sql_column": "users.status",
        "requires_join": [],
    },
    # --- 组织架构维度 ---
    "org_name": {
        "sql_column": "org_units.org_name",
        "requires_join": ["membership", "org"],
    },
    "org_type": {
        "sql_column": "org_units.org_type",
        "requires_join": ["membership", "org"],
    },
    "org_level": {
        "sql_column": "org_units.level",
        "requires_join": ["membership", "org"],
    },
    "position_title": {
        "sql_column": "user_org_memberships.position_title",
        "requires_join": ["membership"],
    },
}
