#!/bin/bash
# Stats Hook 测试运行器（Unix-like 系统）

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_SCRIPT="$SCRIPT_DIR/test_post_stat.py"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Stats Hook 测试运行器${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误：未找到 python3${NC}"
    echo "请安装 Python 3.6 或更高版本"
    exit 1
fi

# 显示 Python 版本
PYTHON_VERSION=$(python3 --version)
echo -e "${BLUE}Python 版本: ${NC}$PYTHON_VERSION"
echo ""

# 检查测试脚本是否存在
if [ ! -f "$TEST_SCRIPT" ]; then
    echo -e "${RED}错误：找不到测试脚本: $TEST_SCRIPT${NC}"
    exit 1
fi

# 运行测试
echo -e "${BLUE}正在运行测试...${NC}"
echo ""

python3 "$TEST_SCRIPT"
EXIT_CODE=$?

echo ""

# 根据退出码显示结果
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ 测试失败 (退出码: $EXIT_CODE)${NC}"
    echo -e "${RED}========================================${NC}"
fi

exit $EXIT_CODE
