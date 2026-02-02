# Stats Hook 测试套件

本目录包含 `post_stat.py` hook 的测试工具和测试用例。

## 文件说明

### test_post_stat.py
主测试脚本，用于验证 hook 的各种功能。

**功能特性：**
- ✅ 跨平台兼容（Windows、macOS、Linux）
- ✅ 彩色终端输出（Windows 下自动禁用）
- ✅ 全中文测试报告
- ✅ 自动验证统计记录
- ✅ 详细的错误信息

**测试覆盖：**
1. Write 工具 - 多行内容写入
2. Edit 工具 - 新增行
3. Edit 工具 - 删除行
4. NotebookEdit 工具 - Notebook 编辑
5. 无变更场景 - 验证跳过逻辑

### test_hook_input.py
Hook 输入检查工具，用于调试和查看 Claude Code 传递给 hook 的原始数据。

**功能：**
- 捕获所有 stdin 数据
- 解析 JSON 内容
- 显示环境变量
- 保存到 `hook_test_output.json` 文件

## 使用方法

### 运行完整测试套件

#### 使用 Python（推荐，跨平台）
```bash
# 在 test 目录下
python test_post_stat.py

# 或在任意目录
python .claude/hooks/stats-hooks/test/test_post_stat.py
```

#### 使用 chmod 添加执行权限（Unix-like 系统）
```bash
chmod +x test_post_stat.py
./test_post_stat.py
```

### 调试 Hook 输入

如果你想查看 Claude Code 传递给 hook 的原始数据：

```bash
# 手动测试
echo '{"session_id": "test", "tool_input": {"___TOOL_NAME___": "Write", "content": "test"}}' | python test_hook_input.py

# 查看输出
cat hook_test_output.json
```

或者将 `test_hook_input.py` 配置为 hook：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "/absolute/path/to/test/test_hook_input.py"
          }
        ]
      }
    ]
  }
}
```

## 测试输出示例

### 成功运行
```
============================================================
post_stat.py Hook 测试套件
============================================================

📁 Hook 脚本: /path/to/post_stat.py
📊 统计文件: /path/to/stats.jsonl
🕐 测试时间: 2026-02-02 15:30:00
📈 测试前记录数: 10

测试 1: Write 工具 - 写入 3 行内容
  标准错误输出:
[stats-hook] ==================== 开始执行 ====================
[stats-hook] 接收到工具调用：Write
[stats-hook] Session ID: test_1738483800
...
✓ Write 工具测试通过: 验证通过

测试 2: Edit 工具 - 新增 2 行
...

============================================================
测试总结
============================================================

📊 总测试数: 5
✓ 通过: 5
✗ 失败: 0

🎉 所有测试通过！
```

### 失败场景
```
测试 3: Edit 工具 - 删除 2 行
✗ Edit 删除行测试失败: 字段 'deletions' 不匹配: 期望 2, 实际 0

============================================================
测试总结
============================================================

📊 总测试数: 5
✓ 通过: 4
✗ 失败: 1

❌ 有 1 个测试失败
```

## 故障排除

### 测试找不到 post_stat.py

确保 `post_stat.py` 在正确的位置：
```
.claude/hooks/stats-hooks/
├── post_stat.py          ← 主 hook 脚本
├── stats.jsonl           ← 统计数据文件
└── test/                 ← 测试目录
    ├── test_post_stat.py
    └── test_hook_input.py
```

### 测试报告没有颜色（Windows）

这是正常的。测试脚本会自动检测 Windows 平台并禁用颜色输出。

### 权限错误

确保脚本有执行权限：
```bash
chmod +x test_post_stat.py
chmod +x test_hook_input.py
```

### Python 版本要求

需要 Python 3.6 或更高版本。检查版本：
```bash
python --version
```

## 持续集成

如果你想在 CI/CD 中运行测试：

```bash
# 在项目根目录
python .claude/hooks/stats-hooks/test/test_post_stat.py

# 检查退出码
if [ $? -eq 0 ]; then
    echo "测试通过"
else
    echo "测试失败"
    exit 1
fi
```

## 添加新测试

要添加新的测试用例，编辑 `test_post_stat.py`，参考现有测试的格式：

```python
# ========== 测试 N: 你的测试描述 ==========
print_test(N, "你的测试描述")

test_data = {
    "session_id": test_session_id,
    "tool_input": {
        "___TOOL_NAME___": "工具名称",
        # 其他参数...
    }
}

success, stdout, stderr = run_hook_test(test_data, "测试描述")

if success:
    # 验证结果...
    records = read_last_stats_records(1)
    if records:
        expected = {
            "tool": "工具名称",
            "additions": 期望值,
            "deletions": 期望值,
            "net_change": 期望值,
            "session_id": test_session_id
        }
        verify_success, verify_msg = verify_stats_record(records[0], expected)
        if verify_success:
            print_success(f"测试通过: {verify_msg}")
            tests_passed += 1
        else:
            print_error(f"测试失败: {verify_msg}")
            tests_failed += 1
```

## 清理测试数据

如果想清理测试产生的数据：

```bash
# 删除今天文件中的测试会话记录
TODAY=$(date +%Y-%m-%d)
grep -v "test_" ../stats/$TODAY.jsonl > ../stats/$TODAY.jsonl.tmp && mv ../stats/$TODAY.jsonl.tmp ../stats/$TODAY.jsonl

# 删除测试输出文件
rm -f hook_test_output.json
```

## 相关文档

- [主 README](../README.md) - Hook 的完整文档
- [post_stat.py](../post_stat.py) - Hook 主脚本

## 贡献

欢迎添加更多测试用例！请确保：
1. 测试用例有清晰的描述
2. 验证逻辑完整
3. 测试通过后再提交
4. 保持代码风格一致
