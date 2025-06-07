# Audits 智能图斑审核——使用 LLM、 PaddleX 和 MinerU 提取PDF及图像中的字段

## 项目介绍

利用 PaddleOCR 和 PaddleSeal 以及 MinerU 分别对 pdf 及图像完成文本字段提取及印章识别工作流。借助 vllm 部署的微调 QWen-VL 多模态模型对提取的字段进行比对，并以 json 格式输出结果，同时利用 mysql 数据库保存审核结果，通过 flask 开发了 api 接口，实现与政府相关系统的无缝对接，为政府的图斑审核工作提供智能化的辅助工具。

该智能体可用于完整的多文档字段提取工作，并且支持多模态的图像和文本识别工作流。

## 系统要求

- Python >= 3.10
- 至少一张 A800 NVIDIA GPU部署LLM和PaddleX + 一张4090 NVIDIA GPU部署MinerU(长期推理使用两张A100)
- 多个可转发Post的Linux内核的Docker容器
- CUDA + PyTorch
- 能够从Huggingface上下载模型权重
- 稳定的网络连接
- 高质量代理IP（重要）

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

响应地址 [http://localhost:30109/v1](http://localhost:30109/v1)

### PaddleX 环境安装

具体安装文档请参考 [install_paddlex](docs/install_paddlex.md)

```bash
./start_paddlex.sh
```

OCR 响应地址 [http://localhost:30104/ocr](http://localhost:30104/ocr)

seal 响应地址 [http://localhost:30105/seal](http://localhost:30105/seal)

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

## 配置说明

### 数据库配置说明

本项目包含两个主要数据库配置部分，分别位于 `config.yaml` 文件中的以下字段：

#### 1. 下载材料相关数据库配置 (`db_download_config`)
用于从源系统下载 PDF 和图像文件的数据库连接信息。

示例配置：

```yaml 
db_download_config: 
  user: 'your_username' # 数据库用户名 
  password: 'your_password' # 数据库密码 
  host: 'localhost' # 数据库主机地址 
  port: 1521 # 数据库端口（如 Oracle） 
  sid: 'orcl' # 数据库 SID（根据实际数据库调整）
```
> ⚠️ 注意：该数据库通常为 Oracle 或其他企业级数据库，请确保你的数据库支持长连接并已开放相应端口。

---

#### 2. 审核结果数据库配置 (`results_db_config`)
用于存储 OCR、VLM 和 LLM 提取结果的数据库配置。支持 SQLite（开发环境）和 MySQL（生产环境）两种类型。

示例配置：
```yaml
results_db_config:
  db_type: "mysql" # 可选值: sqlite, mysql 
  db_name: "./database/audit_results.db" # SQLite 数据库路径（若使用 SQLite） 
  host: "localhost" # MySQL 主机地址 
  port: 3306 # MySQL 端口 
  user: "root" # MySQL 用户名 
  password: "your_password" # MySQL 密码 
  database: "audit_results" # 目标数据库名称
```
> 推荐在生产环境中使用 MySQL，SQLite 仅适用于本地测试。

---

#### 3. 配置建议流程：

1. 复制 `config.yaml` 为 `config.local.yaml`（或 `.yaml.example`），作为本地配置模板。
2. 修改 `db_download_config` 和 `results_db_config` 中的数据库连接信息。
3. 在启动服务前确认数据库服务已运行，并且用户有相应权限。


### 模型配置

本项目使用多个模型完成 OCR、印章识别、文本理解与多模态内容提取任务。所有模型配置均在 `config.yaml` 文件中定义。

#### 1. OCR 模型配置 (`ocr_mineru_config`, `ocr_paddle_config`)
用于 PDF 和图像的文本提取。

- `ocr_mineru_config`: 使用 MinerU 框架 + DocLayout-YOLO 模型解析 PDF 布局。
  - `model`: 指定模型名称，如 `doclayout_yolo`
  - `device`: 指定推理设备，支持 `gpu:0` 或 `cpu`

- `ocr_paddle_config`: 使用 PaddleOCR 进行通用 OCR 处理。
  - `pipeline`: 管道类型，如 `OCR`
  - `device`: 推理设备，支持 GPU 或 CPU
  - `batch_size`: 批处理大小
  - `service_url`: 服务化部署地址（若为远程服务）

---

#### 2. 印章识别配置 (`seal_config`)
用于识别图像中的印章信息。

- `pipeline`: 指定为 [seal_recognition](./models/seal_recognition.py#L0-L0)
- `device`: 推理设备
- `batch_size`: 批量大小
- [service_url](./models/seal_recognition.py#L0-L0): 若为远程服务，指定其地址

---

#### 3. LLM / VLM 配置 ([llm_config](./api/api.py#L31-L31), `vlm_config`)
用于文本和图像内容的理解与字段提取。

- [llm_config](./api/api.py#L31-L31): 使用 QwQ-32B 模型进行文本理解
  - [model](./test/vlm_extraction.py#L0-L0): 模型名称
  - `model_dir`: 本地模型路径
  - [service_url](./models/seal_recognition.py#L0-L0): 若为远程 vLLM 服务
  - `temperature`, `top_p`, `max_tokens`: 生成参数

- `vlm_config`: 使用 Qwen2.5-VL-32B 多模态模型
  - [model](./test/vlm_extraction.py#L0-L0): 模型名称
  - [pdf_max_pages](./models/seal_recognition.py#L0-L0): 最大处理 PDF 页数（默认为 10）

    

## 使用方法

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

api 的响应地址为 [http://localhost:30108/api](http://localhost:30108/api)

### 启动程序

```bash
cd ../
./run.sh
```

## 项目结构
该框架包含以下模块：
<details>
  <summary>👉 点击查看</summary>

```text
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

</details>

## 开发计划
- [ ] 支持更多字段的提取审核
- [ ] 支持公网IP接口
- [ ] 支持更多模型

## 贡献
欢迎提交问题和代码改进。请确保遵循项目的代码风格和贡献指南。

## 许可证
本项目采用 [GNU 许可证](LICENSE)。



