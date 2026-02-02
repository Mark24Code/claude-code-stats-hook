@echo off
REM Stats Hook 测试运行器（Windows 系统）

setlocal enabledelayedexpansion

echo ========================================
echo Stats Hook 测试运行器
echo ========================================
echo.

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "TEST_SCRIPT=%SCRIPT_DIR%test_post_stat.py"

REM 检查 Python 是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误：未找到 python
    echo 请安装 Python 3.6 或更高版本
    echo.
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 显示 Python 版本
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Python 版本: %PYTHON_VERSION%
echo.

REM 检查测试脚本是否存在
if not exist "%TEST_SCRIPT%" (
    echo 错误：找不到测试脚本: %TEST_SCRIPT%
    pause
    exit /b 1
)

REM 运行测试
echo 正在运行测试...
echo.

python "%TEST_SCRIPT%"
set EXIT_CODE=%errorlevel%

echo.

REM 根据退出码显示结果
if %EXIT_CODE% equ 0 (
    echo ========================================
    echo ✓ 所有测试通过！
    echo ========================================
) else (
    echo ========================================
    echo ✗ 测试失败 ^(退出码: %EXIT_CODE%^)
    echo ========================================
)

echo.
pause
exit /b %EXIT_CODE%
