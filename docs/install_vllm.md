# vLLM 安装文档

## 一、vLLM 环境配置

在开始之前，请确保您已准备好以下物品：
- 基于 Linux 的操作系统（推荐 Ubuntu 20.04+）
- 已安装 - Python：3.9 – 3.12
- NVIDIA 驱动程序 525+、CUDA 11.8+（用于 CPU 加速）
- GPU：计算能力 7.0 或更高版本（例如 V100、T4、RTX20xx、A100、L4、H100 等）
### 1. 创建新的 Python 环境

```bash
conda create -n vllm python=3.12 -y
conda activate vllm
```

### 2. 安装 vllm

```bash
pip install vllm --pre --extra-index-url https://wheels.vllm.ai/nightly
```

如果需要安装最新版本，则需要拉取镜像重新编译

```bash
git clone https://github.com/vllm-project/vllm.git
cd vllm
VLLM_USE_PRECOMPILED=1 pip install --editable .  # 预编译安装
pip install -e . # 开发模式安装
```
### 3. 验证安装

### 3.1 检查安装路径

```bash
python3 -c "import vllm; print(vllm.__file__)"
```

如果输出显示了 vLLM 的安装路径，则说明 vLLM 已正确安装。

```bash
/opt/conda/envs/vllm/lib/python3.12/site-packages/vllm/__init__.py
```

#### 3.2 检查依赖

`vLLM` 依赖于多个库（如 `PyTorch`、`CUDA` 等）。确保这些依赖已正确安装：

```bash
python -c "import torch; import torchvision; print(f'Torch Version: {torch.__version__}, Torchvision Version: {torchvision.__version__}, CUDA Available: {torch.cuda.is_available()}, CUDA Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}, CUDA Version: {torch.version.cuda}')"
```

输出如下：

```bash
Torch Version: 2.5.1+cu124, Torchvision Version: 0.20.1+cu124, CUDA Available: True, CUDA Device: NVIDIA A800 80GB PCIe, CUDA Version: 12.4
```

#### 3.3 运行 vLLM 测试脚本

vLLM 提供了一些测试脚本，可以帮助验证安装是否成功。可以尝试运行以下命令：

```bash
python3 -m vllm.entrypoints.openai.api_server --help
```

如果输出显示了 vLLM 的命令行参数和帮助信息，则说明 vLLM 的入口脚本已正确加载。

## 二、Xinference 安装

### 1. 安装 Xinference

参考[安装 — Xinference](https://inference.readthedocs.io/zh-cn/latest/getting_started/installation.html#vllm-backend)，在vLLM 引擎上安装，可以用以下命令安装所有需要的依赖：

```bash
pip install "xinference[vllm]"  -i https://pypi.tuna.tsinghua.edu.cn/simple  
```

FlashInfer 是可选的，但对于特定功能（如 Gemma 2 的滑动窗口关注）是必需的。用于 CUDA 12.4 和 torch 2.4，以支持 gemma 2 和 llama 3.1 风格绳索的滑动窗口注意事项。对于其他 CUDA 和 torch 版本，请查看 [FlashInfer](https://docs.flashinfer.ai/installation.html)

```bash
pip install flashinfer -i https://flashinfer.ai/whl/cu124/torch2.4
```
### 2. 安装 sentence-transformers


```bash
pip install -U sentence-transformers
```

## 三、下载模型

接下来，我们需要下载 `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` 模型。
### 1.  安装 ModelScope 包

ModelScope 是一个模型中心，我们使用它来下载模型。在终端或命令提示符中执行以下命令安装

```bash
pip install modelscope
```

### 2. 下载模型

#### 2.1 LLM 模型下载

- **DeepSeek-R1:70B**

使用 `modelscope download` 命令下载模型[deepseek-ai/DeepSeek-R1-Distill-Llama-70B at main](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/tree/main)

```bash
modelscope download --model deepseek-ai/DeepSeek-R1-Distill-Llama-70B --local_dir /sxs/zhoufei/vLLM/models/deepseek-70b
```

其中，`--model deepseek-ai/DeepSeek-R1-Distill-Llama-70B`: 指定要下载的模型为 `deepseek-ai/DeepSeek-R1-Distill-Llama-70B`。
`--local_dir your_local_path`: 指定模型下载后保存的本地路径。请将 ` your_local_path` 替换为您电脑上实际想要保存模型的路径。例如，如果您想将模型保存在 `/home/user/models/deepseek-70b` 目录下。

- **DeepSeek-R1:32B**

```bash
modelscope download --model deepseek-ai/DeepSeek-R1-Distill-Qwen-32B --local_dir /sxs/zhoufei/vLLM/models/deepseek-32b
```

- **QwQ-32B**

```bash
modelscope download --model Qwen/QwQ-32B --local_dir /sxs/zhoufei/vLLM/models/QwQ-32B
```

#### 2.2 Embedding 模型下载

```bash
modelscope download --model BAAI/bge-m3 --local_dir /sxs/zhoufei/vLLM/models/bge-m3
```
#### 2.3 Rerank 模型下载

- **bge-reranker-v2-m3**
	- 优势：多语言支持能力强，推理速度快，适用于需要多语言和高效率的场景”。
	- 适用场景：适合需要快速部署和多语言支持的中文检索任务”。

```bash
modelscope download --model BAAI/bge-reranker-v2-m3 --local_dir /sxs/zhoufei/vLLM/models/bge-reranker-v2-m3
```

- **bce-reranker-base_v1** 
	- 优势：在 RAG 应用中表现优异，适合需要高精度检索的场景”。
	- 适用场景：更适合对检索精度要求较高的中文任务”。

```bash
modelscope download --model maidalun1020/bce-reranker-base_v1 --local_dir /sxs/zhoufei/vLLM/models/bce-reranker-base_v1
```

#### 2.4 VLM 模型下载

- **Qwen2.5-VL-7B-Instruct**
```bash
modelscope download --model Qwen/Qwen2.5-VL-7B-Instruct --local_dir /sxs/zhoufei/vLLM/models/Qwen2.5-VL-7B
```

- **Qwen2.5-VL-32B-Instruct**

```bash
modelscope download --model Qwen/Qwen2.5-VL-32B-Instruct --local_dir /sxs/zhoufei/vLLM/models/Qwen2.5-VL-32B
```
## 三、启动 vLLM 服务

```bash
#!/bin/bash

# 指定要激活的虚拟环境名称
export CONDA_ENV_NAME="vllm"

# 启用 vLLM 的 V1 版本
export VLLM_USE_V1=1

# 获取本机 IP 地址并在每个节点上设置
export VLLM_HOST_IP=$(hostname -I | awk '{print $1}')

# 设置端口
PORT=8000

# 设置模型路径
MODEL_PATH="/sxs/zhoufei/vLLM/models/deepseek-70b"

# 设置日志文件路径
LOG_FILE="./vLLM.log"

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

# 内存碎片化缓解
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

# 启动 vLLM 服务
python3 -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "deepseek-r1:70b" \
    --host "$VLLM_HOST_IP" \
    --port "$PORT" \
    --max-model-len 4096 \
    --dtype auto \
    --trust-remote-code \
    --gpu-memory-utilization 0.9 \
    --max-num-seqs 32 \
    --max-num-batched-tokens 2048 \
    2>&1 | tee -a "$LOG_FILE"
```

以下是根据你提供的命令参数整理的表格，展示了每个参数的作用、默认值（如果有）以及说明：

| 参数                         | 作用           | 默认值         | 说明                                                     |
| :------------------------- | :----------- | :---------- | :----------------------------------------------------- |
| `--model`                  | 模型路径或名称      | 无           | 指定加载的模型路径或 Hugging Face 模型名称。                          |
| `--served-model-name`      | 提供服务的模型名称    | 模型名称        | 指定通过 API 提供服务时的模型名称。                                   |
| `--host`                   | 服务主机地址       | `localhost` | 指定服务运行的主机地址。                                           |
| `--port`                   | 服务端口         | `8000`      | 指定服务运行的端口号。                                            |
| `--max-model-len`          | 最大上下文长度      | 自动从模型配置中获取  | 设置模型处理的最大上下文长度（单位：tokens）。                             |
| `--dtype`                  | 模型权重和激活的数据类型 | `auto`      | 指定模型权重和激活的数据类型，如 `auto`、`half`、`bfloat16`、`float16` 等。 |
| `--trust-remote-code`      | 允许加载远程代码     | `False`     | 允许加载来自 Hugging Face 的远程代码。                             |
| `--max-num-seqs`           | 每次迭代的最大序列数   | 无           | 设置每次迭代的最大序列数，用于控制推理时的批处理大小。                            |
| `--max-tokens`             | 最大输出长度       | 无           | 设置模型生成的最大输出长度（单位：tokens）。                              |
| `--gpu-memory-utilization` | 显存利用率        | 0.9         | 于控制 vLLM 在 GPU 上的显存利用率，其值范围为 0 到 1。                    |


> [!error] CUDA out of memory. 
> **问题描述**
> ```bash
> ERROR 03-04 07:29:31 engine.py:400] CUDA out of memory. Tried to allocate 1.96 GiB. GPU 0 has a total capacity of 79.15 GiB of which 353.75 MiB is free. Process 3449556 has 78.37 GiB memory in use. Process 2789996 has 414.00 MiB memory in use. Of the allocated memory 0 bytes is allocated by PyTorch, and 0 bytes is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)
> ```
> **解决方案**
> 出现上述问题，是因为显存不足，可通过下述命令，查看显存占用情况：
> ```bash
> nvidia-smi
> ```
> 监测显存变化
> ```bash
> watch -n 1 nvidia-smi
> ```


> [!error] Title
> **问题描述**
> ```bash
> RuntimeError: Failed to find C compiler. Please specify via CC environment variable.
> ```
> **解决方案**
> **Triton 编译器无法找到 C 编译器**，导致模型编译失败。
> 
> 1. **安装 C 编译器**
> 因此需要安装 GCC 和其他编译工具，可以通过以下命令安装：
> ```bash
> sudo apt update
> sudo apt install build-essential -y
> ```
> 2. **设置环境变量 `CC`**
> 终端输入
> 
> ```bash
> vim ~/.bashrc
> ```
> 
> 键入 “i” 进入 INSERT模式，可以进行回车操作，复制以下变量，键入“ESC”退出INSERT模式。
> 
> ```bash
> export CC=/usr/bin/gcc
> ```
> 
> 按 ESC 退出写入，最后键入:wq即可保存并退出。
> 
> 终端输入以下命令，使环境变量生效
> 
> ```bash
> source ~/.bashrc
> ```
> 3. **验证 Triton 编译器**
> 确保 Triton 编译器已正确安装。可以通过以下命令验证：
> ```bash
> python -c "import triton; print(triton.__version__)"
> ```
> 

服务启动成功后，在 Dify 中选择 `OpenAI-API-compatible` 模型供应商，其中 `API endpoint URL` 设置为：

```bash
http://172.16.15.10:30102/v1
```

## 四、启动Xinference 服务

```bash
#!/bin/bash

# 定义环境变量
export CONDA_ENV_NAME="vllm"  # 指定虚拟环境名称
export XINFERENCE_HOST_IP=$(hostname -I | awk '{print $1}')  # 自动获取本机 IP
export PORT=9997  # 服务端口
export LOG_FILE="./xinference.log"  # 日志文件路径

# 设置Xinference相关环境变量
export XINFERENCE_MODEL_SRC="modelscope"  # 指定模型源为ModelScope
export XINFERENCE_HOME="/sxs/zhoufei/vLLM/models"  # 指定模型缓存路径

# 激活虚拟环境
source /opt/conda/bin/activate $CONDA_ENV_NAME
if [ $? -ne 0 ]; then
    echo "Failed to activate conda environment: $CONDA_ENV_NAME" >> ./web.log
    exit 1
else
    echo "Activated conda environment: $CONDA_ENV_NAME" >> ./web.log
fi

# 检查日志文件是否存在，不存在则创建
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi

# 启动 Xinference 服务
echo "Starting Xinference service on $XINFERENCE_HOST_IP:$PORT with model path $MODEL_PATH" >> "$LOG_FILE"
xinference-local \
    --host "$XINFERENCE_HOST_IP" \
    --port "$PORT" \
    --log-level INFO \
    2>&1 | tee -a "$LOG_FILE"
```

服务启动成功后，访问[Xinference](http://172.16.15.10:30103/)：

```bash
http://172.16.15.10:30103/
```


### 参考文章
[GPU — vLLM](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/index.html)
[安装 | vLLM 中文站](https://vllm.hyper.ai/docs/getting-started/installation)
[DeepSeek 部署指南 (使用 vLLM 本地部署)_vllm部署deepseek-CSDN博客](https://blog.csdn.net/m0_48891301/article/details/145491228)
[使用vllm部署DeepSeek-R1-Distill-Qwen-1.5B-CSDN博客](https://blog.csdn.net/xuebodx0923/article/details/145420990)
[vllm 本地部署生产级DeepSeek R1 32B 模型实践_deepseek vllm本地模型运行-CSDN博客](https://blog.csdn.net/maskevinwu/article/details/145429022)
[vLLM部署Deepseek - R1 - 14B？看我超详细踩坑记录！ - 知乎](https://zhuanlan.zhihu.com/p/23933558453)
[vLLM 0.7.1 DeepSeek R1 PP 部署踩坑指南 - 知乎](https://zhuanlan.zhihu.com/p/21064432691)
[vLLM 部署 DeepSeek 大模型避坑指南_vllm部署deepseek整理-CSDN博客](https://blog.csdn.net/weixin_45631123/article/details/145669898)
[安装 — Xinference](https://inference.readthedocs.io/zh-cn/latest/getting_started/installation.html#vllm-backend)
[轻松部署Dify并实现Ollama与Xinference集成教程！_xinference ollama-CSDN博客](https://blog.csdn.net/Everly_/article/details/143289685)
[【4.8k Star Xinference部署】为知识库接入本地Rerank模型，全面提升检索效率_本地部署rerank模型-CSDN博客](https://blog.csdn.net/m0_63171455/article/details/144869092)
[【大模型】Xinference的安装和部署-CSDN博客](https://blog.csdn.net/magic_ll/article/details/144689516)
[Xinference 本地运行大模型_bge-reranker-v2-m3-CSDN博客](https://blog.csdn.net/liuqianglong_liu/article/details/142180111)
[一步到位！7大模型部署框架深度测评：从理论到DeepSeek R1:7B落地实战-CSDN博客](https://blog.csdn.net/zhangzhentiyes/article/details/145584861?ops_request_misc=&request_id=&biz_id=102&utm_term=%E4%B8%80%E6%AD%A5%E5%88%B0%E4%BD%8D%EF%BC%8C7%E5%A4%A7%E6%A8%A1%E5%9E%8B&utm_medium=distribute.pc_search_result.none-task-blog-2~all~sobaiduweb~default-0-145584861.nonecase&spm=1018.2226.3001.4187)
[vllm部署大模型的参数--dtype和量级AWQ有什么区别_vllm dtype-CSDN博客](https://blog.csdn.net/Gu_erye/article/details/141264059)
