#!/bin/bash

export CUDA_VISIBLE_DEVICES=0   # 配置环境配置
export CC=/usr/bin/gcc   # 设置 C 编译器路径
export CONDA_ENV_NAME="vLLM"   # 指定要激活的虚拟环境名称
export VLLM_USE_V1=1   # 启用 vLLM 的 V1 版本
export MODEL_NAME="QwQ-32B" # 设置模型名称
export MODEL_PATH="/sxs/zhoufei/vLLM/models/QwQ-32B"   # 设置模型路径
export VLLM_HOST_IP=$(hostname -I | awk '{print $1}')    # 获取本机 IP 地址并在每个节点上设置
export PORT=8000   # 设置端口
export LOG_FILE="../logs/llm_qwq.log"  # 设置日志文件路径

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

# 启动 vLLM 服务
python3 -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "$MODEL_NAME" \
    --host "$VLLM_HOST_IP" \
    --port "$PORT" \
    --max-model-len 4096 \
    --dtype float16 \
    --trust-remote-code \
    --gpu-memory-utilization 0.9 \
    --max-num-seqs 32 \
    --max-num-batched-tokens 4096 \
    2>&1 | tee -a "$LOG_FILE" &
PID=$!