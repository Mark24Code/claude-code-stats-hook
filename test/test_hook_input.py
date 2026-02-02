#!/usr/bin/env python3
"""
Hook 输入检查工具
用于检查 Claude Code 传递给 hook 的所有数据。
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 输出文件路径
OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = OUTPUT_DIR / 'hook_test_output.json'


def main():
    """主函数：收集并保存所有可用的 hook 数据"""
    print(f"[test-hook] ==================== Hook 输入检查 ====================", file=sys.stderr)

    # 收集数据
    data = {
        "timestamp": datetime.now().isoformat(),
        "script_path": str(Path(__file__).resolve()),
        "working_directory": os.getcwd(),
        "argv": sys.argv,
        "env": {},
        "stdin_available": not sys.stdin.isatty(),
        "stdin_content": None,
        "stdin_parsed": None
    }

    # 收集环境变量（只保留包含 'CLAUDE' 的）
    for key, value in os.environ.items():
        if 'CLAUDE' in key.upper():
            data["env"][key] = value

    print(f"[test-hook] 命令行参数: {data['argv']}", file=sys.stderr)
    print(f"[test-hook] 工作目录: {data['working_directory']}", file=sys.stderr)
    print(f"[test-hook] Claude 相关环境变量数量: {len(data['env'])}", file=sys.stderr)

    # 尝试读取 stdin
    if not sys.stdin.isatty():
        try:
            print(f"[test-hook] 正在读取 stdin 数据...", file=sys.stderr)
            stdin_data = sys.stdin.read()

            if stdin_data:
                data["stdin_content"] = stdin_data
                print(f"[test-hook] Stdin 数据长度: {len(stdin_data)} 字节", file=sys.stderr)

                # 尝试解析 JSON
                try:
                    parsed = json.loads(stdin_data)
                    data["stdin_parsed"] = parsed
                    print(f"[test-hook] ✓ Stdin JSON 解析成功", file=sys.stderr)

                    # 显示关键信息
                    if isinstance(parsed, dict):
                        if 'tool_input' in parsed:
                            tool_name = parsed['tool_input'].get('___TOOL_NAME___', 'Unknown')
                            print(f"[test-hook] 工具名称: {tool_name}", file=sys.stderr)
                        if 'session_id' in parsed:
                            print(f"[test-hook] Session ID: {parsed['session_id']}", file=sys.stderr)

                except json.JSONDecodeError as e:
                    print(f"[test-hook] ✗ Stdin JSON 解析失败: {e}", file=sys.stderr)
            else:
                print(f"[test-hook] 警告：Stdin 为空", file=sys.stderr)
        except Exception as e:
            print(f"[test-hook] 错误：读取 stdin 失败 - {e}", file=sys.stderr)
    else:
        print(f"[test-hook] 警告：Stdin 不可用（TTY）", file=sys.stderr)

    # 保存到文件
    try:
        # 确保输出目录存在
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[test-hook] ✓ 数据已保存到: {OUTPUT_FILE}", file=sys.stderr)

        # 显示文件大小
        file_size = OUTPUT_FILE.stat().st_size
        print(f"[test-hook] 输出文件大小: {file_size} 字节", file=sys.stderr)

    except Exception as e:
        print(f"[test-hook] 错误：保存文件失败 - {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    print(f"[test-hook] ==================== 检查完成 ====================", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[test-hook] 致命错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
