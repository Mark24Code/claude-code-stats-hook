# Claude Code Stats Hook

用于跟踪 Claude Code 代码变更的并发安全 hook。

## 特性

- 🔒 **并发安全**：多个 agents 同时工作，无竞态条件
- 🚀 **无 Git 依赖**：直接从 stdin 读取参数，避免 git diff 的累积状态问题
- 📅 **按日期组织**：统计数据按日期自动分文件存储

## 安装

### 1. 克隆并安装

```bash
git clone https://github.com/Mark24Code/claude-code-stats-hook.git
cd claude-code-stats-hook
python install.py
```

### 2. 配置 Claude Code

安装脚本会显示配置内容，将其**复制粘贴**到 `~/.claude/settings.local.json`：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/claude-code-stats-hook/post_stat.py"
          }
        ]
      }
    ]
  }
}
```

**注意**：如果 `settings.local.json` 不存在，创建该文件并复制配置；如果已存在，将 hooks 部分合并到现有配置中。

### 3. 查看统计

```bash
# 使用 Claude Code 进行一些操作后
python ~/.claude/hooks/claude-code-stats-hook/view_stats.py
```

## 工作原理

### 为什么能解决并发冲突？

传统的 git diff 方案在多个 agents 并发时会出现竞态条件。本方案通过以下方式解决：

**架构设计**
- **直接计算**：从 stdin 读取工具参数直接计算统计，不依赖 git diff
- **独立操作**：每次 hook 调用独立计算，无累积状态
- **文件锁机制**：使用 `fcntl.flock` 确保多进程并发写入安全

**文件锁实现**
```python
import fcntl

def append_to_stats(record):
    with open(stats_file, 'a') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 获取排他锁
        try:
            f.write(json.dumps(record) + '\n')
            f.flush()
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 释放锁
```

**对比**

| 特性 | 本方案 | Git diff 方案 |
|-----|--------|--------------|
| 并发安全 | ✅ 文件锁，无竞态 | ❌ 竞态条件 |
| 准确性 | ✅ 直接跟踪操作 | ⚠️ 累积状态，可能误差 |
| 复杂度 | ✅ 单个 hook | ❌ 需要前后 hook |
| 性能 | ✅ 无 git 命令 | ⚠️ 需要 git diff |

### 统计计算

**Write 工具**
```python
additions = count_lines(content)
deletions = 0
```

**Edit 工具**
```python
old_lines = count_lines(old_string)
new_lines = count_lines(new_string)
additions = max(0, new_lines - old_lines)
deletions = max(0, old_lines - new_lines)
```

**NotebookEdit 工具**
```python
additions = count_lines(new_source)
deletions = 0
```

## 查看统计

```bash
# 显示今天的统计
python view_stats.py

# 显示指定日期
python view_stats.py --date 2026-02-01

# 显示所有历史
python view_stats.py --history

# 显示最近 N 条
python view_stats.py --recent 20

# 列出所有日期
python view_stats.py --list
```

**统计内容**
- 📊 日期汇总：总操作数、新增/删除行数、净变化
- 👤 按用户统计：每个用户的代码变更量
- 🔧 按工具统计：各工具的使用频率
- 💬 按会话统计：每个会话的操作详情

## 数据格式

统计数据存储在 `code-log/` 目录，按日期组织（每天一个 JSONL 文件）：

```json
{
  "timestamp": "2026-02-02T15:42:37+08:00",
  "session_id": "1738483845",
  "email": "user@example.com",
  "tool": "Write",
  "additions": 100,
  "deletions": 0,
  "net_change": 100
}
```

## 更新

```bash
# 更新到最新版本（自动备份数据）
python install.py update
```

## 数据管理

```bash
# 查看数据大小
du -sh code-log

# 清理 30 天前的数据
find code-log -name "*.jsonl" -mtime +30 -delete

# 备份数据
tar -czf stats-backup-$(date +%Y%m%d).tar.gz code-log/
```

## 故障排除

**没有记录统计信息？**
1. 检查 hook 是否可执行：`ls -l post_stat.py`
2. 检查 `~/.claude/settings.local.json` 中是否正确配置
3. 查看 Claude Code 输出的 stderr 是否有错误

**行数统计不对？**
- Hook 使用换行符计数
- 空字符串 = 0 行
- 无尾随换行符的文本 = 行数 + 1

## 许可证

MIT License
