#!/bin/bash

# 设置日志文件路径
LOG_FILE="./install_paddlex.log"

export PATH="/opt/conda/bin:$PATH"

# 指定虚拟环境名称
export CONDA_ENV_NAME="paddlex"

# 切换到工作目录
echo "切换到工作目录" | tee -a "$LOG_FILE"
# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )" | tee -a "$LOG_FILE"
cd "$SCRIPT_DIR/.." || exit | tee -a "$LOG_FILE"

# 检查日志文件是否存在，不存在则创建
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi

# 创建 Conda 虚拟环境
if conda env list | grep -qwE "^$CONDA_ENV_NAME\s+"; then
    echo "虚拟环境 '$CONDA_ENV_NAME' 已存在。" | tee -a "$LOG_FILE"
else
    echo "虚拟环境 '$CONDA_ENV_NAME' 不存在，开始创建..." | tee -a "$LOG_FILE"
    conda create -n "$CONDA_ENV_NAME" python=3.10 -y | tee -a "$LOG_FILE"
    if [ $? -eq 0 ]; then
        echo "虚拟环境 '$CONDA_ENV_NAME' 创建成功。" | tee -a "$LOG_FILE"
    else
        echo "虚拟环境 '$CONDA_ENV_NAME' 创建失败。" | tee -a "$LOG_FILE"
        exit 1
    fi
fi

# 激活conda环境
source /opt/conda/bin/activate $CONDA_ENV_NAME
if [ $? -ne 0 ]; then
    echo "激活 conda 环境失败: $CONDA_ENV_NAME" | tee -a "$LOG_FILE"
    exit 1
else
    echo "激活成功 conda 环境: $CONDA_ENV_NAME" | tee -a "$LOG_FILE"
fi

# 安装 paddlepaddle-gpu
echo "安装 paddlepaddle-gpu..." | tee -a "$LOG_FILE"
python -m pip install paddlepaddle-gpu==3.0.0b1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/ | tee -a "$LOG_FILE"

# 验证 PaddlePaddle 是否安装成功
echo "验证 PaddlePaddle 是否安装成功..." | tee -a "$LOG_FILE"
python -c "import paddle; paddle.utils.run_check()" | tee -a "$LOG_FILE"

# 安装 PaddleX
echo "拉取PaddleX镜像..." | tee -a "$LOG_FILE"
git clone https://github.com/PaddlePaddle/PaddleX.git | tee -a "$LOG_FILE"

# 切换目录
echo "切换目录..." | tee -a "$LOG_FILE"
cd PaddleX | tee -a "$LOG_FILE"

echo "安装PaddleX..." | tee -a "$LOG_FILE"
pip install -e . | tee -a "$LOG_FILE"

# 验证 PaddleX 是否安装成功
echo "验证 PaddleX 是否安装成功..." | tee -a "$LOG_FILE"
paddlex --version | tee -a "$LOG_FILE"

# 安装服务化部署插件
echo "安装服务化部署插件..." | tee -a "$LOG_FILE"
paddlex --install serving | tee -a "$LOG_FILE"

# 验证 PaddleX 是否安装成功
echo "验证服务化部署插件是否安装成功..." | tee -a "$LOG_FILE"
# paddlex --version | tee -a "$LOG_FILE"

echo "安装完成！" | tee -a "$LOG_FILE"
