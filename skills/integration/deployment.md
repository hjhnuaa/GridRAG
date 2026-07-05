# Deployment

## 职责

说明本地运行和部署时需要准备的服务、环境变量和启动顺序。

## 当前实现位置

- `README.md`：快速启动、环境变量和常见问题。
- `.env.example`：环境变量模板。
- `environment.yml`：Conda 环境定义。
- `scripts/setup_conda.ps1`：环境准备脚本。

## 扩展方向

- 增加 Docker Compose 示例。
- 区分开发、演示和生产配置。
- 补充 MySQL、Redis、Chroma 存储目录的备份策略。
