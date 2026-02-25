# GradeInsight 备份手册

## 手工备份
```bash
bash ops/backup_pg.sh
```

环境变量：
- `OUT_DIR`：备份输出目录（默认 `/var/backups/gradeinsight`）
- `KEEP_DAYS`：保留天数（默认 30）

## 定时任务（cron）
每天凌晨 2 点执行：
```cron
0 2 * * * cd /path/to/gradeinsight && OUT_DIR=/var/backups/gradeinsight KEEP_DAYS=30 bash ops/backup_pg.sh >> /var/log/gradeinsight-backup.log 2>&1
```

## 恢复验证（最小流程）
1. 新建数据库
2. 执行恢复：
```bash
psql -U gradeinsight -d gradeinsight < /path/to/backup.sql
```
3. 启动应用并抽查考试/任务数据
