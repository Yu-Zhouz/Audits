#!/bin/bash

# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 切换到项目根目录
cd "$SCRIPT_DIR" || exit

# 激活虚拟环境
source /opt/conda/bin/activate mineru
if [ $? -ne 0 ]; then
    echo "Failed to activate conda environment: mineru"
    exit 1
else
    echo "Activated conda environment: mineru"
fi

while true; do
    # 运行你的Python程序
    python3 main.py
    sleep 1
    # 如果Python程序退出，则重新启动
    if [ $? -ne 0 ]; then
        echo "Python program exited with error. Restarting..."
    else
        echo "Python program exited normally. Exiting loop."
        break
    fi
done