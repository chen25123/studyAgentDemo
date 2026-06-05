SUPPORTED_ORG_METRICS = {
    "org_unit_count": {
        "label": "组织节点数",
        "sql": "COUNT(*)",
    },
    "direct_children_count": {
        "label": "直属下级部门数",
        "sql": "COUNT(*)",
    },
}

SUPPORTED_ORG_FILTERS = {
    "org_name": {
        "sql_column": "org_units.org_name",
        "operator": "like",
    },
    "org_type": {
        "sql_column": "org_units.org_type",
    },
    "org_code": {
        "sql_column": "org_units.org_code",
    },
    "parent_id": {
        "sql_column": "org_units.parent_id",
    },
    "level": {
        "sql_column": "org_units.level",
    },
    "status": {
        "sql_column": "org_units.status",
    },
}

SUPPORTED_ORG_GROUP_BY = {
    "org_name": "org_units.org_name",
    "org_type": "org_units.org_type",
    "level": "org_units.level",
    "parent_id": "org_units.parent_id",
}
