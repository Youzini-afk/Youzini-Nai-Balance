<!--
PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD
-->
# 贡献指南（中文）

欢迎共建。优先保证：安全、可运维、易部署、改动可回滚。

## 1) 开发环境

- Python：建议 `3.12+`（Ubuntu 24 / venv）
- Windows：PowerShell + venv 也可（仓库已有测试脚本）

后端依赖安装（Windows 示例）：

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) 启动项目

在 `backend/` 目录创建 `.env`：
- 复制 `backend/.env.example` → `backend/.env`
- 填好 `SECRET_KEY`、`ENCRYPTION_KEY`、`ADMIN_USERNAME`、`ADMIN_PASSWORD`

启动：

```bash
python run.py
```

访问：
- `http://127.0.0.1:5002/`

## 3) 运行测试

在 `backend/` 目录运行：

```bash
$env:PYTHONPATH='.'
python tests/smoke_test.py
python tests/api_test.py
```

## 4) 代码风格与约定

本项目目前的代码风格偏向“轻量、可读、可运维”，供参考（不做强制要求）：

- Python：以 FastAPI + SQLAlchemy Async 为主，函数/变量名使用清晰语义命名
- 配置：集中在 `backend/app/config.py`，敏感配置仅允许通过 `.env` 设置
- 安全：默认安全（CORS 默认关闭、默认不信任反代 IP 头、前端避免未转义的 `innerHTML`）
- 结构：路由在 `backend/app/routers/`，核心逻辑在 `backend/app/services/`，后台循环任务在 `backend/app/tasks/`

## 5) 提交内容建议

提交 PR 前请自查：
- [ ] 新功能是否带来安全风险（鉴权、XSS、CORS、日志泄露、敏感配置）？
- [ ] 是否需要更新文档（`README.md` 或 `docs/`）？
- [ ] 是否有对应测试或至少手动验证步骤？
- [ ] 多机模式是否考虑到“每节点重复任务”的问题（leader-only）？

## 6) 目录结构（简述）

- `backend/app/routers/`：HTTP API 路由
- `backend/app/services/`：业务逻辑（加密、鉴权、池、代理池、防爆破等）
- `backend/app/tasks/`：后台循环任务调度（健康检测/探活）
- `frontend/`：静态前端（由后端提供）
- `docs/`：部署/配置/API/安全等文档（中文默认 + 英文版）

## 7) 安全与合规

本项目的“代理池/多出口”功能仅用于线路容灾/保活，不用于规避上游限制或其他不当用途。
