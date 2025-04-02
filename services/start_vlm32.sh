#!/bin/bash

export CUDA_VISIBLE_DEVICES=1   # 配置环境配置
export CC=/usr/bin/gcc   # 设置 C 编译器路径
export CONDA_ENV_NAME="vLLM"   # 指定要激活的虚拟环境名称
export VLLM_USE_V1=1   # 启用 vLLM 的 V1 版本
export MODEL_NAME="Qwen2.5-VL-32B" # 设置模型名称
export MODEL_PATH="/sxs/zhoufei/vLLM/models/Qwen2.5-VL-32B"   # 设置模型路径
export VLLM_HOST_IP=$(hostname -I | awk '{print $1}')    # 获取本机 IP 地址并在每个节点上设置
export PORT=8001   # 设置端口
export LOG_FILE="../logs/vlm_qwen2.5-vl-32b.log"  # 设置日志文件路径

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
echo "Starting vLLM service on host $VLLM_HOST_IP at port $PORT with model $MODEL_NAME" | tee -a "$LOG_FILE"
python3 -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "$MODEL_NAME" \
    --host "$VLLM_HOST_IP" \
    --port "$PORT" \
    --max-model-len 5120 \
    --limit-mm-per-prompt image=10 \
    --dtype float16 \
    --trust-remote-code \
    --gpu-memory-utilization 0.95 \
    --max-num-seqs 32 \
    --max-num-batched-tokens 2048 \
    2>&1 | tee -a "$LOG_FILE" &
PID=$!

# 检查服务是否成功启动
if [ $? -eq 0 ]; then
    echo "vLLM service started successfully with PID: $PID" | tee -a "$LOG_FILE"
else
    echo "Failed to start vLLM service" | tee -a "$LOG_FILE"
    exit 1
fi

# 保持脚本运行，直到服务被手动停止
wait $PID
echo "vLLM service stopped" | tee -a "$LOG_FILE"