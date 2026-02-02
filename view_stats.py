#!/usr/bin/env python3
"""
统计数据查看工具
提供便捷的方式查看和分析 stats hook 收集的数据。
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# 路径配置
SCRIPT_DIR = Path(__file__).resolve().parent
STATS_DIR = SCRIPT_DIR / "code-log"


def get_today_date():
    """获取今天的日期（东八区）"""
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz).date()


def list_available_dates():
    """列出所有可用的统计日期"""
    if not STATS_DIR.exists():
        return []

    dates = []
    for file in STATS_DIR.glob("*.jsonl"):
        try:
            date_str = file.stem  # 获取文件名（不含扩展名）
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            dates.append(date_str)
        except ValueError:
            continue

    return sorted(dates)


def read_stats_file(date_str):
    """读取指定日期的统计文件"""
    file_path = STATS_DIR / f"{date_str}.jsonl"

    if not file_path.exists():
        return []

    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    except Exception as e:
        print(f"错误：读取文件 {file_path} 失败 - {e}", file=sys.stderr)

    return records


def aggregate_by_date(date_str, records):
    """按日期聚合统计"""
    if not records:
        return None

    total_additions = sum(r['additions'] for r in records)
    total_deletions = sum(r['deletions'] for r in records)
    net_change = sum(r['net_change'] for r in records)

    return {
        'date': date_str,
        'total_additions': total_additions,
        'total_deletions': total_deletions,
        'net_change': net_change,
        'total_operations': len(records),
        'first_time': records[0]['timestamp'] if records else None,
        'last_time': records[-1]['timestamp'] if records else None
    }


def aggregate_by_user(records):
    """按用户聚合统计"""
    user_stats = defaultdict(lambda: {
        'additions': 0,
        'deletions': 0,
        'net_change': 0,
        'operations': 0
    })

    for record in records:
        email = record.get('email', 'unknown')
        user_stats[email]['additions'] += record['additions']
        user_stats[email]['deletions'] += record['deletions']
        user_stats[email]['net_change'] += record['net_change']
        user_stats[email]['operations'] += 1

    return dict(user_stats)


def aggregate_by_tool(records):
    """按工具聚合统计"""
    tool_stats = defaultdict(lambda: {
        'additions': 0,
        'deletions': 0,
        'net_change': 0,
        'operations': 0
    })

    for record in records:
        tool = record.get('tool', 'Unknown')
        tool_stats[tool]['additions'] += record['additions']
        tool_stats[tool]['deletions'] += record['deletions']
        tool_stats[tool]['net_change'] += record['net_change']
        tool_stats[tool]['operations'] += 1

    return dict(tool_stats)


def aggregate_by_session(records):
    """按会话聚合统计"""
    session_stats = defaultdict(lambda: {
        'additions': 0,
        'deletions': 0,
        'net_change': 0,
        'operations': 0,
        'tools': set()
    })

    for record in records:
        session_id = record.get('session_id', 'unknown')
        session_stats[session_id]['additions'] += record['additions']
        session_stats[session_id]['deletions'] += record['deletions']
        session_stats[session_id]['net_change'] += record['net_change']
        session_stats[session_id]['operations'] += 1
        session_stats[session_id]['tools'].add(record.get('tool', 'Unknown'))

    # 转换 set 为 list 以便 JSON 序列化
    result = {}
    for session_id, stats in session_stats.items():
        result[session_id] = {
            'additions': stats['additions'],
            'deletions': stats['deletions'],
            'net_change': stats['net_change'],
            'operations': stats['operations'],
            'tools': sorted(list(stats['tools']))
        }

    return result


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def show_summary(date_str=None):
    """显示摘要"""
    if date_str is None:
        date_str = get_today_date().strftime("%Y-%m-%d")

    print_header(f"📊 统计摘要 - {date_str}")

    records = read_stats_file(date_str)

    if not records:
        print(f"\n⚠️  {date_str} 没有统计记录")
        return

    # 日期汇总
    date_summary = aggregate_by_date(date_str, records)
    print(f"\n📅 日期：{date_summary['date']}")
    print(f"📈 总操作数：{date_summary['total_operations']}")
    print(f"➕ 新增行数：{date_summary['total_additions']}")
    print(f"➖ 删除行数：{date_summary['total_deletions']}")
    print(f"📊 净变化：{date_summary['net_change']:+d}")
    print(f"🕐 首次记录：{date_summary['first_time']}")
    print(f"🕐 最后记录：{date_summary['last_time']}")

    # 按用户统计
    user_stats = aggregate_by_user(records)
    if user_stats:
        print_header("👤 按用户统计")
        for email, stats in sorted(user_stats.items()):
            print(f"\n用户：{email}")
            print(f"  操作数：{stats['operations']}")
            print(f"  新增：+{stats['additions']} | 删除：-{stats['deletions']} | 净变化：{stats['net_change']:+d}")

    # 按工具统计
    tool_stats = aggregate_by_tool(records)
    if tool_stats:
        print_header("🔧 按工具统计")
        for tool, stats in sorted(tool_stats.items()):
            print(f"\n工具：{tool}")
            print(f"  使用次数：{stats['operations']}")
            print(f"  新增：+{stats['additions']} | 删除：-{stats['deletions']} | 净变化：{stats['net_change']:+d}")

    # 按会话统计
    session_stats = aggregate_by_session(records)
    if session_stats:
        print_header(f"💬 会话统计（共 {len(session_stats)} 个会话）")
        for session_id, stats in sorted(session_stats.items(), key=lambda x: x[1]['operations'], reverse=True)[:5]:
            print(f"\nSession：{session_id}")
            print(f"  操作数：{stats['operations']}")
            print(f"  工具：{', '.join(stats['tools'])}")
            print(f"  新增：+{stats['additions']} | 删除：-{stats['deletions']} | 净变化：{stats['net_change']:+d}")

        if len(session_stats) > 5:
            print(f"\n... 还有 {len(session_stats) - 5} 个会话")


def show_history():
    """显示历史统计"""
    print_header("📅 历史统计")

    dates = list_available_dates()

    if not dates:
        print("\n⚠️  没有找到任何统计记录")
        return

    print(f"\n找到 {len(dates)} 天的统计记录\n")

    total_additions = 0
    total_deletions = 0
    total_net = 0
    total_ops = 0

    for date_str in dates:
        records = read_stats_file(date_str)
        summary = aggregate_by_date(date_str, records)

        if summary:
            print(f"{date_str}: "
                  f"{summary['total_operations']:3d} 操作 | "
                  f"+{summary['total_additions']:5d} / -{summary['total_deletions']:5d} | "
                  f"净变化：{summary['net_change']:+6d}")

            total_additions += summary['total_additions']
            total_deletions += summary['total_deletions']
            total_net += summary['net_change']
            total_ops += summary['total_operations']

    print_header("📊 总计")
    print(f"\n总操作数：{total_ops}")
    print(f"总新增行：+{total_additions}")
    print(f"总删除行：-{total_deletions}")
    print(f"净变化：{total_net:+d}")
    print(f"日期范围：{dates[0]} 至 {dates[-1]}")


def show_recent(n=10):
    """显示最近的记录"""
    today = get_today_date().strftime("%Y-%m-%d")
    records = read_stats_file(today)

    print_header(f"🕐 最近 {n} 条记录 - {today}")

    if not records:
        print(f"\n⚠️  今天没有统计记录")
        return

    recent_records = records[-n:]

    print(f"\n显示 {len(recent_records)} 条记录：\n")

    for i, record in enumerate(recent_records, 1):
        timestamp = record.get('timestamp', 'N/A')
        tool = record.get('tool', 'Unknown')
        email = record.get('email', 'unknown')
        additions = record.get('additions', 0)
        deletions = record.get('deletions', 0)
        net = record.get('net_change', 0)

        print(f"{i:2d}. [{timestamp}] {tool:12s} | "
              f"{email:25s} | +{additions:3d}/-{deletions:3d} (净:{net:+4d})")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='统计数据查看工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s                    # 显示今天的统计摘要
  %(prog)s --date 2026-02-01  # 显示指定日期的统计
  %(prog)s --history          # 显示所有历史统计
  %(prog)s --recent 20        # 显示最近 20 条记录
  %(prog)s --list             # 列出所有可用的日期
        """
    )

    parser.add_argument('--date', '-d', help='指定日期（YYYY-MM-DD）')
    parser.add_argument('--history', '-H', action='store_true', help='显示历史统计')
    parser.add_argument('--recent', '-r', type=int, metavar='N', help='显示最近 N 条记录')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有可用的日期')

    args = parser.parse_args()

    # 检查 stats 目录是否存在
    if not STATS_DIR.exists():
        print(f"错误：统计目录不存在: {STATS_DIR}", file=sys.stderr)
        print(f"提示：请先使用 stats hook 生成一些统计数据", file=sys.stderr)
        sys.exit(1)

    if args.list:
        dates = list_available_dates()
        if dates:
            print("可用的统计日期：")
            for date in dates:
                print(f"  {date}")
        else:
            print("没有找到任何统计记录")

    elif args.history:
        show_history()

    elif args.recent:
        show_recent(args.recent)

    elif args.date:
        show_summary(args.date)

    else:
        # 默认显示今天的摘要
        show_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
