# GradeInsight 环境变量与运维检查手册

## 1. 这份手册覆盖什么

现有 `docs/runbook/deploy.md` 与 `docs/runbook/backup.md` 已经给出了最小部署与备份步骤。
这份补充手册聚焦：

- 环境变量含义
- 容器服务职责
- 上线前检查清单
- 常见故障的第一排查入口

---

## 2. 环境变量说明

以下变量来自 `.env.example` 与 `config/settings.py`。

| 变量名 | 默认值 | 用途 | 备注 |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | `replace-with-strong-secret`（示例） | Django 密钥 | 生产必须替换为高强度随机值 |
| `DJANGO_DEBUG` | `1` | 控制 Debug 模式 | 生产必须设为 `0` |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Django Host 白名单 | 生产需包含域名和公网 IP |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | 空 | CSRF 信任来源 | HTTPS 域名部署必须配置 |
| `DATABASE_URL` | `postgresql://gradeinsight:gradeinsight@db:5432/gradeinsight`（示例） | 数据库连接串 | 本地不配时回退到 SQLite |
| `GRADEINSIGHT_UPLOAD_MAX_BYTES` | `5242880` | 上传文件大小限制 | 默认 5MB |
| `GRADEINSIGHT_EPSILON` | `0.01` | 题目均分比较容差 | 影响“高于/低于平均分”和强弱项边界 |

---

## 3. 运行时组件

## 3.1 容器角色

`docker-compose.yml` 当前定义三个服务：

| 服务 | 作用 | 关键点 |
|---|---|---|
| `db` | PostgreSQL 16 | 带 `pg_isready` 健康检查 |
| `web` | Django + Gunicorn | 读取 `.env`，依赖 `db` 健康后启动 |
| `caddy` | 反向代理 | 当前默认只做 `:80 -> web:8000` 反代 |

## 3.2 Web 容器行为

`docker/web/Dockerfile` 当前会：

1. 使用 `python:3.12-slim`
2. 安装编译工具与 `curl`
3. 安装 `requirements.txt`
4. 复制整个项目到 `/app`
5. 用 Gunicorn 启动 `config.wsgi:application`

## 3.3 静态资源与前端依赖

当前运行时有两层前端依赖：

1. 本地静态资源
   - `static/`
   - 通过 `whitenoise` 提供
2. 外部 CDN 资源
   - Google Fonts
   - Bootstrap / Bootstrap Icons（jsDelivr）
   - HTMX（unpkg）
   - Chart.js（jsDelivr）

如果服务器所在网络无法访问这些外部 CDN，页面可能出现样式缺失、图表不显示、HTMX 交互失效等问题。

---

## 4. 上线前检查清单

## 4.1 基础配置

- [ ] `DJANGO_DEBUG=0`
- [ ] `DJANGO_SECRET_KEY` 已替换
- [ ] `DJANGO_ALLOWED_HOSTS` 已包含真实域名 / IP
- [ ] `DJANGO_CSRF_TRUSTED_ORIGINS` 已配置为真实 HTTPS 域名
- [ ] `DATABASE_URL` 指向目标 PostgreSQL

## 4.2 容器启动

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f --tail=200 web
```

确认点：

- `db` 为 `healthy`
- `web` 已启动且无导入错误
- `caddy` 正常监听

## 4.3 Django 初始化

```bash
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py collectstatic --noinput
docker compose run --rm web python manage.py createsuperuser
```

之所以建议执行 `collectstatic`，是因为当前 `STATICFILES_STORAGE` 使用的是 `whitenoise.storage.CompressedManifestStaticFilesStorage`。
如果线上以 `DJANGO_DEBUG=0` 运行，提前生成静态资源清单会更稳妥。

## 4.4 HTTP / HTTPS 入口

当前 `docker/caddy/Caddyfile` 默认是：

```caddy
:80 {
  encode zstd gzip
  reverse_proxy web:8000
}
```

这表示当前仓库默认提供的是 **HTTP 反向代理骨架**。
如果你要启用正式 HTTPS：

- 把 `:80` 改成真实域名
- 按真实站点需求扩展 Caddy 配置
- 再配置 `DJANGO_ALLOWED_HOSTS` 与 `DJANGO_CSRF_TRUSTED_ORIGINS`

---

## 5. 备份与恢复

## 5.1 备份脚本行为

`ops/backup_pg.sh` 会：

1. 创建输出目录
2. 执行 `docker compose exec -T db pg_dump -U gradeinsight gradeinsight`
3. 输出 SQL 文件
4. 按 `KEEP_DAYS` 删除过期备份

关键环境变量：

- `OUT_DIR`：备份输出目录，默认 `/var/backups/gradeinsight`
- `KEEP_DAYS`：保留天数，默认 `30`

## 5.2 手工执行

```bash
bash ops/backup_pg.sh
```

执行前请确认：

- `db` 容器正在运行
- 当前 shell 位于仓库根目录
- 备份目标目录有写权限

## 5.3 最小恢复验证

```bash
psql -U gradeinsight -d gradeinsight < /path/to/backup.sql
```

恢复后建议至少验证：

- 能否登录系统
- 考试列表是否可见
- 学生详情与任务详情是否可正常打开

---

## 6. 常见故障与第一排查入口

## 6.1 400 / CSRF 失败

先检查：

- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- 反向代理后的真实访问域名
- `templates/base.html` 中 HTMX 的 `X-CSRFToken` 注入逻辑

常见场景：

- 域名切换后没同步更新 `DJANGO_CSRF_TRUSTED_ORIGINS`
- 用 HTTPS 部署，但仍按 HTTP 域名填写信任来源

## 6.2 静态资源 404 或样式错乱

先检查：

- 是否执行了 `collectstatic`
- `STATIC_ROOT` 是否可写
- `web` 容器日志中是否有 WhiteNoise / staticfiles 相关错误

## 6.3 页面能打开但图表或交互失效

先检查：

- 浏览器控制台是否有 CDN 加载失败
- `templates/base.html` 中的 Chart.js / HTMX 是否成功加载
- 服务器网络是否能访问外部静态资源 CDN

## 6.4 导入功能报错

先检查：

- 上传文件大小是否超过 `GRADEINSIGHT_UPLOAD_MAX_BYTES`
- 文件后缀是否是 `.xls` / `.xlsx`
- 是否重复导入同一文件
- `web` 日志中是否有 Excel 解析异常

## 6.5 备份脚本失败

先检查：

- `db` 容器是否在运行
- 当前目录是否为仓库根目录
- `OUT_DIR` 是否有写权限
- `docker compose exec -T db pg_dump ...` 能否手工执行

---

## 7. 推荐的最小运维流程

如果是一次标准上线或迁移环境，推荐顺序是：

1. 配置 `.env`
2. `docker compose up -d --build`
3. `docker compose run --rm web python manage.py migrate`
4. `docker compose run --rm web python manage.py collectstatic --noinput`
5. `docker compose run --rm web python manage.py createsuperuser`
6. `docker compose ps`
7. `docker compose logs -f --tail=200 web`
8. 登录系统做最小冒烟检查
9. 运行一次备份脚本确认备份链路可用

这个顺序能覆盖配置、数据库、静态资源、登录与备份四类高频问题。
