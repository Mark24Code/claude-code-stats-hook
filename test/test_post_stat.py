#!/usr/bin/env python3
"""
post_stat.py 的测试脚本（跨平台兼容）
测试各种工具调用场景，验证统计功能是否正常工作。
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# 路径配置
TEST_DIR = Path(__file__).resolve().parent
HOOKS_DIR = TEST_DIR.parent
POST_STAT_SCRIPT = HOOKS_DIR / "post_stat.py"
STATS_DIR = HOOKS_DIR / "stats"  # 统计数据目录


def get_today_stats_file():
    """获取今天的统计文件路径"""
    from datetime import datetime, timezone, timedelta
    beijing_tz = timezone(timedelta(hours=8))
    today = datetime.now(beijing_tz).date()
    date_str = today.strftime("%Y-%m-%d")
    return STATS_DIR / f"{date_str}.jsonl"


class Color:
    """终端颜色（Windows 和 Unix 兼容）"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def disable():
        """禁用颜色（Windows 兼容性）"""
        Color.HEADER = ''
        Color.BLUE = ''
        Color.CYAN = ''
        Color.GREEN = ''
        Color.YELLOW = ''
        Color.RED = ''
        Color.RESET = ''
        Color.BOLD = ''


def print_header(text):
    """打印测试标题"""
    print(f"\n{Color.BOLD}{Color.BLUE}{'=' * 60}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{text}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{'=' * 60}{Color.RESET}\n")


def print_test(test_num, description):
    """打印测试用例信息"""
    print(f"{Color.CYAN}测试 {test_num}: {description}{Color.RESET}")


def print_success(message):
    """打印成功信息"""
    print(f"{Color.GREEN}✓ {message}{Color.RESET}")


def print_error(message):
    """打印错误信息"""
    print(f"{Color.RED}✗ {message}{Color.RESET}")


def run_hook_test(test_data, description):
    """
    运行单个 hook 测试。

    参数：
        test_data: 要发送给 hook 的 JSON 数据
        description: 测试描述

    返回：
        (success, stdout, stderr)
    """
    try:
        # 将测试数据转换为 JSON 字符串
        json_input = json.dumps(test_data, ensure_ascii=False)

        # 调用 post_stat.py，通过 stdin 传递数据
        result = subprocess.run(
            [sys.executable, str(POST_STAT_SCRIPT)],
            input=json_input,
            capture_output=True,
            text=True,
            timeout=5
        )

        return True, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "超时"
    except Exception as e:
        return False, "", str(e)


def read_last_stats_records(n=1):
    """读取最后 n 条统计记录"""
    try:
        if not get_today_stats_file().exists():
            return []

        with open(get_today_stats_file(), 'r', encoding='utf-8') as f:
            lines = f.readlines()
            records = []
            for line in lines[-n:]:
                if line.strip():
                    records.append(json.loads(line))
            return records
    except Exception as e:
        print_error(f"读取统计文件失败: {e}")
        return []


def verify_stats_record(record, expected):
    """
    验证统计记录是否符合预期。

    参数：
        record: 实际的统计记录
        expected: 期望的字段值

    返回：
        (success, message)
    """
    for key, value in expected.items():
        if key not in record:
            return False, f"缺少字段 '{key}'"
        if record[key] != value:
            return False, f"字段 '{key}' 不匹配: 期望 {value}, 实际 {record[key]}"
    return True, "验证通过"


def main():
    """主测试函数"""
    print_header("post_stat.py Hook 测试套件")

    # 检查平台，Windows 下禁用颜色
    import platform
    if platform.system() == 'Windows':
        Color.disable()

    # 检查脚本是否存在
    if not POST_STAT_SCRIPT.exists():
        print_error(f"错误：找不到 post_stat.py: {POST_STAT_SCRIPT}")
        sys.exit(1)

    print(f"📁 Hook 脚本: {POST_STAT_SCRIPT}")
    print(f"📊 统计文件: {get_today_stats_file()}")
    print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 记录测试前的统计记录数量
    initial_records = 0
    if get_today_stats_file().exists():
        with open(get_today_stats_file(), 'r', encoding='utf-8') as f:
            initial_records = sum(1 for line in f if line.strip())

    print(f"📈 测试前记录数: {initial_records}")

    test_session_id = f"test_{int(datetime.now().timestamp())}"
    tests_passed = 0
    tests_failed = 0

    # ========== 测试 1: Write 工具 - 多行内容 ==========
    print_test(1, "Write 工具 - 写入 3 行内容")

    test_data = {
        "session_id": test_session_id,
        "tool_input": {
            "___TOOL_NAME___": "Write",
            "content": "第一行\n第二行\n第三行"
        }
    }

    success, stdout, stderr = run_hook_test(test_data, "Write 工具测试")

    if success:
        print(f"  标准错误输出:\n{stderr}")

        # 验证统计记录
        records = read_last_stats_records(1)
        if records:
            expected = {
                "tool": "Write",
                "additions": 3,
                "deletions": 0,
                "net_change": 3,
                "session_id": test_session_id
            }
            verify_success, verify_msg = verify_stats_record(records[0], expected)
            if verify_success:
                print_success(f"Write 工具测试通过: {verify_msg}")
                tests_passed += 1
            else:
                print_error(f"Write 工具测试失败: {verify_msg}")
                tests_failed += 1
        else:
            print_error("未找到统计记录")
            tests_failed += 1
    else:
        print_error(f"执行失败: {stderr}")
        tests_failed += 1

    # ========== 测试 2: Edit 工具 - 新增行 ==========
    print_test(2, "Edit 工具 - 新增 2 行")

    test_data = {
        "session_id": test_session_id,
        "tool_input": {
            "___TOOL_NAME___": "Edit",
            "old_string": "旧内容",
            "new_string": "旧内容\n新增行 1\n新增行 2"
        }
    }

    success, stdout, stderr = run_hook_test(test_data, "Edit 新增行测试")

    if success:
        print(f"  标准错误输出:\n{stderr}")

        records = read_last_stats_records(1)
        if records:
            expected = {
                "tool": "Edit",
                "additions": 2,
                "deletions": 0,
                "net_change": 2,
                "session_id": test_session_id
            }
            verify_success, verify_msg = verify_stats_record(records[0], expected)
            if verify_success:
                print_success(f"Edit 新增行测试通过: {verify_msg}")
                tests_passed += 1
            else:
                print_error(f"Edit 新增行测试失败: {verify_msg}")
                tests_failed += 1
        else:
            print_error("未找到统计记录")
            tests_failed += 1
    else:
        print_error(f"执行失败: {stderr}")
        tests_failed += 1

    # ========== 测试 3: Edit 工具 - 删除行 ==========
    print_test(3, "Edit 工具 - 删除 2 行")

    test_data = {
        "session_id": test_session_id,
        "tool_input": {
            "___TOOL_NAME___": "Edit",
            "old_string": "第一行\n第二行\n第三行",
            "new_string": "第一行"
        }
    }

    success, stdout, stderr = run_hook_test(test_data, "Edit 删除行测试")

    if success:
        print(f"  标准错误输出:\n{stderr}")

        records = read_last_stats_records(1)
        if records:
            expected = {
                "tool": "Edit",
                "additions": 0,
                "deletions": 2,
                "net_change": -2,
                "session_id": test_session_id
            }
            verify_success, verify_msg = verify_stats_record(records[0], expected)
            if verify_success:
                print_success(f"Edit 删除行测试通过: {verify_msg}")
                tests_passed += 1
            else:
                print_error(f"Edit 删除行测试失败: {verify_msg}")
                tests_failed += 1
        else:
            print_error("未找到统计记录")
            tests_failed += 1
    else:
        print_error(f"执行失败: {stderr}")
        tests_failed += 1

    # ========== 测试 4: 无变更 - 应该跳过记录 ==========
    print_test(5, "无变更场景 - 应该跳过记录")

    test_data = {
        "session_id": test_session_id,
        "tool_input": {
            "___TOOL_NAME___": "Edit",
            "old_string": "相同内容",
            "new_string": "相同内容"
        }
    }

    records_before = initial_records + tests_passed

    success, stdout, stderr = run_hook_test(test_data, "无变更测试")

    if success:
        print(f"  标准错误输出:\n{stderr}")

        # 验证没有新增记录
        current_records = 0
        if get_today_stats_file().exists():
            with open(get_today_stats_file(), 'r', encoding='utf-8') as f:
                current_records = sum(1 for line in f if line.strip())

        if current_records == records_before:
            print_success("无变更测试通过: 正确跳过记录")
            tests_passed += 1
        else:
            print_error(f"无变更测试失败: 应该跳过记录，但记录数从 {records_before} 变为 {current_records}")
            tests_failed += 1
    else:
        print_error(f"执行失败: {stderr}")
        tests_failed += 1

    # ========== 测试总结 ==========
    print_header("测试总结")

    total_tests = tests_passed + tests_failed
    print(f"📊 总测试数: {total_tests}")
    print(f"{Color.GREEN}✓ 通过: {tests_passed}{Color.RESET}")
    print(f"{Color.RED}✗ 失败: {tests_failed}{Color.RESET}")

    if tests_failed == 0:
        print(f"\n{Color.GREEN}{Color.BOLD}🎉 所有测试通过！{Color.RESET}")

        # 显示最近的统计记录
        print_header("最近的统计记录")
        records = read_last_stats_records(4)
        for i, record in enumerate(records, 1):
            print(f"\n记录 {i}:")
            print(json.dumps(record, ensure_ascii=False, indent=2))

        return 0
    else:
        print(f"\n{Color.RED}{Color.BOLD}❌ 有 {tests_failed} 个测试失败{Color.RESET}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Color.YELLOW}测试被用户中断{Color.RESET}")
        sys.exit(130)
    except Exception as e:
        print_error(f"测试执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
