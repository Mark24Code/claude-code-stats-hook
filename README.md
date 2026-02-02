# Claude code stats hook

用于跟踪 Claude Code agents 代码变更的并发安全 hook。

## 概述

此 hook 直接从 stdin 读取工具参数来计算统计信息，避免了使用 git diff 时在并发 agents 下出现的竞态条件。

**核心特性：**
- 📅 **按日期组织**：统计数据按日期自动分文件存储，便于管理和查询
- 🔒 **并发安全**：使用文件锁机制，支持多个 agents 同时工作
- 🌍 **跨平台兼容**：完美支持 Windows、macOS 和 Linux
- 🇨🇳 **全中文支持**：代码注释、日志输出、文档全部中文化
- 🛠️ **完整工具链**：提供测试套件和统计查看工具

## 工作原理

### 架构

- **单一 Hook**：只需要 `post_stat.py`（PostToolUse hook）
- **直接计算**：从 Claude Code 传递的 stdin 读取工具输入
- **无 Git 依赖**：独立于仓库状态工作
- **并发安全**：每次调用独立计算，使用文件锁防止写入冲突

### 支持的工具

- **Write**：统计新内容的行数
- **Edit**：比较 old_string 和 new_string 计算增删行数
- **NotebookEdit**：统计新源代码的行数

### 统计计算方式

```python
# Write 工具
additions = count_lines(content)
deletions = 0
net_change = additions

# Edit 工具
old_lines = count_lines(old_string)
new_lines = count_lines(new_string)
additions = max(0, new_lines - old_lines)
deletions = max(0, old_lines - new_lines)
net_change = new_lines - old_lines
```

## 快速开始

### 1. 验证安装

```bash
# 检查文件是否存在
ls -la .claude/hooks/stats-hooks/post_stat.py

# 确保有执行权限
chmod +x .claude/hooks/stats-hooks/post_stat.py
```

### 2. 运行测试

```bash
# 运行测试套件验证功能
python .claude/hooks/stats-hooks/test/test_post_stat.py
```

### 3. 查看统计

Hook 配置生效后，使用查看工具：

```bash
# 查看今天的统计
python .claude/hooks/stats-hooks/view_stats.py

# 查看历史统计
python .claude/hooks/stats-hooks/view_stats.py --history
```

## 设置

### 1. 配置

在 `.claude/settings.local.json` 中添加：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "/绝对路径/post_stat.py"
          }
        ]
      }
    ]
  }
}
```

### 2. 设置执行权限

```bash
chmod +x .claude/hooks/stats-hooks/post_stat.py
```

## 目录结构

```
.claude/hooks/stats-hooks/
├── post_stat.py              # 主 hook 脚本
├── view_stats.py             # 统计查看工具
├── README.md                 # 主文档
├── stats/                    # 统计数据目录（按日期组织）
│   ├── 2026-02-01.jsonl      # 2026-02-01 的统计记录
│   ├── 2026-02-02.jsonl      # 2026-02-02 的统计记录
│   └── 2026-02-03.jsonl      # 2026-02-03 的统计记录
└── test/                     # 测试套件目录
    ├── test_post_stat.py     # 主测试脚本
    ├── test_hook_input.py    # Hook 输入调试工具
    ├── run_tests.sh          # Unix 测试运行器
    ├── run_tests.bat         # Windows 测试运行器
    └── README.md             # 测试文档
```

## 输出格式

统计信息按日期组织，存储在 `stats/` 目录下，每天一个文件。

每个文件包含当天的所有统计记录：

```json
{
  "timestamp": "2026-02-02T15:42:37.737981+08:00",
  "session_id": "1738483845",
  "email": "user@example.com",
  "tool": "Write",
  "additions": 100,
  "deletions": 0,
  "net_change": 100
}
```

### 字段说明

- `timestamp`：ISO 8601 东八区（北京时间）时间戳
- `session_id`：会话标识符（从 stdin 获取或生成）
- `email`：Git 用户邮箱（从 `git config user.email` 获取）
- `tool`：工具名称（Write、Edit、NotebookEdit）
- `additions`：新增行数
- `deletions`：删除行数
- `net_change`：净变化（additions - deletions）

## 测试

运行测试脚本：

```bash
./.claude/hooks/stats-hooks/test_post_stat.sh
```

测试内容包括：
- Write 工具多行写入
- Edit 工具新增行
- Edit 工具删除行
- NotebookEdit 工具

检查 `stats.jsonl` 中的结果。

## 相比基于 Git 的方案的优势

### 并发安全
- ✅ 无竞态条件
- ✅ 每次 hook 调用独立
- ✅ 多个 agents 可同时工作
- ✅ 使用文件锁防止写入冲突

### 准确性
- ✅ 跟踪实际的工具操作
- ✅ 无累积状态问题
- ✅ 精确的行数统计

### 简洁性
- ✅ 单个 hook 文件
- ✅ 无需状态文件管理
- ✅ 无需前后 hook 协调

### 性能
- ✅ 不执行 git 命令
- ✅ 更快的 hook 执行
- ✅ 更低的系统开销

## 并发安全实现

### 文件锁机制

使用 `fcntl.flock` 确保并发写入安全：

```python
import fcntl

def append_to_stats(record):
    with open(STATS_FILE, 'a') as f:
        # 获取排他锁
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(json.dumps(record) + '\n')
            f.flush()  # 确保数据写入磁盘
        finally:
            # 释放锁
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

### 锁的特性

- **排他锁（LOCK_EX）**：同一时间只有一个进程能写入
- **阻塞式**：如果有其他进程持有锁，当前进程会等待
- **自动释放**：文件关闭时自动释放，即使程序崩溃也安全

## 故障排除

### 没有记录统计信息

检查：
1. Hook 是否可执行：`ls -l post_stat.py`
2. Hook 是否在 settings.local.json 中配置
3. stdin 数据是否可用：Hook 会将警告记录到 stderr

### 行数统计不正确

Hook 使用简单的换行符计数器：
- 空字符串 = 0 行
- 无尾随换行符的文本 = 行数 + 1
- 处理所有标准文本格式

### 调试模式

添加调试日志：

```python
# 在 read_hook_input() 中添加：
with open('/tmp/hook_debug.json', 'w') as f:
    json.dump(data, f, indent=2)
```

## 实现细节

### Git 用户邮箱

通过执行 `git config user.email` 获取当前用户的邮箱地址。如果未配置或获取失败，将使用 "unknown" 作为默认值。

### Session ID

从 stdin 数据中提取 session_id。如果未提供，hook 会使用当前时间戳生成一个。

### 行数统计逻辑

```python
def count_lines(text):
    if not text:
        return 0
    return text.count('\n') + (1 if text and not text.endswith('\n') else 0)
```

处理情况：
- 空文件：0 行
- 单行无换行符：1 行
- 多行：换行符数量 + 1（如果没有尾随换行符）

### 错误处理

Hook 永远不会阻塞工具执行：
- 捕获所有异常
- 错误记录到 stderr
- 始终以退出码 0 退出

## 从基于 Git 的 Hook 迁移

### 旧方案的问题
- 使用 git diff（累积状态）
- 需要 pre-hook + post-hook 协调
- 并发 agents 下存在竞态条件
- 状态文件管理复杂

### 迁移步骤
1. 从 settings 中移除 PreToolUse hook
2. 更新 PostToolUse hook 路径为 post_stat.py
3. 删除旧 hook 文件（pre_stat_git.py、post_stat_git.py）
4. 清理状态文件（.state.*.json）
5. 测试并发操作

## 文件说明

- `post_stat.py` - 主 hook 实现
- `view_stats.py` - 统计数据查看工具（推荐使用）
- `stats/` - 统计数据目录（按日期组织）
  - `YYYY-MM-DD.jsonl` - 每天的统计记录
- `test/` - 测试套件目录
  - `test_post_stat.py` - 主测试脚本
  - `test_hook_input.py` - Hook 输入调试工具
  - `run_tests.sh` - Unix/macOS 测试运行器
  - `run_tests.bat` - Windows 测试运行器
  - `README.md` - 测试文档
- `README.md` - 本文档

## 查看统计信息

### 使用统计查看工具（推荐）

我们提供了一个方便的 Python 工具来查看统计数据：

```bash
# 显示今天的统计摘要
python view_stats.py

# 或直接执行（Unix-like 系统）
./view_stats.py

# 显示指定日期的统计
python view_stats.py --date 2026-02-01

# 显示所有历史统计
python view_stats.py --history

# 显示最近 20 条记录
python view_stats.py --recent 20

# 列出所有可用的日期
python view_stats.py --list
```

**功能特性：**
- 📊 日期汇总：总操作数、新增/删除行数、净变化
- 👤 按用户统计：每个用户的代码变更量
- 🔧 按工具统计：各工具的使用频率
- 💬 按会话统计：每个会话的操作详情
- 📅 历史统计：所有历史数据的汇总
- 🕐 最近记录：查看最新的操作记录

### 使用命令行工具（高级）

### 查看今天的记录
```bash
# 获取今天的日期
TODAY=$(date +%Y-%m-%d)

# 查看今天的所有记录
cat .claude/hooks/stats-hooks/stats/$TODAY.jsonl | jq

# 查看今天的最近 10 条记录
tail -n 10 .claude/hooks/stats-hooks/stats/$TODAY.jsonl | jq
```

### 查看指定日期的记录
```bash
# 查看 2026-02-01 的记录
cat .claude/hooks/stats-hooks/stats/2026-02-01.jsonl | jq
```

### 查看所有历史记录
```bash
# 合并所有日期的记录
cat .claude/hooks/stats-hooks/stats/*.jsonl | jq
```

### 今日统计汇总
```bash
TODAY=$(date +%Y-%m-%d)
cat .claude/hooks/stats-hooks/stats/$TODAY.jsonl | jq -s '
  {
    date: "'$TODAY'",
    total_additions: map(.additions) | add,
    total_deletions: map(.deletions) | add,
    net_change: map(.net_change) | add,
    total_operations: length
  }
'
```

### 按会话聚合（今日）
```bash
TODAY=$(date +%Y-%m-%d)
cat .claude/hooks/stats-hooks/stats/$TODAY.jsonl | jq -s '
  group_by(.session_id) |
  map({
    session_id: .[0].session_id,
    total_additions: map(.additions) | add,
    total_deletions: map(.deletions) | add,
    total_net: map(.net_change) | add,
    operations: length
  })
'
```

### 按用户聚合（今日）
```bash
TODAY=$(date +%Y-%m-%d)
cat .claude/hooks/stats-hooks/stats/$TODAY.jsonl | jq -s '
  group_by(.email) |
  map({
    email: .[0].email,
    total_additions: map(.additions) | add,
    total_deletions: map(.deletions) | add,
    total_net: map(.net_change) | add,
    operations: length
  })
'
```

### 所有历史统计
```bash
cat .claude/hooks/stats-hooks/stats/*.jsonl | jq -s '
  {
    total_additions: map(.additions) | add,
    total_deletions: map(.deletions) | add,
    net_change: map(.net_change) | add,
    total_operations: length,
    date_range: {
      first: .[0].timestamp,
      last: .[-1].timestamp
    }
  }
'
```

### 按日期统计
```bash
# 列出每天的统计摘要
for file in .claude/hooks/stats-hooks/stats/*.jsonl; do
    date=$(basename "$file" .jsonl)
    stats=$(cat "$file" | jq -s '{
        additions: map(.additions) | add,
        deletions: map(.deletions) | add,
        net: map(.net_change) | add,
        ops: length
    }')
    echo "$date: $stats"
done
```

## 数据管理

### 查看数据大小

```bash
# 查看 stats 目录总大小
du -sh .claude/hooks/stats-hooks/stats

# 查看每个文件的大小
ls -lh .claude/hooks/stats-hooks/stats/
```

### 清理旧数据

```bash
# 删除 30 天前的数据
find .claude/hooks/stats-hooks/stats -name "*.jsonl" -mtime +30 -delete

# 删除指定日期的数据
rm .claude/hooks/stats-hooks/stats/2026-01-01.jsonl
```

### 备份数据

```bash
# 备份整个 stats 目录
tar -czf stats-backup-$(date +%Y%m%d).tar.gz .claude/hooks/stats-hooks/stats/

# 备份到其他位置
cp -r .claude/hooks/stats-hooks/stats/ ~/backups/claude-stats-$(date +%Y%m%d)/
```

### 合并数据

如果需要合并多天的数据：

```bash
# 合并所有数据到一个文件
cat .claude/hooks/stats-hooks/stats/*.jsonl > all-stats.jsonl

# 合并指定月份的数据
cat .claude/hooks/stats-hooks/stats/2026-02-*.jsonl > 2026-02-stats.jsonl
```

## 未来增强

可能的改进：
- 跟踪被修改的文件路径
- 支持更多工具类型
- 导出为其他格式（CSV、SQLite、Excel）
- 可视化统计报表和图表
- 自动生成周报/月报
- 数据自动归档和压缩

## 许可证

claude-stats 项目的一部分。
