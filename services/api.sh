#!/bin/bash

export CONDA_ENV_NAME="mineru"   # 指定要激活的虚拟环境名称
export FLASK_HOST=$(hostname -I | awk '{print $1}')    # 获取本机 IP 地址并在每个节点上设置
export FLASK_PORT=8082   # 设置端口
export LOG_FILE="./logs/api.log"  # 设置日志文件路径

# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 切换到项目根目录
cd "$SCRIPT_DIR/.." || exit

# 检查日志文件是否存在，不存在则创建
if [ ! -f "$LOG_FILE" ]; then
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


# 启动 Flask 应用
echo "Starting Flask application..." | tee -a "$LOG_FILE"
python3 api/api.py 2>&1 | tee -a "$LOG_FILE"