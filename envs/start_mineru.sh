#!/bin/bash

# 设置日志文件路径
LOG_FILE="./install_mineru.log"

# 指定虚拟环境名称
export CONDA_ENV_NAME="mineru"

if [ -f "$LOG_FILE" ]; then
    > "$LOG_FILE"  # 清空文件内容
else
    touch "$LOG_FILE"  # 创建文件
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
        echo "模型下载脚本获取成功。" | tee -a "$LOG_FILE"
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

# 重新切换虚拟环境
echo "重新切换虚拟环境..." | tee -a "$LOG_FILE"
source /opt/conda/bin/activate $CONDA_ENV_NAME | tee -a "$LOG_FILE"
if [ $? -ne 0 ]; then
    echo "Failed to activate conda environment: $CONDA_ENV_NAME" | tee -a "$LOG_FILE"
    exit 1
else
    echo "Activated conda environment: $CONDA_ENV_NAME" | tee -a "$LOG_FILE"
fi

# 测试 CUDA 加速效果
echo "测试 CUDA..." | tee -a "$LOG_FILE"
wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/demo/small_ocr.pdf | tee -a "$LOG_FILE"
magic-pdf -p small_ocr.pdf -o ./output | tee -a "$LOG_FILE"

# 安装其它依赖文件
echo "安装其它依赖文件..." | tee -a "$LOG_FILE"
pip install -r envs/requirements.txt | tee -a "$LOG_FILE"

echo "安装完成！" | tee -a "$LOG_FILE"