# Development Guidelines

本项目后续开发默认遵守本文规范。若规范之间冲突，优先级为：

1. 安全性、正确性、数据一致性
2. 项目现有约定
3. 官方框架规范
4. 自动化工具格式化结果

## Frontend: Vue 3 + Vite + TypeScript

- 使用 Vue 3 单文件组件，组件名使用多词命名，根组件 `App.vue` 除外。
- 组件 props 必须写明确类型；复杂结构使用 `interface` 或 `type`。
- TypeScript 开启 `strict`，禁止用 `any` 绕过类型系统。边界数据使用 `unknown`，再用类型守卫收窄。
- 业务状态、消息结构、接口返回值都要有明确类型定义。
- Vite 环境变量只使用 `VITE_` 前缀暴露给前端，禁止把密钥、数据库密码、后端 token 写进前端环境变量。
- 用户可见的功能必须至少通过 `npm run build` 验证；涉及界面交互时，还要做浏览器层验证。
- 样式保持可读、响应式、无元素重叠；按钮、输入框、列表、面板必须有稳定尺寸和移动端适配。
- 前端只负责展示和调用后端 API，不直接连接数据库。

## Python Backend / Agent

- 遵守 PEP 8：命名清晰，函数和模块职责单一，缩进 4 空格。
- 公共模块、类、复杂函数写 docstring，遵守 PEP 257 的语义和格式。
- 新代码必须写类型标注；复杂字典结构优先使用 `TypedDict`、`dataclass` 或 Pydantic 模型。
- 配置全部来自环境变量或 `.env`，禁止硬编码 API Key、数据库密码等敏感信息。
- 使用参数化 SQL 或受控查询构造，禁止拼接用户输入生成可执行 SQL。
- Agent 工具必须定义输入、输出、错误处理和权限边界。
- 可写操作必须有确认、审计日志和事务保护。
- 对 LLM 输出不能盲信：SQL、状态流转、批量操作都必须经过规则校验。

## Formatting And Quality Gates

- Python 推荐使用 Ruff 统一 lint 和 format；如项目引入 Black，则以 Black 格式化结果为准。
- 前端使用 TypeScript 编译和 Vite build 作为最低检查门槛。
- 修改前端后运行：

```powershell
npm.cmd run build
```

- 修改 Python 后，在 Python 环境可用时运行：

```powershell
ruff check .
ruff format --check .
```

- 后续引入测试后，数据库工具、Agent 状态流转、SQL 生成、安全校验必须有测试覆盖。

## Database And Agent Safety

- 表字段变更必须考虑迁移、索引、历史数据兼容。
- 查询类 Agent 默认只读；写操作单独开放工具，不允许自然语言直接变成任意 SQL。
- 数据统计必须明确口径，例如“新建 Bug”默认表示创建时间在统计区间内，而不是 `status = 'new'`。
- 所有状态变更写入状态日志，保留操作者、原状态、新状态、原因和时间。
- API 设计遵守最小权限原则，避免越权访问和过度暴露字段。

## Sources

- Vue Style Guide: https://vuejs.org/style-guide/rules-essential.html
- Vite Env Variables: https://vite.dev/guide/env-and-mode/
- Vite Build: https://vite.dev/guide/build
- TypeScript Handbook: https://www.typescriptlang.org/docs/handbook/2/basic-types.html
- PEP 8: https://peps.python.org/pep-0008/
- PEP 257: https://peps.python.org/pep-0257/
- Python Typing Specification: https://typing.python.org/en/latest/spec/type-system.html
- Ruff Linter: https://docs.astral.sh/ruff/linter/
- Black Code Style: https://black.readthedocs.io/en/stable/the_black_code_style/index.html
- OWASP Top 10: https://owasp.org/Top10/2021/
- OWASP API Security Top 10: https://owasp.org/API-Security/editions/2023/en/0x00-header/
- Twelve-Factor Config: https://www.12factor.net/config
- Python Packaging / pyproject.toml: https://packaging.python.org/specifications/declaring-project-metadata/
