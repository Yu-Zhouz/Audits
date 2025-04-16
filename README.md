

## 智能体框架
```
Audits
    ├── config/
    │   ├── config.yaml                # 配置文件，存储路径、参数等配置信息
    ├── data/
    │   ├── data/                      # 存放待处理佐证材料，主要为 PDF 和图片文件
    │   ├── output/                    # 输出文件夹，存放 OCR、印章识别和审核结果
    │   │   ├── markdown/              # OCR 转换后的 Markdown 文件
    │   │   ├── json/                  # OCR 提取的 JSON 文件
    │   │   └── images/                # OCR 提取的图片
    │   └── models/                    # 模型文件夹，存放预训练模型权重
    ├── database/
    │   ├── db_downloader.py           # 单线程下载数据类，用于从平台下载PDF和图片文件
    │   ├── db_downloader_mt.py        # 多线程下载数据类，用于从平台下载PDF和图片文件
    │   ├── audit_results_my.py        # mysql 数据库结果操作类，用于将模型识别的字典结果储存到数据库与api查询结果
    │   ├── audit_results.py           # 数据库结果操作类，用于将模型识别的字典结果储存到数据库与api查询结果
    │   └── audit_results.db           # 数据库文件，用于存储模型识别的字典结果
    ├── models/
    │   ├── ocr_mineru.py              # OCR 处理脚本，调用 MinerU 框架
    │   ├── ocr_paddle.py              # OCR 处理脚本，调用 PaddleOCR 框架
    │   ├── seal_recognition.py        # 印章识别脚本，调用 PaddleX 框架
    │   ├── llm_extraction.py          # LLM 内容提取脚本，调用 QWQ-32b 模型
    │   └── vlm_extraction.py          # VLM 内容提取脚本，调用 QWen-VL-32b 模型
    ├── workflow/
    │   ├── workflow.py                # 工作流基类，用于执行智能体框架的各个步骤
    │   ├── workflow_mini.py           # 只使用VLM模型单条流
    │   ├── workflow_lite.py           # 使用VLM和MinerU和PaddleX文本处理双工作流
    │   ├── workflow_ultra.py          # 使用VLM和MinerU的多模态和MinerU文本的双工作流
    │   ├── workflow_pro.py            # 使用LLM和MinerU和PaddleX的图像和文本双工作流
    │   └── workflow_plus.py           # 使用VLM和MinerU的多模态和MinerU文本和PaddleOCR的三工作流
    ├── test/
    │   ├── db_download_id.py          # 单ID下载数据类，用于从平台下载PDF和图片文件
    │   └── vlm_extraction.py          # VLM 内容提取脚本，用于测试VLM模型
    ├── services/
    │   ├── start_llm.sh               # LLM 服务启动脚本
    │   ├── start_paddlex.sh           # PaddleX 服务启动脚本
    │   ├── start_vlm.sh               # vLM 服务启动 Qwen-vl-7b模型脚本
    │   ├── start_vlm32.sh             # VLM 服务启动 Qwen-vl-32b模型脚本
    │   └── app.sh                     # Flask 服务脚本，提供接口与平台交互
    ├── api/
    │   ├── api.py                     # API 脚本，提供接口与平台交互
    ├── utils/
    │   └── utils.py                   # 工具函数
    ├── envs/
    │   ├── start_vllm.sh              # VLLM 环境安装脚本
    │   ├── start_paddlex.sh           # PaddleX 环境安装脚本
    │   ├── start_mineru.sh            # MinerU 环境安装脚本
    │   └── start_mysql.sh             # mysql 环境安装脚本
    ├── docs/
    │   ├── api.md                     # API 文档
    │   ├── issues.md                  # 问题反馈文档
    │   ├── 
    ├── main.py                        # 主程序入口，用于启动服务
    ├── README.md                      # 项目说明文档
    │── requirements.txt               # 服务依赖文件
    ├── setup.sh                       # 环境搭建脚本，用于初始化虚拟环境和安装依赖
    └── run.sh                         # 启动脚本，用于启动服务
```

## 环境搭建

切换工作目录

```bash
cd envs
```

### VLLM 环境安装

具体安装文档请参考 [install_vllm](docs/install_vllm.md)

```bash
./start_vllm.sh
```

响应地址 [http://172.16.15.10:30109/v1](http://172.16.15.10:30109/v1)

### PaddleX 环境安装

具体安装文档请参考 [install_paddlex](docs/install_paddlex.md)

```bash
./start_paddlex.sh
```

OCR 响应地址 [http://172.16.15.10:30104/ocr](http://172.16.15.10:30104/ocr)

seal 响应地址 [http://172.16.15.10:30105/seal](http://172.16.15.10:30105/seal)

### MinerU 环境安装

具体安装文档请参考 [install_mineru](docs/install_mineru.md)
```bash
./start_mineru.sh
```

### mysql 环境安装

需要修改安装脚本 [start_mysql.sh](envs/start_mysql.sh) 中的参数，包括安装包路径等，安装文档请参考 [install_mysql](docs/install_mysql.md) 然后执行安装命令

```bash
./start_mysql.sh
```

## 启动服务

切换工作目录

```bash
cd services
```

### 启动vllm服务

```bash
./start_vllm32.sh
```

### 启动paddlex服务

```bash
./start_paddlex.sh
```

### 启动api服务

关于api接口的具体说明请参考 [api](docs/api.md)

```bash
./api.sh
```

api 的响应地址为 [http://172.16.15.10:30108/api](http://172.16.15.10:30108/api)

### 启动程序

```bash
cd ../
./run.sh
```







