USE agent_workflow;

CREATE TABLE IF NOT EXISTS llm_conversations (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  trace_id VARCHAR(64) NOT NULL,
  session_id VARCHAR(100) NOT NULL,
  user_input TEXT NOT NULL,
  final_output TEXT NULL,
  model_name VARCHAR(100) NOT NULL,
  provider VARCHAR(100) NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'success',
  error_message TEXT NULL,
  prompt_tokens INT UNSIGNED NULL,
  completion_tokens INT UNSIGNED NULL,
  total_tokens INT UNSIGNED NULL,
  duration_ms INT UNSIGNED NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  UNIQUE KEY uk_llm_conversations_trace_id (trace_id),
  KEY idx_llm_conversations_session_id (session_id),
  KEY idx_llm_conversations_created_at (created_at),
  KEY idx_llm_conversations_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS llm_messages (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  trace_id VARCHAR(64) NOT NULL,
  session_id VARCHAR(100) NOT NULL,
  message_order INT UNSIGNED NOT NULL,
  role VARCHAR(30) NOT NULL,
  content LONGTEXT NOT NULL,
  message_type VARCHAR(30) NOT NULL DEFAULT 'chat',
  tool_name VARCHAR(100) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  KEY idx_llm_messages_trace_id_order (trace_id, message_order),
  KEY idx_llm_messages_session_id (session_id),
  CONSTRAINT fk_llm_messages_trace_id
    FOREIGN KEY (trace_id)
    REFERENCES llm_conversations(trace_id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
