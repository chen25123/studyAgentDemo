USE agent_workflow;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE workflow_attachments;
TRUNCATE TABLE workflow_comments;
TRUNCATE TABLE workflow_status_logs;
TRUNCATE TABLE bugs;
TRUNCATE TABLE requirements;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

SET SESSION cte_max_recursion_depth = 200000;

INSERT INTO users (
  username,
  display_name,
  email,
  phone,
  avatar_url,
  department,
  job_title,
  role_code,
  status,
  last_login_at,
  created_at,
  updated_at
)
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 500
)
SELECT
  CONCAT('user_', LPAD(n, 4, '0')),
  CONCAT('用户', LPAD(n, 4, '0')),
  CONCAT('user_', LPAD(n, 4, '0'), '@example.com'),
  CONCAT('138', LPAD(n, 8, '0')),
  CONCAT('https://example.com/avatar/', n, '.png'),
  ELT((n MOD 8) + 1, '产品中心', '研发一部', '研发二部', '测试中心', '运维平台', '数据平台', '设计中心', '客户成功'),
  ELT((n MOD 9) + 1, '产品经理', '后端工程师', '前端工程师', '测试工程师', '架构师', '运维工程师', '数据工程师', '设计师', '项目经理'),
  ELT((n MOD 6) + 1, 'admin', 'product', 'developer', 'tester', 'ops', 'member'),
  IF(n MOD 37 = 0, 'disabled', 'active'),
  TIMESTAMPADD(DAY, -(n MOD 90), NOW()),
  TIMESTAMP('2026-03-01 09:00:00') + INTERVAL (n MOD 90) DAY,
  TIMESTAMP('2026-03-01 09:00:00') + INTERVAL (n MOD 90) DAY + INTERVAL (n MOD 10) HOUR
FROM seq;

INSERT INTO requirements (
  requirement_no,
  title,
  description,
  status,
  priority,
  requirement_type,
  source,
  product_line,
  module_name,
  version_name,
  business_value,
  acceptance_criteria,
  creator_id,
  product_owner_id,
  developer_owner_id,
  tester_owner_id,
  planned_start_at,
  planned_due_at,
  actual_start_at,
  actual_done_at,
  released_at,
  created_at,
  updated_at,
  created_by,
  updated_by,
  version
)
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 20000
)
SELECT
  CONCAT('REQ-2026-', LPAD(n, 6, '0')),
  CONCAT(ELT((n MOD 8) + 1, '登录体验优化', '订单流程改造', '报表中心升级', '权限体系重构', '消息通知增强', '移动端适配', '搜索性能优化', '结算规则调整'), ' #', n),
  CONCAT('这是第 ', n, ' 条模拟需求，覆盖澄清、开发、测试、上线等不同阶段。'),
  ELT((n MOD 9) + 1, 'clarifying', 'clarified', 'pending_development', 'developing', 'development_done', 'pending_testing', 'testing', 'testing_done', 'released'),
  ELT((n MOD 4) + 1, 'low', 'medium', 'high', 'urgent'),
  ELT((n MOD 5) + 1, 'feature', 'optimization', 'compliance', 'data', 'technical_debt'),
  ELT((n MOD 6) + 1, 'customer', 'internal', 'operation', 'market', 'data_analysis', 'risk_control'),
  ELT((n MOD 6) + 1, '交易平台', '用户增长', '数据中台', '客服系统', '开放平台', '财务结算'),
  ELT((n MOD 10) + 1, '账号', '订单', '支付', '报表', '权限', '消息', '搜索', '库存', '合同', '审批'),
  CONCAT('v', 1 + (n MOD 5), '.', n MOD 12),
  CONCAT('预计提升核心指标，样本编号 ', n),
  CONCAT('验收标准：主流程通过，异常路径有提示，日志可追踪，编号 ', n),
  1 + (n MOD 500),
  1 + ((n + 7) MOD 500),
  1 + ((n + 19) MOD 500),
  1 + ((n + 31) MOD 500),
  TIMESTAMP('2026-03-01 09:00:00') + INTERVAL (n MOD 92) DAY,
  TIMESTAMP('2026-03-01 09:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (3 + (n MOD 21)) DAY,
  IF(n MOD 9 IN (3,4,5,6,7,8), TIMESTAMP('2026-03-01 09:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (n MOD 3) DAY, NULL),
  IF(n MOD 9 IN (4,5,6,7,8), TIMESTAMP('2026-03-01 09:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (5 + (n MOD 21)) DAY, NULL),
  IF(n MOD 9 = 8, TIMESTAMP('2026-03-01 09:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (10 + (n MOD 25)) DAY, NULL),
  TIMESTAMP('2026-03-01 09:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (n MOD 24) HOUR,
  TIMESTAMP('2026-03-01 09:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (n MOD 24) HOUR + INTERVAL (n MOD 20) DAY,
  1 + (n MOD 500),
  1 + ((n + 11) MOD 500),
  1 + (n MOD 9)
FROM seq;

INSERT INTO bugs (
  bug_no,
  title,
  description,
  status,
  severity,
  priority,
  bug_type,
  source,
  product_line,
  module_name,
  environment,
  reproduce_steps,
  expected_result,
  actual_result,
  root_cause,
  fix_solution,
  requirement_id,
  reporter_id,
  assignee_id,
  verifier_id,
  found_version,
  fixed_version,
  planned_due_at,
  fixed_at,
  verified_at,
  closed_at,
  reopened_count,
  created_at,
  updated_at,
  created_by,
  updated_by,
  version
)
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 80000
)
SELECT
  CONCAT('BUG-2026-', LPAD(n, 6, '0')),
  CONCAT(ELT((n MOD 10) + 1, '页面按钮无响应', '接口返回异常', '权限校验缺失', '报表数据不一致', '移动端样式错位', '支付回调失败', '搜索结果重复', '消息延迟', '导出文件乱码', '审批状态错误'), ' #', n),
  CONCAT('这是第 ', n, ' 条模拟 Bug，覆盖新建、处理中、修复、挂起、重开、打回和关闭。'),
  ELT((n MOD 7) + 1, 'new', 'processing', 'fixed', 'suspended', 'reopened', 'rejected', 'closed'),
  ELT((n MOD 4) + 1, 'minor', 'major', 'critical', 'blocker'),
  ELT((n MOD 4) + 1, 'low', 'medium', 'high', 'urgent'),
  ELT((n MOD 6) + 1, 'functional', 'performance', 'security', 'compatibility', 'data', 'ui'),
  ELT((n MOD 5) + 1, 'qa', 'customer', 'monitoring', 'dogfood', 'operation'),
  ELT((n MOD 6) + 1, '交易平台', '用户增长', '数据中台', '客服系统', '开放平台', '财务结算'),
  ELT((n MOD 10) + 1, '账号', '订单', '支付', '报表', '权限', '消息', '搜索', '库存', '合同', '审批'),
  ELT((n MOD 5) + 1, 'production', 'staging', 'test', 'windows_chrome', 'ios_app'),
  CONCAT('1. 打开模块；2. 输入测试数据；3. 点击提交；样本编号 ', n),
  CONCAT('系统应按预期完成操作，编号 ', n),
  CONCAT('系统出现异常表现，编号 ', n),
  IF(n MOD 7 IN (2,4,6), CONCAT('边界条件处理不完整，编号 ', n), NULL),
  IF(n MOD 7 IN (2,6), CONCAT('补充校验并增加回归用例，编号 ', n), NULL),
  IF(n MOD 10 = 0, NULL, 1 + (n MOD 20000)),
  1 + ((n + 3) MOD 500),
  IF(n MOD 7 = 0, NULL, 1 + ((n + 17) MOD 500)),
  IF(n MOD 7 IN (2,6), 1 + ((n + 29) MOD 500), NULL),
  CONCAT('v', 1 + (n MOD 5), '.', n MOD 12),
  IF(n MOD 7 IN (2,6), CONCAT('v', 1 + ((n + 1) MOD 5), '.', (n + 2) MOD 12), NULL),
  TIMESTAMP('2026-03-01 10:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (1 + (n MOD 14)) DAY,
  IF(n MOD 7 IN (2,6), TIMESTAMP('2026-03-01 10:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (1 + (n MOD 7)) DAY, NULL),
  IF(n MOD 7 = 6, TIMESTAMP('2026-03-01 10:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (2 + (n MOD 9)) DAY, NULL),
  IF(n MOD 7 = 6, TIMESTAMP('2026-03-01 10:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (3 + (n MOD 10)) DAY, NULL),
  IF(n MOD 7 = 4, 1 + (n MOD 4), 0),
  TIMESTAMP('2026-03-01 10:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (n MOD 24) HOUR,
  TIMESTAMP('2026-03-01 10:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (n MOD 24) HOUR + INTERVAL (n MOD 15) DAY,
  1 + ((n + 3) MOD 500),
  1 + ((n + 17) MOD 500),
  1 + (n MOD 6)
FROM seq;

INSERT INTO workflow_status_logs (
  entity_type,
  entity_id,
  from_status,
  to_status,
  reason,
  operator_id,
  operated_at
)
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 70000
)
SELECT
  IF(n MOD 5 = 0, 'requirement', 'bug'),
  IF(n MOD 5 = 0, 1 + (n MOD 20000), 1 + (n MOD 80000)),
  CASE
    WHEN n MOD 5 = 0 THEN ELT((n MOD 9) + 1, NULL, 'clarifying', 'clarified', 'pending_development', 'developing', 'development_done', 'pending_testing', 'testing', 'testing_done')
    ELSE ELT((n MOD 7) + 1, NULL, 'new', 'processing', 'fixed', 'suspended', 'reopened', 'rejected')
  END,
  CASE
    WHEN n MOD 5 = 0 THEN ELT((n MOD 9) + 1, 'clarifying', 'clarified', 'pending_development', 'developing', 'development_done', 'pending_testing', 'testing', 'testing_done', 'released')
    ELSE ELT((n MOD 7) + 1, 'new', 'processing', 'fixed', 'suspended', 'reopened', 'rejected', 'closed')
  END,
  CONCAT('模拟状态流转记录 ', n),
  1 + (n MOD 500),
  TIMESTAMP('2026-03-01 08:30:00') + INTERVAL (n MOD 92) DAY + INTERVAL (n MOD 86400) SECOND
FROM seq;

INSERT INTO workflow_comments (
  entity_type,
  entity_id,
  content,
  author_id,
  created_at,
  updated_at
)
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 30000
)
SELECT
  IF(n MOD 4 = 0, 'requirement', 'bug'),
  IF(n MOD 4 = 0, 1 + (n MOD 20000), 1 + (n MOD 80000)),
  CONCAT('模拟评论 ', n, '：补充背景、处理结论或测试反馈。'),
  1 + (n MOD 500),
  TIMESTAMP('2026-03-01 11:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (n MOD 86400) SECOND,
  TIMESTAMP('2026-03-01 11:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (n MOD 86400) SECOND
FROM seq;

INSERT INTO workflow_attachments (
  entity_type,
  entity_id,
  file_name,
  file_url,
  file_size,
  mime_type,
  uploader_id,
  created_at
)
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 12000
)
SELECT
  IF(n MOD 3 = 0, 'requirement', 'bug'),
  IF(n MOD 3 = 0, 1 + (n MOD 20000), 1 + (n MOD 80000)),
  CONCAT('attachment_', LPAD(n, 6, '0'), IF(n MOD 5 = 0, '.xlsx', IF(n MOD 2 = 0, '.png', '.log'))),
  CONCAT('https://files.example.com/workflow/', n),
  1024 + (n MOD 10485760),
  IF(n MOD 5 = 0, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', IF(n MOD 2 = 0, 'image/png', 'text/plain')),
  1 + (n MOD 500),
  TIMESTAMP('2026-03-01 12:00:00') + INTERVAL (n MOD 92) DAY + INTERVAL (n MOD 86400) SECOND
FROM seq;

SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
UNION ALL
SELECT 'requirements', COUNT(*) FROM requirements
UNION ALL
SELECT 'bugs', COUNT(*) FROM bugs
UNION ALL
SELECT 'workflow_status_logs', COUNT(*) FROM workflow_status_logs
UNION ALL
SELECT 'workflow_comments', COUNT(*) FROM workflow_comments
UNION ALL
SELECT 'workflow_attachments', COUNT(*) FROM workflow_attachments;
