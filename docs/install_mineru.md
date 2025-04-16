## MinerU 安装文档

为了确保项目的稳定性和可靠性，我们在开发过程中仅对特定的软硬件环境进行优化和测试。这样当用户在推荐的系统配置上部署和运行项目时，能够获得最佳的性能表现和最少的兼容性问题。

![[MinerU安装要求.png]]

这里我们以基础的 [[Linux服务器部署PaddleX实战教程]] 使用 Paddle-gpu环境为例
### 1. 创建 Conda 虚拟环境

需指定python版本为3.10

```bash
conda create -n mineru python=3.10 -y
conda activate mineru
```
### 2. 安装 magic-pdf

```bash
pip install -U magic-pdf[full] --extra-index-url https://wheels.myhloli.com -i https://mirrors.aliyun.com/pypi/simple
```

### 3 .验证安装

下载完成后，务必通过以下命令确认magic-pdf的版本是否正确

```bash
magic-pdf --version
```

输出如下：

```bash
Creating new Ultralytics Settings v0.0.6 file ✅ 
View Ultralytics Settings with 'yolo settings' or at '/root/.config/Ultralytics/settings.json'
Update Settings with 'yolo settings key=value', i.e. 'yolo settings runs_dir=path/to/dir'. For help see https://docs.ultralytics.com/quickstart/#ultralytics-settings.
import tensorrt_llm failed, if do not use tensorrt, ignore this message
import lmdeploy failed, if do not use lmdeploy, ignore this message
magic-pdf, version 1.2.2
```

如果版本号小于0.7.0，请到 [issue](https://github.com/opendatalab/MinerU/issues) 中反馈

### 4. 安装 paddlepaddle-gpu

#### 4.1 安装 paddlepaddle-gpu

版本参考[飞桨官网](https://www.paddlepaddle.org.cn/install/quick?docurl=/documentation./docs/zh/install/pip/linux-pip.html)，我们的 CUDA 版本为 12.2，<font color="#ff0000">这里需要注意 `paddlepaddle-gpu` 安装 `b1` 版本的，`b2` 版本与 `magic-pdf` 不兼容</font>，安装命令如下： 

```shell
python -m pip install paddlepaddle-gpu==3.0.0b1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

如果出现错误，大多数情况是网络不够稳定，因此，重新执行即可解决。若是版本问题则需要根据[飞桨官网](https://www.paddlepaddle.org.cn/install/quick?docurl=/documentation./docs/zh/install/pip/linux-pip.html)安装适配版本，目前官方已经支持国产芯片部署了。

#### 4.2 验证 PaddlePaddle 是否安装成功

使用以下命令可以验证 PaddlePaddle 是否安装成功。

```bash
python -c "import paddle; paddle.utils.run_check(); print(paddle.__version__)"
```

输出如下：

```
Running verify PaddlePaddle program ... 
I0309 12:29:41.671007  1301 program_interpreter.cc:243] New Executor is Running.
W0309 12:29:41.673063  1301 gpu_resources.cc:119] Please NOTE: device: 0, GPU Compute Capability: 8.0, Driver API Version: 12.2, Runtime API Version: 11.8
W0309 12:29:41.673806  1301 gpu_resources.cc:164] device: 0, cuDNN Version: 8.7.
I0309 12:29:42.088343  1301 interpreter_util.cc:648] Standalone Executor is Used.
PaddlePaddle works well on 1 GPU.
PaddlePaddle is installed successfully! Let's start deep learning with PaddlePaddle now.
3.0.0-beta1
```


> [!error] cv2 缺少 libGL.so.1 模块
> **问题描述**
> 
> >ImportError: libgomp.so.1: cannot open shared object file: No such file or directory
> 
> **解决方案**
> 
> [[cv2缺少libGL.so.1模块]]
> 
> ```bash
> apt-get install sudo
> sudo apt-get update 
> sudo apt-get install libglvnd-dev libgl1 -y
> ```

> [!error] Title
> 
> **问题描述**
> 
> >/opt/conda/envs/paddlex/lib/python 3.10/site-packages/paddle/utils/cpp_extension/extension_utils. Py:686: UserWarning: No ccache found. Please be aware that recompiling all source files may be required. You can download and install ccache from: https://github.com/ccache/ccache/blob/master/doc/INSTALL.md
> Warnings. Warn (warning_message)
> 
> **解决方案**
> 
> 这个警告信息来自于 PaddlePaddle（飞桨）框架，它提示您的系统中没有找到 `ccache`。`ccache` 是一个编译缓存工具，它可以加速 C/C++项目的重新编译过程，通过缓存之前的编译结果来避免重复编译相同的源文件。
> 
> ```shell
> (paddlex) python -c "import paddle; paddle. Utils. Run_check ()"
> Running verify PaddlePaddle program ... 
> I 1217 07:30:18.775925  1038 pir_interpreter. Cc: 1480] New Executor is Running ...
> W 1217 07:30:18.777175  1038 gpu_resources. Cc: 119] Please NOTE: device: 0, GPU Compute Capability: 8.0, Driver API Version: 12.2, Runtime API Version: 11.8
> W 1217 07:30:18.777792  1038 gpu_resources. Cc: 164] device: 0, cuDNN Version: 8.9.
> I 1217 07:30:19.045917  1038 pir_interpreter. Cc: 1506] pir interpreter is running by multi-thread mode ...
> PaddlePaddle works well on 1 GPU.
> PaddlePaddle is installed successfully! Let's start deep learning with PaddlePaddle now.
> ```

### 4 .模型下载

参考 [[HuggingFace模型下载指南]]中的下载方式，我们使用从 `ModelScope` 下载模型

#### 4.1 安装 ModelScope 包

ModelScope 是一个模型中心，我们使用它来下载模型。在终端或命令提示符中执行以下命令安装

```bash
pip install modelscope
```
#### 4.2 下载模型

```bash
wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/scripts/download_models.py -O download_models.py
python download_models.py
```

输出以下内容，则代表下载成功：

```bash
Downloading Model to directory: /root/.cache/modelscope/hub/models/opendatalab/PDF-Extract-Kit-1.0

model_dir is: /root/.cache/modelscope/hub/models/opendatalab/PDF-Extract-Kit-1___0/models
layoutreader_model_dir is: /root/.cache/modelscope/hub/models/ppaanngggg/layoutreader
The configuration file has been configured successfully, the path is: /root/magic-pdf.json
```

### 5. 配置文件存放的位置

完成下载模型步骤后，脚本会自动生成用户目录下的 `magic-pdf.json` 文件，并自动配置默认模型路径。您可在【用户目录】下找到magic-pdf.json文件。linux用户目录为 “/home/用户名”。

```bash
cat /root/magic-pdf.json
```

我们可以看到 `device-mode` 的值是 `cpu`，因此如果使用 `GPU` 加速的话，需要修改为 `cuda`
#### 5.1 修改配置文件

编辑配置文件内容，`i` 启动编辑

```bash
vim /root/magic-pdf.json
```

修改【用户目录】中配置文件 magic-pdf.json 中”device-mode”的值

```bash
{
  "device-mode":"cuda"
}
```

`ESC` 退出写入，`: wq` 退出保存文件。

#### 5.2 测试 CUDA

运行以下命令测试 cuda 加速效果

```bash
magic-pdf -p small_ocr.pdf -o ./output
```

CUDA 加速是否生效可以根据 log 中输出的各个阶段 cost 耗时来简单判断，通常情况下， `layout detection cost` 、 `mfr time` 和 `ocr cost` 应提速10倍以上。Log日志显示，已经修改为 `cuda`

```bash
2025-03-09 12:49:58.761 | INFO     | magic_pdf.model.pdf_extract_kit:__init__:92 - using device: cuda
```

### 6 .ssh 脚本安装

也可以直接创立下述 `install.sh` 自动化脚本安装：

```bash
#!/bin/bash

# 设置日志文件路径
LOG_FILE="./install.log"

# 指定虚拟环境名称
export CONDA_ENV_NAME="mineru"

# 检查日志文件是否存在，不存在则创建
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi

# 切换到工作目录
echo "切换到工作目录" | tee -a "$LOG_FILE"
cd /sxs/zhoufei/Audits | tee -a "$LOG_FILE"

# 创建 Conda 虚拟环境
echo "创建 Conda 虚拟环境..." | tee -a "$LOG_FILE"
conda create -n $CONDA_ENV_NAME  python=3.10 -y | tee -a "$LOG_FILE"

source /opt/conda/bin/activate $CONDA_ENV_NAME 
if [ $? -ne 0 ]; then
    echo "Failed to activate conda environment: $CONDA_ENV_NAME" | tee -a "$LOG_FILE"
    exit 1 
else 
    echo "Activated conda environment: $CONDA_ENV_NAME" | tee -a "$LOG_FILE"
fi

# 安装 magic-pdf
echo "安装 magic-pdf..." | tee -a "$LOG_FILE"
pip install -U magic-pdf[full] --extra-index-url https://wheels.myhloli.com -i https://mirrors.aliyun.com/pypi/simple | tee -a "$LOG_FILE"

# 验证 magic-pdf 安装
echo "验证 magic-pdf 安装..." | tee -a "$LOG_FILE"
magic-pdf --version | tee -a "$LOG_FILE"

# 安装 paddlepaddle-gpu
echo "安装 paddlepaddle-gpu..." | tee -a "$LOG_FILE"
python -m pip install paddlepaddle-gpu==3.0.0b1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/ | tee -a "$LOG_FILE"

# 验证 PaddlePaddle 是否安装成功
echo "验证 PaddlePaddle 是否安装成功..." | tee -a "$LOG_FILE"
python -c "import paddle; paddle.utils.run_check()" | tee -a "$LOG_FILE"

# 安装 ModelScope 包
echo "安装 ModelScope 包..." | tee -a "$LOG_FILE"
pip install modelscope | tee -a "$LOG_FILE"

# 下载模型
echo "尝试下载模型..." | tee -a "$LOG_FILE"
max_retries=5
retry_count=0
download_successful=false

while [ "$retry_count" -lt "$max_retries" ] && [ "$download_successful" = false ]; do
    wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/scripts/download_models.py -O download_models.py
    if [ $? -eq 0 ]; then
        echo "模型下载文件下载成功。" | tee -a "$LOG_FILE"
        download_successful=true
    else
        let retry_count++
        echo "下载失败，正在重试（$retry_count/$max_retries）..." | tee -a "$LOG_FILE"
        sleep 5  # 等待5秒后重试
        if [ $retry_count -eq $max_retries ]; then
            echo "达到最大重试次数，尝试ping网址测试连通性..." | tee -a "$LOG_FILE"
            ping -c 4 gcore.jsdelivr.net | tee -a "$LOG_FILE"
        fi
    fi
done

if [ "$download_successful" = false ]; then
    echo "模型下载失败，请检查网络连接或链接的有效性。" | tee -a "$LOG_FILE"
    exit 1
fi

# 运行下载脚本
echo "运行下载脚本..." | tee -a "$LOG_FILE"


python download_models.py | tee -a "$LOG_FILE"

# 配置文件存放的位置
echo "配置文件存放的位置..." | tee -a "$LOG_FILE"
cat /root/magic-pdf.json | tee -a "$LOG_FILE"

# 修改配置文件
echo "修改配置文件..." | tee -a "$LOG_FILE"
# 备份原始配置文件
cp /root/magic-pdf.json /root/magic-pdf.json.backup | tee -a "$LOG_FILE"

# 使用 sed 命令直接修改文件中的 device-mode 值为 cuda
sed -i 's/"device-mode": ".*"/"device-mode": "cuda"/' /root/magic-pdf.json | tee -a "$LOG_FILE"

# 检查配置文件是否修改成功
cat /root/magic-pdf.json | tee -a "$LOG_FILE"

# 测试 CUDA 加速效果
echo "测试 CUDA..." | tee -a "$LOG_FILE"
wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/demo/small_ocr.pdf | tee -a "$LOG_FILE"
magic-pdf -p small_ocr.pdf -o ./output | tee -a "$LOG_FILE"

echo "安装完成！" | tee -a "$LOG_FILE"
```

1. 赋予脚本执行权限：

```bash
chmod +x install.sh
```

2. 运行脚本：
```bash
./install.sh
```



### 参考文章

[MinerU/docs/README_Ubuntu_CUDA_Acceleration_zh_CN.md at master · opendatalab/MinerU](https://github.com/opendatalab/MinerU/blob/master/docs/README_Ubuntu_CUDA_Acceleration_zh_CN.md)
[使用 CUDA 加速 — MinerU 1.2.2 文档](https://mineru.readthedocs.io/zh-cn/latest/user_guide/install/boost_with_cuda.html)
[Mineru保姆级部署教程-CSDN博客](https://blog.csdn.net/2201_75283933/article/details/145907602)
[最新开源的解析效果非常好的PDF解析工具MinerU （pdf2md pdf2json）-CSDN博客](https://blog.csdn.net/star1210644725/article/details/140534238)
[国产PDF智能提取神器：MinerU功能全解析_mineru官方网站-CSDN博客](https://blog.csdn.net/weixin_43837507/article/details/145319903)
