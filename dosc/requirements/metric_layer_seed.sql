USE agent_workflow;

-- ============================================================
-- 语义层种子数据：Bug 实体 + 9 维度 + 2 度量 + 1 指标
-- ============================================================

-- 1. 实体
INSERT INTO entity_definitions (entity_code, entity_name, base_table, primary_key, default_time_field, default_filter, description)
VALUES (
    'bug', 'Bug', 'bugs', 'id', 'created_at', 'deleted_at IS NULL',
    '研发流程缺陷管理'
);

-- 2. 维度（无 JOIN 的简单维度）
INSERT INTO dimension_definitions (entity_code, dimension_code, dimension_name, field_expression, data_type, is_filterable, is_groupable, allowed_values)
VALUES
    ('bug', 'status',      '状态',    'bugs.status',      'string', 1, 1, '["new","processing","fixed","closed","reopened","suspended","rejected"]'),
    ('bug', 'severity',    '严重程度', 'bugs.severity',    'string', 1, 1, '["minor","major","critical","blocker"]'),
    ('bug', 'priority',    '优先级',   'bugs.priority',    'string', 1, 1, '["low","medium","high","urgent"]'),
    ('bug', 'module_name', '模块',     'bugs.module_name', 'string', 1, 1, NULL),
    ('bug', 'product_line','产品线',   'bugs.product_line','string', 1, 1, NULL),
    ('bug', 'assignee_id', '负责人ID', 'bugs.assignee_id', 'integer', 1, 0, NULL),
    ('bug', 'reporter_id', '创建人ID', 'bugs.reporter_id', 'integer', 1, 0, NULL);

-- 3. 维度（需 JOIN 的组织维度）
INSERT INTO dimension_definitions (entity_code, dimension_code, dimension_name, field_expression, join_config, data_type, is_filterable, is_groupable)
VALUES
    ('bug', 'assignee_org_id', '负责人部门ID',
     'org_units.id',
     '{"joins": [{"table": "user_org_memberships", "on": "bugs.assignee_id = user_org_memberships.user_id AND user_org_memberships.ended_at IS NULL"}, {"table": "org_units", "on": "user_org_memberships.org_unit_id = org_units.id AND org_units.deleted_at IS NULL"}]}',
     'integer', 1, 1),

    ('bug', 'assignee_org_name', '负责人部门名称',
     'org_units.org_name',
     '{"joins": [{"table": "user_org_memberships", "on": "bugs.assignee_id = user_org_memberships.user_id AND user_org_memberships.ended_at IS NULL"}, {"table": "org_units", "on": "user_org_memberships.org_unit_id = org_units.id AND org_units.deleted_at IS NULL"}]}',
     'string', 1, 1);

-- 4. 度量
INSERT INTO measure_definitions (measure_code, measure_name, entity_code, aggregation, expression, filter_config, description)
VALUES
    ('bug_count', 'Bug 总数', 'bug',
     'count', '*', NULL,
     '统计 Bug 数量，默认排除软删除'),

    ('closed_bug_count', '已关闭 Bug 数', 'bug',
     'count', '*',
     '{"filters": [{"field": "bugs.status", "operator": "eq", "value": "closed"}]}',
     '当前状态为 closed 的 Bug 数');

-- 5. 指标：Bug 关闭率
INSERT INTO metric_definitions (
    metric_code, metric_name, entity_code,
    formula_type, formula_config,
    time_field, format_type, description, status
)
VALUES (
    'bug_close_rate', 'Bug 关闭率', 'bug',
    'ratio',
    '{"numerator": "closed_bug_count", "denominator": "bug_count"}',
    'created_at', 'percent',
    '统计周期内创建的 Bug 中，当前状态为 closed 的占比。关闭率 = 已关闭 Bug 数 / Bug 总数。',
    'active'
);

SELECT 'Entity' AS tbl, COUNT(*) AS cnt FROM entity_definitions
UNION ALL SELECT 'Dimension', COUNT(*) FROM dimension_definitions
UNION ALL SELECT 'Measure', COUNT(*) FROM measure_definitions
UNION ALL SELECT 'Metric', COUNT(*) FROM metric_definitions;
