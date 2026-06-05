USE agent_workflow;

-- ============================================================
-- 语义层 (Metric Layer) 建表
-- Entity → Dimension → Measure → Metric → QueryPlan
-- ============================================================

-- 1. 实体定义
CREATE TABLE IF NOT EXISTS entity_definitions (
    id           BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    entity_code  VARCHAR(40)  NOT NULL,
    entity_name  VARCHAR(100) NOT NULL,
    base_table   VARCHAR(100) NOT NULL,
    primary_key  VARCHAR(100) NOT NULL DEFAULT 'id',
    default_time_field   VARCHAR(100) NULL,
    default_filter       VARCHAR(500) NULL,
    description  TEXT NULL,
    status       VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_entity_definitions_code (entity_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- 2. 维度定义
CREATE TABLE IF NOT EXISTS dimension_definitions (
    id                BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    entity_code       VARCHAR(40)  NOT NULL,
    dimension_code    VARCHAR(100) NOT NULL,
    dimension_name    VARCHAR(100) NOT NULL,
    field_expression  VARCHAR(300) NOT NULL,
    join_config       JSON NULL,
    data_type         VARCHAR(30)  NOT NULL DEFAULT 'string',
    is_filterable     TINYINT(1)   NOT NULL DEFAULT 1,
    is_groupable      TINYINT(1)   NOT NULL DEFAULT 1,
    allowed_values    JSON NULL,
    status            VARCHAR(20)  NOT NULL DEFAULT 'active',
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_dimension_definitions (entity_code, dimension_code),
    CONSTRAINT fk_dim_entity FOREIGN KEY (entity_code)
        REFERENCES entity_definitions(entity_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- 3. 度量定义
CREATE TABLE IF NOT EXISTS measure_definitions (
    id             BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    measure_code   VARCHAR(100) NOT NULL,
    measure_name   VARCHAR(100) NOT NULL,
    entity_code    VARCHAR(40)  NOT NULL,
    aggregation    VARCHAR(30)  NOT NULL DEFAULT 'count',
    expression     VARCHAR(300) NOT NULL DEFAULT '*',
    filter_config  JSON NULL,
    description    TEXT NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_measure_definitions_code (measure_code),
    CONSTRAINT fk_measure_entity FOREIGN KEY (entity_code)
        REFERENCES entity_definitions(entity_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- 4. 指标定义
CREATE TABLE IF NOT EXISTS metric_definitions (
    id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    metric_code     VARCHAR(100) NOT NULL,
    metric_name     VARCHAR(200) NOT NULL,
    entity_code     VARCHAR(40)  NOT NULL,
    formula_type    VARCHAR(30)  NOT NULL DEFAULT 'count',
    formula_config  JSON         NOT NULL,
    time_field      VARCHAR(100) NULL,
    format_type     VARCHAR(20)  NOT NULL DEFAULT 'number',
    description     TEXT         NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'draft',
    version         INT UNSIGNED NOT NULL DEFAULT 1,
    created_by      BIGINT UNSIGNED NULL,
    updated_by      BIGINT UNSIGNED NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,

    UNIQUE KEY uk_metric_definitions_code (metric_code),
    CONSTRAINT fk_metric_entity FOREIGN KEY (entity_code)
        REFERENCES entity_definitions(entity_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- 5. 指标变更日志
CREATE TABLE IF NOT EXISTS metric_change_logs (
    id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    metric_id       BIGINT UNSIGNED NOT NULL,
    change_type     VARCHAR(30)  NOT NULL,
    before_config   JSON NULL,
    after_config    JSON NULL,
    operator_id     BIGINT UNSIGNED NULL,
    reason          VARCHAR(500) NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    KEY idx_metric_change_logs_metric (metric_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- 6. 指标查询日志（审计）
CREATE TABLE IF NOT EXISTS metric_query_logs (
    id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    trace_id        VARCHAR(64)  NOT NULL,
    session_id      VARCHAR(100) NOT NULL,
    query_plan      JSON         NOT NULL,
    compiled_sql    TEXT         NOT NULL,
    duration_ms     INT UNSIGNED NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'success',
    error_message   TEXT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    KEY idx_metric_query_logs_trace (trace_id),
    KEY idx_metric_query_logs_session (session_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
