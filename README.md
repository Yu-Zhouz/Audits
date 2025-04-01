

## 智能体框架
```
Audits
    ├── config/
    │   ├── config.yaml                # 配置文件，存储路径、参数等配置信息
    │   ├── ocr.json                   # llm需要的json模板
    │   ├── ocr_merge.json             # 多文件合并后的的json模板
    │   ├── seal.json                  # 印章识别的json模板
    │   └── llm_field.json             # llm返回的字段模板
    ├── data/
    │   ├── input/                     # 输入文件夹，存放待处理的 PDF 和图片文件
    │   ├── output/                    # 输出文件夹，存放 OCR、印章识别和审核结果
    │   │   ├── markdown/              # OCR 转换后的 Markdown 文件
    │   │   ├── json/                  # OCR 提取的 JSON 文件
    │   │   └── images/                # OCR 提取的图片
    │   └── models/                    # 模型文件夹，存放预训练模型权重
    ├── load_data/
    │   ├── download_data.py           # 下载数据脚本，用于从平台下载PDF和图片文件
    ├── models/
    │   ├── download.py                # 从平台下载佐证脚本
    │   ├── ocr_mineru.py              # OCR 处理脚本，调用 MinerU 框架
    │   ├── ocr_paddle.py              # OCR 处理脚本，调用 PaddleOCR 框架
    │   ├── seal_recognition.py        # 印章识别脚本，调用 PaddleX 框架
    │   ├── llm_extraction.py          # LLM 内容提取脚本，调用 vLLM 模型
    │   ├── field_verification.py      # 字段核对脚本，实现字段值核对逻辑
    │   └── main_workflow.py           # 主工作流脚本，整合以上模块
    ├── services/
    │   ├── start_paddlex.sh           # PaddleX 服务启动脚本
    │   ├── start_vllm.sh              # vLLM 服务启动脚本
    │   └── app.py                     # Flask 服务脚本，提供接口与平台交互
    ├── database/
    │   ├── db.py                      # 数据库连接脚本，用于连接数据库
    ├── api/
    │   ├── api.py                     # API 脚本，提供接口与平台交互
    ├── utils/
    │   └── utils.py                   # 工具函数
    ├── main.py                        # 主程序入口，用于启动服务
    ├── README.md                      # 项目说明文档
    │── requirements.txt               # 服务依赖文件
    ├── setup.sh                       # 环境搭建脚本，用于初始化虚拟环境和安装依赖
    └── run.sh                         # 启动脚本，用于启动服务
```

## 安装

```bash
pip install oracledb Flask
```



