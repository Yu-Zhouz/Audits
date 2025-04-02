#!/bin/bash

# [1] 确保使用空闲GPU（假设GPU 1可用）
export CUDA_VISIBLE_DEVICES=0
export PADDLEX_DEVICE=gpu:0  # 与CUDA_VISIBLE_DEVICES匹配 [[1]]

# [2] 显存优化配置（PaddlePaddle专用）
export FLAGS_allocator_strategy=auto_growth  # 按需分配显存 [[6]]
export FLAGS_eager_delete_tensor_gb=0.0      # 及时释放无用显存
export FLAGS_fraction_of_gpu_memory_to_use=0.8  # 限制显存使用上限

export CC=/usr/bin/gcc   # 设置 C 编译器路径
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libGLX.so.0 # 设置 LD_PRELOAD 环境变量以解决 libGLX.so.0 链接问题
export CONDA_ENV_NAME="paddlex"   # 指定要激活的虚拟环境名称
export MODEL_PATH=""   # 设置模型路径
export PADDLEX_HOST_IP=$(hostname -I | awk '{print $1}')    # 获取本机 IP 地址并在每个节点上设置
export OCR_PORT=8080   # 设置端口
export SEAL_PORT=8081
export LOG_FILE="../logs/paddlex.log"  # 设置日志文件路径

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

# 内存碎片化缓解
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

# 启动 PaddleX OCR 服务
paddlex --serve --pipeline OCR --device $PADDLEX_DEVICE --host $PADDLEX_HOST_IP --port $OCR_PORT 2>&1 | tee -a "$LOG_FILE" &
OCR_PID=$!

# 启动 PaddleX seal_recognition 服务
paddlex --serve --pipeline seal_recognition --device $PADDLEX_DEVICE --host $PADDLEX_HOST_IP --port $SEAL_PORT 2>&1 | tee -a "$LOG_FILE" &
SEAL_PID=$!

# 等待两个服务进程结束
wait $OCR_PID $SEAL_PID