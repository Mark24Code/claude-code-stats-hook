#!/usr/bin/env python3
"""
Claude Code Stats Hook 安装/更新脚本
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


class Installer:
    """安装器类"""

    REPO_URL = "https://github.com/Mark24Code/claude-code-stats-hook.git"
    DEFAULT_INSTALL_PATH = "~/.claude/hooks/claude-code-stats-hook"

    def __init__(self, custom_path=None):
        self.custom_path = custom_path
        self.install_path = None
        self.temp_dir = None

    def expand_path(self, path):
        """展开路径（~和环境变量）"""
        return Path(os.path.expanduser(os.path.expandvars(path))).resolve()

    def simplify_path(self, path):
        """简化路径显示（使用 ~ 代替家目录）"""
        try:
            home = Path.home()
            path = Path(path).resolve()
            if path.is_relative_to(home):
                return f"~/{path.relative_to(home)}"
        except (ValueError, RuntimeError):
            pass
        return str(path)

    def choose_install_path(self):
        """选择安装路径"""
        if self.custom_path:
            self.install_path = self.expand_path(self.custom_path)
            print(f"使用指定路径: {self.simplify_path(self.install_path)}")
            return

        claude_path = self.expand_path("~/.claude/hooks/claude-code-stats-hook")
        project_dir = Path.cwd()
        project_claude_path = project_dir / ".." / ".claude" / "hooks" / "claude-code-stats-hook"

        print("\n选择安装路径:")
        print(f"1. ~/.claude 目录 (推荐): {self.simplify_path(claude_path)}")
        print(f"2. 项目目录: {self.simplify_path(project_claude_path)}")
        print("3. 输入自定义路径")

        while True:
            choice = input("\n请选择 (1-3): ").strip()

            if choice == "1":
                self.install_path = claude_path
                break
            elif choice == "2":
                self.install_path = project_claude_path
                break
            elif choice == "3":
                custom = input("请输入安装路径（绝对路径）: ").strip()
                if custom:
                    self.install_path = self.expand_path(custom)
                    break
                print("路径不能为空，请重新选择")
            else:
                print("无效选择，请输入 1-3")

        print(f"\n将安装到: {self.simplify_path(self.install_path)}")

    def clone_repo(self):
        """在临时目录克隆仓库"""
        print("正在下载最新代码...", end=" ", flush=True)
        self.temp_dir = tempfile.mkdtemp(prefix="claude-stats-")

        try:
            subprocess.run(
                ["git", "clone", self.REPO_URL, self.temp_dir],
                check=True,
                capture_output=True,
                text=True
            )

            # 检查是否有 tags
            result = subprocess.run(
                ["git", "-C", self.temp_dir, "tag", "-l"],
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout.strip():
                # 获取最新 tag
                tag_result = subprocess.run(
                    ["git", "-C", self.temp_dir, "tag", "--sort=-v:refname"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                latest_tag = tag_result.stdout.strip().split('\n')[0]

                # Checkout 到最新 tag
                subprocess.run(
                    ["git", "-C", self.temp_dir, "checkout", latest_tag],
                    check=True,
                    capture_output=True
                )
                print(f"完成 ({latest_tag})")
            else:
                print("完成 (main)")

        except subprocess.CalledProcessError as e:
            print("失败")
            print(f"错误: 下载代码失败 - {e.stderr if e.stderr else str(e)}")
            self.cleanup()
            sys.exit(1)

    def copy_files(self):
        """复制文件到安装目录"""
        print("正在安装文件...", end=" ", flush=True)

        # 确保目标目录存在
        self.install_path.mkdir(parents=True, exist_ok=True)

        # 复制文件，排除 .git
        for item in Path(self.temp_dir).iterdir():
            if item.name in ['.git', '.gitignore', '__pycache__']:
                continue

            dest = self.install_path / item.name

            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        # 确保 code-log 目录存在
        log_dir = self.install_path / "code-log"
        log_dir.mkdir(exist_ok=True)

        print("完成")

    def set_permissions(self):
        """设置可执行权限（Unix/macOS）"""
        if os.name != 'posix':
            return

        scripts = ["post_stat.py", "view_stats.py"]

        for script in scripts:
            script_path = self.install_path / script
            if script_path.exists():
                script_path.chmod(0o755)

    def show_config_instruction(self):
        """显示配置说明"""
        print("\n" + "="*60)
        print("配置说明")
        print("="*60)

        # 从脚本当前目录读取示例配置
        script_dir = Path(__file__).parent
        example_path = script_dir / "example.settings.local.json"

        if not example_path.exists():
            print("警告: 找不到配置模板文件")
            return

        with open(example_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 更新 hook 命令路径为用户的安装路径
        hook_script = self.install_path / "post_stat.py"
        if "hooks" in config and "PostToolUse" in config["hooks"]:
            for hook in config["hooks"]["PostToolUse"]:
                if "command" in hook:
                    hook["command"] = self.simplify_path(hook_script)

        print("\n请在 .claude/settings.local.json 或 .claude/settings.json 中添加：")
        print("\n" + "-"*60)
        print(json.dumps(config, indent=2, ensure_ascii=False))
        print("-"*60)

        print(f"\nHook 脚本路径: {self.simplify_path(hook_script)}")

    def verify_installation(self):
        """验证安装"""
        print("\n" + "="*60)
        print("安装成功!")
        print("="*60)
        print(f"安装路径: {self.simplify_path(self.install_path)}")

        print("\n下一步:")
        print("1. 按照上方配置说明，将 Hook 添加到 .claude/settings.local.json")
        print(f"2. 使用 Claude Code 时会自动记录统计信息")
        print(f"3. 查看统计: python {self.simplify_path(self.install_path / 'view_stats.py')}")

        print("\n快捷命令:")
        print(f"  alias claude-stats='python {self.simplify_path(self.install_path / 'view_stats.py')}'")

        # 显示更新命令
        install_script = Path(__file__).resolve()
        print(f"  更新: python {self.simplify_path(install_script)} update")

    def cleanup(self):
        """清理临时文件"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def install(self):
        """执行安装"""
        try:
            self.choose_install_path()
            self.clone_repo()
            self.copy_files()
            self.set_permissions()
            self.show_config_instruction()
            self.verify_installation()
        finally:
            self.cleanup()

    def update(self):
        """执行更新"""
        # 检测安装
        if self.custom_path:
            install_path = self.expand_path(self.custom_path)
        else:
            install_path = self.expand_path(self.DEFAULT_INSTALL_PATH)

        if not install_path.exists():
            print(f"错误: 未找到安装，请先运行 install 命令")
            print(f"检查路径: {self.simplify_path(install_path)}")
            sys.exit(1)

        self.install_path = install_path
        print(f"更新路径: {self.simplify_path(self.install_path)}\n")

        try:
            # 备份数据
            log_dir = self.install_path / "code-log"
            backup_log_dir = None

            if log_dir.exists() and any(log_dir.iterdir()):
                print("正在备份数据...", end=" ", flush=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_log_dir = self.install_path / f"code-log.backup.{timestamp}"
                shutil.copytree(log_dir, backup_log_dir)
                print("完成")

            # 获取最新代码
            self.clone_repo()

            # 删除旧文件（保留 code-log 和配置）
            for item in self.install_path.iterdir():
                if item.name in ['code-log', 'settings.local.json']:
                    continue
                if item.name.startswith('code-log.backup.'):
                    continue

                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

            # 复制新文件
            self.copy_files()

            # 恢复数据（如果备份了）
            if backup_log_dir:
                if log_dir.exists():
                    shutil.rmtree(log_dir)
                shutil.copytree(backup_log_dir, log_dir)

            # 设置权限
            self.set_permissions()

            # 显示更新摘要
            print("\n" + "="*60)
            print("更新成功!")
            print("="*60)
            print(f"安装路径: {self.simplify_path(self.install_path)}")

            if backup_log_dir:
                print(f"数据备份: {self.simplify_path(backup_log_dir)}")

            print("\n注意: 配置文件未改动")

        finally:
            self.cleanup()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Claude Code Stats Hook 安装/更新脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 默认安装（交互式）
  python install.py

  # 明确指定安装命令
  python install.py install

  # 安装到指定路径
  python install.py install --path /custom/path

  # 更新已安装的版本
  python install.py update

  # 更新指定路径的安装
  python install.py update --path /custom/path
        """
    )

    parser.add_argument(
        'command',
        nargs='?',  # 可选参数
        default='install',  # 默认为 install
        choices=['install', 'update'],
        help='命令: install (安装，默认) 或 update (更新)'
    )

    parser.add_argument(
        '--path',
        help='自定义安装路径（可选）'
    )

    args = parser.parse_args()

    # 检查 git 是否可用
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 未找到 git 命令，请先安装 git")
        sys.exit(1)

    installer = Installer(custom_path=args.path)

    if args.command == 'install':
        installer.install()
    elif args.command == 'update':
        installer.update()


if __name__ == '__main__':
    main()
