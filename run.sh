#!/bin/bash

# 设置日志文件路径
export LOG_FILE="./logs/run.log"

# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 切换到项目根目录
cd "$SCRIPT_DIR" || exit

# 检查日志目录是否存在，不存在则创建
if [ ! -d "logs" ]; then
    mkdir -p logs
fi

# 检查日志文件是否存在，不存在则创建
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi

# 激活虚拟环境
source /opt/conda/bin/activate mineru
if [ $? -ne 0 ]; then
    echo "Failed to activate conda environment: mineru" | tee -a "$LOG_FILE"
    exit 1
else
    echo "Activated conda environment: mineru" | tee -a "$LOG_FILE"
fi

# 启动 PaddleX 服务
echo "Starting PaddleX service..." | tee -a "$LOG_FILE"
./services/start_paddlex.sh 2>&1 | tee -a "$LOG_FILE"

# 启动 vLLM 服务
echo "Starting vLLM service..." | tee -a "$LOG_FILE"
./services/start_vllm.sh 2>&1 | tee -a "$LOG_FILE"

# 启动 Flask 服务
echo "Starting Flask service..." | tee -a "$LOG_FILE"
python3 ./services/app.py 2>&1 | tee -a "$LOG_FILE"