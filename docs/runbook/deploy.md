# GradeInsight 部署手册

## 1. 初始化环境
1. 复制环境变量：
   ```bash
   cp .env.example .env
   ```
2. 根据实际域名和公网地址修改 `.env`：
   - `DJANGO_DEBUG=0`
   - `DJANGO_ALLOWED_HOSTS=<your-domain>,<your-ip>`
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-domain>`

## 2. 启动服务
```bash
docker compose up -d --build
```

## 3. 初始化数据库
```bash
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py createsuperuser
```

## 4. 验证服务
```bash
docker compose ps
docker compose logs -f --tail=200 web
```

默认访问：
- 应用：`http://<server-ip>:8000`（直接访问 web）
- 反向代理：`http://<server-ip>`（经 Caddy）

## 5. 生产建议
- 使用正式域名并在 `docker/caddy/Caddyfile` 中配置站点
- `DJANGO_SECRET_KEY` 使用高强度随机值
- 周期执行备份脚本 `ops/backup_pg.sh`
