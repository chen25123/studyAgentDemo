USE agent_workflow;

CREATE TABLE IF NOT EXISTS org_units (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  parent_id BIGINT UNSIGNED NULL,
  org_code VARCHAR(64) NOT NULL,
  org_name VARCHAR(100) NOT NULL,
  org_type VARCHAR(30) NOT NULL,
  path VARCHAR(500) NULL,
  level INT UNSIGNED NOT NULL DEFAULT 1,
  sort_order INT UNSIGNED NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,

  UNIQUE KEY uk_org_units_code (org_code),
  KEY idx_org_units_parent (parent_id),
  KEY idx_org_units_type (org_type),
  KEY idx_org_units_path (path),
  CONSTRAINT fk_org_units_parent FOREIGN KEY (parent_id) REFERENCES org_units(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_org_memberships (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  org_unit_id BIGINT UNSIGNED NOT NULL,
  relation_type VARCHAR(30) NOT NULL DEFAULT 'primary',
  position_title VARCHAR(100) NULL,
  is_manager TINYINT(1) NOT NULL DEFAULT 0,
  started_at DATE NULL,
  ended_at DATE NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  UNIQUE KEY uk_user_org_relation (user_id, org_unit_id, relation_type),
  KEY idx_user_org_user (user_id),
  KEY idx_user_org_org (org_unit_id),
  CONSTRAINT fk_user_org_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_user_org_org FOREIGN KEY (org_unit_id) REFERENCES org_units(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE user_org_memberships;
TRUNCATE TABLE org_units;
SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO org_units (id, parent_id, org_code, org_name, org_type, level, sort_order)
VALUES
  (1, NULL, 'COMPANY', '星河科技', 'company', 1, 1),
  (2, 1, 'BU-RD', '研发中心', 'business_unit', 2, 1),
  (3, 1, 'BU-PRODUCT', '产品中心', 'business_unit', 2, 2),
  (4, 1, 'BU-QA', '测试中心', 'business_unit', 2, 3),
  (5, 1, 'BU-OPS', '运维平台', 'business_unit', 2, 4),
  (6, 1, 'BU-DATA', '数据平台', 'business_unit', 2, 5),
  (7, 1, 'BU-SUCCESS', '客户成功', 'business_unit', 2, 6),

  (20, 2, 'DEPT-RD-1', '研发一部', 'department', 3, 1),
  (21, 2, 'DEPT-RD-2', '研发二部', 'department', 3, 2),
  (22, 2, 'DEPT-ARCH', '架构组', 'department', 3, 3),
  (30, 3, 'DEPT-PRODUCT-A', '交易产品部', 'department', 3, 1),
  (31, 3, 'DEPT-PRODUCT-B', '增长产品部', 'department', 3, 2),
  (40, 4, 'DEPT-QA-AUTO', '自动化测试部', 'department', 3, 1),
  (41, 4, 'DEPT-QA-BIZ', '业务测试部', 'department', 3, 2),
  (50, 5, 'DEPT-OPS-SRE', 'SRE 部', 'department', 3, 1),
  (51, 5, 'DEPT-OPS-PLATFORM', '平台运维部', 'department', 3, 2),
  (60, 6, 'DEPT-DATA-WAREHOUSE', '数仓部', 'department', 3, 1),
  (61, 6, 'DEPT-DATA-ALGO', '算法部', 'department', 3, 2),
  (70, 7, 'DEPT-CS-IMPL', '实施交付部', 'department', 3, 1),
  (71, 7, 'DEPT-CS-SUPPORT', '客户支持部', 'department', 3, 2),

  (200, 20, 'TEAM-RD-ORDER', '订单研发组', 'team', 4, 1),
  (201, 20, 'TEAM-RD-PAY', '支付研发组', 'team', 4, 2),
  (202, 20, 'TEAM-RD-ACCOUNT', '账号研发组', 'team', 4, 3),
  (210, 21, 'TEAM-RD-SEARCH', '搜索研发组', 'team', 4, 1),
  (211, 21, 'TEAM-RD-MESSAGE', '消息研发组', 'team', 4, 2),
  (212, 21, 'TEAM-RD-CONTRACT', '合同研发组', 'team', 4, 3),
  (220, 22, 'TEAM-ARCH-BASE', '基础架构组', 'team', 4, 1),
  (221, 22, 'TEAM-ARCH-DEVOPS', 'DevOps 工具组', 'team', 4, 2),
  (300, 30, 'TEAM-PRODUCT-TRADE', '交易产品组', 'team', 4, 1),
  (301, 30, 'TEAM-PRODUCT-SETTLEMENT', '结算产品组', 'team', 4, 2),
  (310, 31, 'TEAM-PRODUCT-GROWTH', '增长策略组', 'team', 4, 1),
  (311, 31, 'TEAM-PRODUCT-CRM', '客户运营组', 'team', 4, 2),
  (400, 40, 'TEAM-QA-AUTO-REGRESSION', '自动化回归组', 'team', 4, 1),
  (401, 40, 'TEAM-QA-PERFORMANCE', '性能测试组', 'team', 4, 2),
  (410, 41, 'TEAM-QA-TRADE', '交易测试组', 'team', 4, 1),
  (411, 41, 'TEAM-QA-MOBILE', '移动测试组', 'team', 4, 2),
  (500, 50, 'TEAM-OPS-SRE-APP', '应用 SRE 组', 'team', 4, 1),
  (501, 50, 'TEAM-OPS-SRE-DB', '数据库 SRE 组', 'team', 4, 2),
  (510, 51, 'TEAM-OPS-CLOUD', '云平台组', 'team', 4, 1),
  (511, 51, 'TEAM-OPS-MONITOR', '监控平台组', 'team', 4, 2),
  (600, 60, 'TEAM-DATA-ODS', 'ODS 建模组', 'team', 4, 1),
  (601, 60, 'TEAM-DATA-BI', 'BI 分析组', 'team', 4, 2),
  (610, 61, 'TEAM-DATA-RECOMMEND', '推荐算法组', 'team', 4, 1),
  (611, 61, 'TEAM-DATA-RISK', '风控算法组', 'team', 4, 2),
  (700, 70, 'TEAM-CS-ENTERPRISE', '企业交付组', 'team', 4, 1),
  (701, 70, 'TEAM-CS-SMB', '中小客户交付组', 'team', 4, 2),
  (710, 71, 'TEAM-CS-L1', '一线支持组', 'team', 4, 1),
  (711, 71, 'TEAM-CS-L2', '专家支持组', 'team', 4, 2);

UPDATE org_units SET path = CONCAT('/', id, '/') WHERE parent_id IS NULL;
UPDATE org_units child
JOIN org_units parent ON child.parent_id = parent.id
SET child.path = CONCAT(parent.path, child.id, '/')
WHERE child.level = 2;
UPDATE org_units child
JOIN org_units parent ON child.parent_id = parent.id
SET child.path = CONCAT(parent.path, child.id, '/')
WHERE child.level = 3;
UPDATE org_units child
JOIN org_units parent ON child.parent_id = parent.id
SET child.path = CONCAT(parent.path, child.id, '/')
WHERE child.level = 4;

INSERT INTO user_org_memberships (
  user_id,
  org_unit_id,
  relation_type,
  position_title,
  is_manager,
  started_at
)
SELECT
  id AS user_id,
  CASE
    WHEN role_code = 'product' THEN ELT((id MOD 4) + 1, 300, 301, 310, 311)
    WHEN role_code = 'developer' THEN ELT((id MOD 8) + 1, 200, 201, 202, 210, 211, 212, 220, 221)
    WHEN role_code = 'tester' THEN ELT((id MOD 4) + 1, 400, 401, 410, 411)
    WHEN role_code = 'ops' THEN ELT((id MOD 4) + 1, 500, 501, 510, 511)
    WHEN role_code = 'admin' THEN ELT((id MOD 6) + 1, 20, 30, 40, 50, 60, 70)
    ELSE ELT((id MOD 8) + 1, 600, 601, 610, 611, 700, 701, 710, 711)
  END AS org_unit_id,
  'primary',
  job_title,
  IF(id MOD 37 = 0, 1, 0),
  DATE('2025-01-01') + INTERVAL (id MOD 365) DAY
FROM users;

INSERT INTO user_org_memberships (
  user_id,
  org_unit_id,
  relation_type,
  position_title,
  is_manager,
  started_at
)
SELECT
  id AS user_id,
  CASE
    WHEN role_code IN ('developer', 'tester') THEN ELT((id MOD 4) + 1, 300, 301, 310, 311)
    WHEN role_code = 'product' THEN ELT((id MOD 4) + 1, 200, 201, 210, 211)
    ELSE ELT((id MOD 4) + 1, 400, 410, 500, 600)
  END AS org_unit_id,
  'project',
  CONCAT('项目协作-', job_title),
  0,
  DATE('2026-03-01') + INTERVAL (id MOD 60) DAY
FROM users
WHERE id MOD 5 = 0;

SELECT org_type, COUNT(*) AS cnt
FROM org_units
GROUP BY org_type
ORDER BY cnt DESC;

SELECT relation_type, COUNT(*) AS cnt
FROM user_org_memberships
GROUP BY relation_type
ORDER BY cnt DESC;
