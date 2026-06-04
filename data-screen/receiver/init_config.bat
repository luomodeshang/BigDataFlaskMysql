@echo off
chcp 65001 >nul
echo ========================================
echo 实时数据同步系统 - 配置初始化工具
echo ========================================
echo.

REM 获取本地IP地址
echo 正在查询本地IP地址...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set "local_ip=%%a"
    setlocal enabledelayedexpansion
    set "local_ip=!local_ip: =!"
    echo 找到IP地址: !local_ip!
    goto :ip_found
)
:ip_found

REM 如果没找到IP，使用127.0.0.1
if "%local_ip%"=="" (
    set "local_ip=127.0.0.1"
    echo 未找到IP地址，使用默认: %local_ip%
)

echo.
echo 请选择要配置的文件:
echo 1. 文件A (发送端 - sender.py)
echo 2. 文件B (接收端 - receiver.py)
echo.
set /p choice="请输入选择 (1 或 2): "

if "%choice%"=="1" goto config_a
if "%choice%"=="2" goto config_b
echo 无效选择，退出...
pause
exit /b

:config_a
echo.
echo ===== 配置文件A (发送端) =====
echo.
set /p db_server="请输入SQL Server服务器名 (例如: DESKTOP-XXX\SQLEXPRESS): "
set /p db_name="请输入数据库名 (默认: DataAnalysis): "
if "%db_name%"=="" set "db_name=DataAnalysis"
set /p table_name="请输入表名 (默认: BK_DataModel): "
if "%table_name%"=="" set "table_name=BK_DataModel"
echo.
set /p target_ip="请输入目标主机IP (接收端IP): "
set /p target_port="请输入目标端口 (默认: 8888): "
if "%target_port%"=="" set "target_port=8888"
set /p check_interval="请输入检查间隔(秒) (默认: 1): "
if "%check_interval%"=="" set "check_interval=1"

REM 创建config_A.json
echo.
echo 正在生成 config_A.json...
(
echo {
echo   "local_database": {
echo     "server": "%db_server%",
echo     "database": "%db_name%",
echo     "table_name": "%table_name%"
echo   },
echo   "target": {
echo     "host": "%target_ip%",
echo     "port": %target_port%
echo   },
echo   "sync": {
echo     "check_interval": %check_interval%,
echo     "timeout": 10
echo   }
echo }
) > config_A.json

echo ✓ 配置文件已生成: config_A.json
goto :end

:config_b
echo.
echo ===== 配置文件B (接收端) =====
echo.
echo 本地IP地址: %local_ip%
set /p listen_port="请输入监听端口 (默认: 8888): "
if "%listen_port%"=="" set "listen_port=8888"
echo.
echo MySQL数据库配置:
set /p mysql_host="请输入MySQL主机地址 (默认: localhost): "
if "%mysql_host%"=="" set "mysql_host=localhost"
set /p mysql_port="请输入MySQL端口 (默认: 3306): "
if "%mysql_port%"=="" set "mysql_port=3306"
set /p mysql_user="请输入MySQL用户名: "
set /p mysql_password="请输入MySQL密码: "
set /p mysql_database="请输入数据库名 (默认: DataAnalysis): "
if "%mysql_database%"=="" set "mysql_database=DataAnalysis"
set /p table_name="请输入表名 (默认: BK_DataModel): "
if "%table_name%"=="" set "table_name=BK_DataModel"

REM 创建config_B.json
echo.
echo 正在生成 config_B.json...
(
echo {
echo   "local_database": {
echo     "host": "%mysql_host%",
echo     "port": %mysql_port%,
echo     "user": "%mysql_user%",
echo     "password": "%mysql_password%",
echo     "database": "%mysql_database%",
echo     "table_name": "%table_name%"
echo   },
echo   "server": {
echo     "host": "0.0.0.0",
echo     "port": %listen_port%
echo   },
echo   "sync": {
echo     "timeout": 10
echo   }
echo }
) > config_B.json

echo ✓ 配置文件已生成: config_B.json
echo.
echo 提示: 接收端将自动检查并创建数据表（如果不存在）
goto :end

:end
echo.
echo ========================================
echo 配置完成！
echo ========================================
pause

