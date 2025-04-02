# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: ocr_mineru.py
@Time    : 2025/3/12 上午10:10
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 使用 MinerU 框架将 PDF 或图像文件转换为 Markdown 和 JSON 格式
@Usage   : https://mineru.readthedocs.io/en/latest/user_guide/usage/api.html
"""
import logging
import os
import json
import sys

from magic_pdf.config.enums import SupportedPdfParseMethod
from magic_pdf.data.data_reader_writer import FileBasedDataReader, FileBasedDataWriter
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.data.read_api import read_local_images
from loguru import logger

logger.remove(0)  # 移除默认的日志处理器
logger.add(sys.stderr, level="CRITICAL")  # 只输出 CRITICAL 级别的日志

class MinerUOCR:
    def __init__(self, config):
        """
        初始化 OCR 处理器。
        :param output_dir: 输出目录
        :param delete_files: 是否删除处理后的文件以释放空间
        """
        self.config = config.get("ocr_mineru_config", {})
        self.output_dir = os.path.join(config.get("data_config", {}).get("output_dir"), "miner")
        self.image_dir = os.path.join(self.output_dir, "images")
        self.delete_files = config.get("data_config", {}).get("delete_files")
        self._prepare_directories()
        self._initialize_readers_writers()
        # logging.info(f"OCR 处理器已初始化，输出目录为 {self.output_dir}")

    def _prepare_directories(self):
        """创建必要的输出目录"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

    def _initialize_readers_writers(self):
        """初始化读写器"""
        self.reader = FileBasedDataReader("")
        self.image_writer = FileBasedDataWriter(self.image_dir)
        self.md_writer = FileBasedDataWriter(self.output_dir)

    def _process_pdf(self, pdf_file_path):
        """处理 PDF 文件并提取内容"""
        pdf_bytes = self.reader.read(pdf_file_path)
        ds = PymuDocDataset(pdf_bytes)
        if ds.classify() == SupportedPdfParseMethod.OCR:
            infer_result = ds.apply(doc_analyze, ocr=True)
            pipe_result = infer_result.pipe_ocr_mode(self.image_writer)
        else:
            infer_result = ds.apply(doc_analyze, ocr=False)
            pipe_result = infer_result.pipe_txt_mode(self.image_writer)

        # 删除生成的文件，释放空间
        if os.path.exists(self.image_dir):
            for file in os.listdir(self.image_dir):
                os.remove(os.path.join(self.image_dir, file))

        return pipe_result

    def _process_image(self, image_file_path):
        """处理图像文件并提取内容"""
        ds = read_local_images(image_file_path)[0]
        infer_result = ds.apply(doc_analyze, ocr=True)
        pipe_result = infer_result.pipe_ocr_mode(self.image_writer)

        # 删除生成的文件，释放空间
        if os.path.exists(self.image_dir):
            for file in os.listdir(self.image_dir):
                os.remove(os.path.join(self.image_dir, file))

        return pipe_result

    def _save_files(self, pipe_result, name_without_suff):
        """保存 Markdown 和 JSON 文件"""
        md_file_path = os.path.join(self.output_dir, f"{name_without_suff}.md")
        json_file_path = os.path.join(self.output_dir, f"{name_without_suff}.json")
        pipe_result.dump_md(self.md_writer, f"{name_without_suff}.md", "images")
        pipe_result.dump_content_list(self.md_writer, f"{name_without_suff}.json", "images")

        # 读取文件内容
        with open(md_file_path, "r", encoding="utf-8") as md_file:
            md_content = md_file.read()

        with open(json_file_path, "r", encoding="utf-8") as json_file:
            json_content = json.load(json_file)

        # 删除文件
        if self.delete_files:
            if os.path.exists(md_file_path):
                os.remove(md_file_path)
            if os.path.exists(json_file_path):
                os.remove(json_file_path)

        return md_content, json_content

    def _convert_to_llm_format(self, content, file_name, llm_text=True):
        """将提取的内容转换为 LLM 需要的 JSON 格式
        :param content: OCR 解析的文件内容
        :param file_name: 文件名
        """
        llm_json = {
            "file_name": file_name,
            "content": []
        }

        # 用于存储按页面索引分组的文本内容
        text_by_page = {}

        for item in content:
            if item["type"] == "text":
                page_idx = item["page_idx"]
                if page_idx not in text_by_page:
                    text_by_page[page_idx] = []
                text_by_page[page_idx].append(item["text"])
            elif item["type"] == "table":
                # 检查 table_caption 是否为空
                table_caption = item.get("table_caption", [""])[0] if item.get("table_caption") else ""
                llm_json["content"].append({
                    "type": "table",
                    "table_caption": table_caption,  # 提取表格标题
                    "table_body": item["table_body"],  # 表格内容
                    "page_idx": item["page_idx"]
                })

        # 将同一页面的文本内容合并为一个 Markdown 格式的字符串
        for page_idx, texts in text_by_page.items():
            combined_text = "\n".join(texts)  # 使用换行符合并文本
            llm_json["content"].append({
                "type": "text",
                "title": "",  # 如果需要标题，可以根据需求提取或设置
                "text": combined_text,
                "page_idx": page_idx
            })

        # 按 page_idx 排序
        llm_json["content"] = sorted(llm_json["content"], key=lambda x: x["page_idx"])

        # 如果 llm_text 为 True，则返回合并的文本字符串
        if llm_text:
            all_texts = []
            for item in llm_json["content"]:
                if item["type"] == "text":
                    text = f"# {item['title']}\n" if item['title'] else ""
                    text += item["text"].strip()
                    all_texts.append(text)
                elif item["type"] == "table":
                    # 将表格内容转换为 Markdown 格式的文本
                    table_text = f"# {item['table_caption']}\n" if item['table_caption'] else ""
                    table_text += item["table_body"].strip()  # 表格内容已经是 Markdown 格式
                    all_texts.append(table_text)
            return "\n\n".join(all_texts)  # 使用换行符分隔不同页面或元素的内容
        else:
            return llm_json

    def process(self, input_path, llm_text=True):
        """
        执行 OCR 处理流程。
        :param input_path:
        :param llm_text:
        :return: 返回转换为 LLM 格式的 JSON 内容
        """
        file_name = os.path.basename(input_path)
        name_without_suff = os.path.splitext(file_name)[0]
        if input_path.lower().endswith(".pdf"):
            pipe_result = self._process_pdf(input_path)
        elif input_path.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            pipe_result = self._process_image(input_path)
        else:
            logging.error(f"不支持的文件类型：{input_path}")
            return None

        md_content, json_content = self._save_files(pipe_result, name_without_suff)

        llm_results = self._convert_to_llm_format(json_content, file_name, llm_text=llm_text)
        return llm_results


# 示例用法
if __name__ == "__main__":
    # output_dir = "./data_test/output"
    from utils.utils import load_config
    config = load_config()
    processor = MinerUOCR(config)

    files = [
        "./data_test/8d1c1ff1-d6f2-4889-b8c9-17f52052cd22.pdf",
        "./data_test/2810号.pdf",
        "./data_test/img_v3_02kc_6e2bade0-a0ed-4529-8dfa-db73f379354g.jpg"  # 添加图像文件测试
    ]
    merged = []
    for file_path in files:
        llm_results = processor.process(file_path, llm_text=True)
        if llm_results:
            merged.append(llm_results)
        print(f"LLM 需要的 JSON 格式：")
        print(json.dumps(llm_results, ensure_ascii=False, indent=4))

    print(f"合并后的 JSON 结果：")
    print(json.dumps(merged, ensure_ascii=False, indent=4))
