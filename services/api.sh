#!/bin/bash

export CONDA_ENV_NAME="mineru"   # 指定要激活的虚拟环境名称
export FLASK_HOST=$(hostname -I | awk '{print $1}')    # 获取本机 IP 地址并在每个节点上设置
export FLASK_PORT=8082   # 设置端口
export LOG_FILE="./logs/api.log"  # 设置日志文件路径

# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 切换到项目根目录
cd "$SCRIPT_DIR/.." || exit

# 检查日志文件是否存在
if [ -f "$LOG_FILE" ]; then
    # 清空日志文件
    echo -n "" > "$LOG_FILE"
else
    # 创建日志文件
    touch "$LOG_FILE"
fi

# 激活指定的虚拟环境
source /opt/conda/bin/activate $CONDA_ENV_NAME
if [ $? -ne 0 ]; then
    echo "Failed to activate conda environment: $CONDA_ENV_NAME" | tee -a "$LOG_FILE"
    exit 1
else
    echo "Activated conda environment: $CONDA_ENV_NAME" | tee -a "$LOG_FILE"
fi


# 使用 nohup 启动 Flask 应用，并将日志同时输出到终端和文件
echo "Starting Flask application with nohup..." | tee -a "$LOG_FILE"
nohup python3 api/api.py 2>&1 | tee -a "$LOG_FILE" &

# 获取 nohup 启动的进程 ID
PID=$!

echo "Flask application started with PID: $PID" | tee -a "$LOG_FILE"

# 捕获 SIGINT (Ctrl+C) 和 SIGTERM 信号
trap 'echo "Received termination signal. Terminating Flask application..." | tee -a "$LOG_FILE"; kill -TERM $PID 2>/dev/null; exit' SIGINT SIGTERM

# 保持脚本运行，直到收到终止信号
wait $PID