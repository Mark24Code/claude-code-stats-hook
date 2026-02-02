# Claude Code Stats Hook 安装指南

本文档详细说明如何使用 `install.py` 脚本安装和更新 Claude Code Stats Hook。

## 目录

- [系统要求](#系统要求)
- [安装](#安装)
  - [交互式安装](#交互式安装)
  - [指定路径安装](#指定路径安装)
- [更新](#更新)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

## 系统要求

- Python 3.6+
- Git 命令行工具
- Unix/Linux/macOS 或 Windows 系统

## 安装

### 方法一：交互式安装（推荐）

1. **克隆仓库到本地**

```bash
git clone https://github.com/Mark24Code/claude-code-stats-hook.git
cd claude-code-stats-hook
```

2. **运行安装脚本**

```bash
# 默认执行 install 命令
python install.py
```

3. **选择安装路径**

脚本会提示你选择安装路径：

```
选择安装路径:
1. ~/.claude 目录 (推荐): ~/.claude/hooks/claude-code-stats-hook
2. 项目目录: /path/to/project/.claude/hooks/claude-code-stats-hook
3. 输入自定义路径

请选择 (1-3):
```

- **选项 1（推荐）**: 安装到用户目录 `~/.claude/hooks/claude-code-stats-hook`
- **选项 2**: 安装到项目目录 `${项目目录}/.claude/hooks/claude-code-stats-hook`
- **选项 3**: 输入自定义绝对路径

4. **配置 Claude Code**

脚本会显示需要添加的配置内容：

```
============================================================
配置说明
============================================================

请在 ~/.claude/settings.local.json 或 ~/.claude/settings.json 中添加以下配置：

------------------------------------------------------------
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
------------------------------------------------------------

提示: command 字段的完整路径为:
  /Users/username/.claude/hooks/claude-code-stats-hook/post_stat.py
```

**手动添加配置**：复制上述配置内容到你的 `~/.claude/settings.local.json` 或 `~/.claude/settings.json` 文件中。

5. **验证安装**

安装成功后会显示摘要：

```
============================================================
安装完成!
============================================================

安装路径: ~/.claude/hooks/claude-code-stats-hook

后续步骤:
1. 配置 Claude Code Hook（见上方配置说明）
2. 查看统计数据: python ~/.claude/hooks/claude-code-stats-hook/view_stats.py
3. 使用 Claude Code 时会自动记录统计信息

提示:
  - 你可以将 view_stats.py 添加为 alias 方便使用
    例如: alias claude-stats='python ~/.claude/hooks/claude-code-stats-hook/view_stats.py'

  - 更新命令: python ~/path/to/install.py update
```

### 方法二：指定路径安装

如果你想直接指定安装路径，可以使用 `--path` 参数：

```bash
# 安装到默认路径
python install.py install --path ~/.claude/hooks/claude-code-stats-hook

# 安装到自定义路径
python install.py install --path /path/to/custom/location
```

## 更新

当有新版本发布时，使用以下命令更新：

### 更新默认路径的安装

```bash
cd claude-code-stats-hook  # 进入仓库目录
python install.py update
```

### 更新指定路径的安装

```bash
python install.py update --path /path/to/your/installation
```

### 更新流程

更新时，脚本会：

1. **备份数据**：自动备份 `code-log/` 目录到 `code-log.backup.TIMESTAMP`
2. **下载最新代码**：从 GitHub 获取最新版本
3. **更新文件**：替换所有脚本文件，保留数据和配置
4. **恢复数据**：将备份的数据恢复到 `code-log/` 目录

更新完成后会显示摘要：

```
============================================================
更新完成!
============================================================

安装路径: ~/.claude/hooks/claude-code-stats-hook
数据备份: ~/.claude/hooks/claude-code-stats-hook/code-log.backup.20260202_153000

提示: 配置文件未改动，如需更新配置请手动修改 ~/.claude/settings.local.json
```

## 配置说明

### 手动配置

安装脚本会显示需要添加的配置内容，你需要**手动添加**到 Claude Code 的配置文件中。

**配置文件位置**（选择其一）：
- `~/.claude/settings.local.json` (推荐)
- `~/.claude/settings.json`

### 配置结构

需要添加的配置格式：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/absolute/path/to/post_stat.py"
          }
        ]
      }
    ]
  }
}
```

**重要说明**：
- `command` 字段使用**绝对路径**
- 安装脚本会根据你选择的安装路径计算出正确的路径
- 这是因为 Claude Code 的 PostToolUse hooks 执行时环境变量可能不可用

### 如何添加配置

1. **如果配置文件不存在**：直接创建并添加上述内容

2. **如果配置文件已存在**：
   - 打开配置文件
   - 如果没有 `hooks` 部分，添加整个配置
   - 如果已有 `hooks.PostToolUse`，在数组中添加新的 hook 对象

**示例 - 已有其他配置**：

```json
{
  "someOtherSetting": "value",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/username/.claude/hooks/claude-code-stats-hook/post_stat.py"
          }
        ]
      }
    ]
  }
}
```

### 编辑配置文件

```bash
# 使用你喜欢的编辑器
vim ~/.claude/settings.local.json
# 或
nano ~/.claude/settings.local.json
# 或
code ~/.claude/settings.local.json
```

## 常见问题

### Q1: 安装脚本提示 "未找到 git 命令"

**原因**：系统未安装 Git

**解决方法**：
- macOS: `brew install git`
- Ubuntu/Debian: `sudo apt-get install git`
- Windows: 从 https://git-scm.com/ 下载安装

### Q2: 如何手动配置？

**答**：安装脚本会显示需要添加的配置内容，手动编辑 `~/.claude/settings.local.json` 或 `~/.claude/settings.json`：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/your/installation/post_stat.py"
          }
        ]
      }
    ]
  }
}
```

使用安装脚本显示的**完整绝对路径**。

### Q3: 如何卸载？

**步骤**：

1. 删除安装目录：
```bash
rm -rf ~/.claude/hooks/claude-code-stats-hook
```

2. 从 `~/.claude/settings.local.json` 中移除 hook 配置

3. （可选）删除备份文件：
```bash
rm ~/.claude/settings.local.json.bak.*
```

### Q4: 更新后统计数据会丢失吗？

**答**：不会。更新脚本会：
- 自动备份 `code-log/` 目录
- 更新完成后恢复数据
- 保留所有历史统计记录

### Q5: 可以在多个位置安装吗？

**答**：技术上可以，但不推荐。建议：
- 使用一个标准位置（如默认路径）
- 所有项目共享同一个安装
- 这样可以集中管理统计数据

### Q6: Windows 系统如何使用？

**答**：Windows 用户使用相同的命令：

```bash
# PowerShell 或 CMD
python install.py install
python install.py update
```

脚本会自动处理路径差异。

### Q7: 安装后没有统计数据？

**检查清单**：

1. 确认配置文件正确：
```bash
cat ~/.claude/settings.local.json
```

2. 确认脚本有执行权限（Unix/macOS）：
```bash
ls -l ~/.claude/hooks/claude-code-stats-hook/post_stat.py
```

3. 手动测试 hook：
```bash
python ~/.claude/hooks/claude-code-stats-hook/test/test_post_stat.py
```

4. 查看 Claude Code 日志是否有错误信息

### Q8: 如何查看安装的版本？

**答**：检查 Git tag 或 commit：

```bash
cd ~/.claude/hooks/claude-code-stats-hook
git log -1 --oneline  # 如果目录包含 .git
```

或查看文件修改时间：

```bash
ls -l ~/.claude/hooks/claude-code-stats-hook/post_stat.py
```

## 获取帮助

使用 `--help` 查看完整帮助信息：

```bash
python install.py --help
```

输出：

```
usage: install.py [-h] [--path PATH] [{install,update}]

Claude Code Stats Hook 安装/更新脚本

positional arguments:
  {install,update}  命令: install (安装，默认) 或 update (更新)

options:
  -h, --help        show this help message and exit
  --path PATH       自定义安装路径（可选）

示例:
  # 默认安装（交互式）
  python install.py

  # 明确指定安装命令
  python install.py install

  # 安装到指定路径
  python install.py --path /custom/path

  # 更新已安装的版本
  python install.py update

  # 更新指定路径的安装
  python install.py update --path /custom/path
```

## 反馈与贡献

如果遇到问题或有改进建议，请访问：
https://github.com/Mark24Code/claude-code-stats-hook

## 相关文档

- [README.md](README.md) - 项目主文档
- [test/README.md](test/README.md) - 测试文档
