#!/usr/bin/env python3
"""
用于从工具参数跟踪代码变更的 Post-hook。
直接从 stdin 读取工具输入并计算统计信息。
无 git 依赖 - 支持并发 agents。
"""

import json
import sys
import time
import platform
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 根据平台导入相应的文件锁模块
PLATFORM = platform.system()
if PLATFORM == 'Windows':
    import msvcrt
else:
    import fcntl

# 路径配置（跨平台兼容）
SCRIPT_DIR = Path(__file__).resolve().parent
STATS_DIR = SCRIPT_DIR / "code-log"  # 统计数据目录

# Hook 名称（用于日志输出）
HOOK_NAME = "stats-hook"


def get_today_stats_file():
    """
    获取今天的统计文件路径。
    按日期组织：stats/YYYY-MM-DD.jsonl
    """
    today = datetime.now(timezone(timedelta(hours=8))).date()
    date_str = today.strftime("%Y-%m-%d")
    return STATS_DIR / f"{date_str}.jsonl"


def read_hook_input():
    """
    从 stdin 读取 Claude Code hook 输入。
    返回包含 tool_name、tool_input 和 session_id 的字典。
    """
    try:
        if sys.stdin.isatty():
            print(f"[{HOOK_NAME}] 警告：stdin 是 TTY，没有可用输入数据", file=sys.stderr)
            return None

        raw_data = sys.stdin.read()
        if not raw_data:
            print(f"[{HOOK_NAME}] 警告：stdin 为空，未接收到数据", file=sys.stderr)
            return None

        data = json.loads(raw_data)

        # 提取工具信息
        tool_input = data.get('tool_input', {})
        tool_name = tool_input.get('___TOOL_NAME___') or data.get('tool_name', 'Unknown')

        # 提取 session ID（如果没有则生成一个）
        session_id = data.get('session_id') or str(int(time.time()))

        print(f"[{HOOK_NAME}] 接收到工具调用：{tool_name}", file=sys.stderr)

        return {
            'tool_name': tool_name,
            'tool_input': tool_input,
            'session_id': session_id,
            'raw_data': data
        }
    except json.JSONDecodeError as e:
        print(f"[{HOOK_NAME}] 错误：解析 JSON 失败 - {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[{HOOK_NAME}] 错误：读取 hook 输入时出错 - {e}", file=sys.stderr)
        return None


def get_git_user_email():
    """
    获取当前 git 用户邮箱。
    如果未配置则返回 'unknown'。
    """
    try:
        result = subprocess.run(
            ['git', 'config', 'user.email'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            email = result.stdout.strip()
            print(f"[{HOOK_NAME}] Git 用户邮箱：{email}", file=sys.stderr)
            return email
        else:
            print(f"[{HOOK_NAME}] 警告：未配置 git 用户邮箱，使用默认值 'unknown'", file=sys.stderr)
    except Exception as e:
        print(f"[{HOOK_NAME}] 警告：获取 git 用户邮箱失败 - {e}", file=sys.stderr)
    return "unknown"


def count_lines(text):
    """
    统计文本字符串中的行数。
    空字符串 = 0 行，无换行符的非空字符串 = 1 行。
    """
    if not text:
        return 0
    # 统计换行符数量 + 1（如果最后一行没有换行符）
    return text.count('\n') + (1 if text and not text.endswith('\n') else 0)


def calculate_stats_from_tool_input(tool_name, tool_input):
    """
    直接从工具参数计算统计信息。

    返回：(additions, deletions, net_change)
    """
    if tool_name == 'Write':
        # Write 工具：统计新内容的行数
        content = tool_input.get('content', '')
        lines = count_lines(content)
        return lines, 0, lines

    elif tool_name == 'Edit':
        # Edit 工具：比较旧字符串和新字符串
        old_str = tool_input.get('old_string', '')
        new_str = tool_input.get('new_string', '')

        old_lines = count_lines(old_str)
        new_lines = count_lines(new_str)

        additions = max(0, new_lines - old_lines)
        deletions = max(0, old_lines - new_lines)
        net_change = new_lines - old_lines

        return additions, deletions, net_change

    elif tool_name == 'NotebookEdit':
        # NotebookEdit 工具：统计新源代码的行数
        new_source = tool_input.get('new_source', '')
        lines = count_lines(new_source)
        # 简单起见，视为新增（可以后续优化）
        return lines, 0, lines

    return 0, 0, 0


def lock_file(file_obj):
    """
    跨平台文件锁定（排他锁）。
    Windows 使用 msvcrt，Unix-like 系统使用 fcntl。
    """
    if PLATFORM == 'Windows':
        # Windows 平台：使用 msvcrt.locking
        # 锁定从当前位置开始的 1 字节（对于追加模式足够）
        # LK_LOCK 会阻塞直到获得锁
        file_obj.seek(0, 2)  # 移动到文件末尾
        try:
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
        except OSError:
            # 如果锁定失败，等待一小段时间后重试
            time.sleep(0.01)
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
    else:
        # Unix-like 平台：使用 fcntl.flock
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)


def unlock_file(file_obj):
    """
    跨平台文件解锁。
    Windows 使用 msvcrt，Unix-like 系统使用 fcntl。
    """
    if PLATFORM == 'Windows':
        # Windows 平台：使用 msvcrt.locking
        # 解锁之前锁定的 1 字节
        try:
            file_obj.seek(0, 2)  # 移动到文件末尾
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            # 忽略解锁错误（文件关闭时会自动解锁）
            pass
    else:
        # Unix-like 平台：使用 fcntl.flock
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)


def append_to_stats(record):
    """
    追加记录到今天的统计文件，使用文件锁保证并发安全。
    支持 Windows 和 Unix-like 系统。
    统计文件按日期组织：stats/YYYY-MM-DD.jsonl
    """
    try:
        # 获取今天的统计文件路径
        stats_file = get_today_stats_file()

        # 确保统计目录存在
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        print(f"[{HOOK_NAME}] 正在写入统计文件：{stats_file}", file=sys.stderr)

        with open(stats_file, 'a', encoding='utf-8') as f:
            # 获取排他锁以防止并发写入冲突
            lock_file(f)
            try:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                f.flush()  # 确保数据写入磁盘
                print(f"[{HOOK_NAME}] 统计记录写入成功", file=sys.stderr)
            finally:
                # 释放锁（文件关闭时会自动释放，但显式释放更清晰）
                unlock_file(f)
    except Exception as e:
        print(f"[{HOOK_NAME}] 错误：写入统计文件失败 - {e}", file=sys.stderr)
        raise


def main():
    """主执行函数。"""
    print(f"[{HOOK_NAME}] ==================== 开始执行 ====================", file=sys.stderr)

    # 从 stdin 读取 hook 输入
    hook_input = read_hook_input()

    if not hook_input:
        print(f"[{HOOK_NAME}] 无有效 hook 输入，跳过统计", file=sys.stderr)
        sys.exit(0)

    tool_name = hook_input['tool_name']
    tool_input = hook_input['tool_input']
    session_id = hook_input['session_id']

    print(f"[{HOOK_NAME}] Session ID: {session_id}", file=sys.stderr)

    # 计算统计信息
    additions, deletions, net_change = calculate_stats_from_tool_input(tool_name, tool_input)

    # 仅在有实际变更时记录
    if additions == 0 and deletions == 0:
        print(f"[{HOOK_NAME}] {tool_name} 工具：未检测到代码变更，跳过记录", file=sys.stderr)
        sys.exit(0)

    print(f"[{HOOK_NAME}] 检测到代码变更：+{additions} 行，-{deletions} 行，净变化 {net_change:+d} 行", file=sys.stderr)

    # 创建记录，使用东八区（北京时间）时间戳
    beijing_tz = timezone(timedelta(hours=8))
    record = {
        "timestamp": datetime.now(beijing_tz).isoformat(),
        "session_id": session_id,
        "email": get_git_user_email(),
        "tool": tool_name,
        "additions": additions,
        "deletions": deletions,
        "net_change": net_change
    }

    # 追加到统计文件
    append_to_stats(record)

    print(f"[{HOOK_NAME}] ✓ {tool_name} 工具统计完成：+{additions}/-{deletions} (净变化：{net_change:+d})", file=sys.stderr)
    print(f"[{HOOK_NAME}] ==================== 执行完成 ====================", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[{HOOK_NAME}] ==================== 执行失败 ====================", file=sys.stderr)
        print(f"[{HOOK_NAME}] 错误：Hook 执行出错 - {e}", file=sys.stderr)
        import traceback
        print(f"[{HOOK_NAME}] 错误堆栈：", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(f"[{HOOK_NAME}] 注意：错误不会阻塞工具执行", file=sys.stderr)
        sys.exit(0)  # 出错时不阻塞工具执行
