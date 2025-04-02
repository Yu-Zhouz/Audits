# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: ocr_paddle.py
@Time    : 2025/3/12 下午6:13
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : OCR 处理脚本，调用 PaddleOCR 框架，使用 PaddleX 框架的 OCR 完成图像和 PDF 的文字提取为 JSON 格式
@Usage   :
"""
import logging
import os
import json
import base64
import time

import requests
# from modelscope.models.multi_modal.vldoc.conv_fpn_trans import logging
from pdf2image import convert_from_path


class PaddleOCR:
    def __init__(self, config):
        """
        初始化 OCR 处理器。
        :param config
        """
        # 获取 OCR 识别服务的配置
        self.output_dir = os.path.join(config.get("data_config", {}).get("output_dir"), "paddle")
        self.image_dir = os.path.join(self.output_dir , "images")
        self.service_url = config.get("ocr_paddle_config", {}).get("service_url")
        self.delete_files = config.get("data_config", {}).get("delete_files")
        self._prepare_directories()
        # logging.info(f"OCR 处理器已初始化，服务器地址为： {self.service_url}")

    def _prepare_directories(self):
        """创建必要的输出目录"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

    def _call_ocr_service(self, image_path, max_retries=10, delay=3):
        """
        调用 OCR 服务，获取文字检测结果。
        :param image_path: 输入图片路径
        :param max_retries: 最大重试次数
        :param delay: 每次重试之间的延迟秒数
        :return: OCR 结果（包含文字边界框和内容）
        """
        with open(image_path, "rb") as file:
            file_bytes = file.read()
            file_data = base64.b64encode(file_bytes).decode("ascii")

        payload = {"file": file_data, "fileType": 1}  # fileType=1 表示图像文件

        for attempt in range(max_retries):
            try:
                response = requests.post(self.service_url, json=payload, timeout=(30, 90))

                if response.status_code != 200:
                    logging.error(f"请求失败，状态代码 {response.status_code}: {response.text}")

                ocr_result = response.json()
                # print(f"OCR 结果已获取：{image_path}")
                return ocr_result

            except Exception as e:
                logging.error(f"尝试 {attempt + 1} 次,失败: {e}")
                if attempt < max_retries - 1:
                    logging.info(f"在 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    logging.error("达到最大重试次数。")
                    raise

    def _convert_pdf_to_images(self, pdf_path):
        """
        将 PDF 转换为图像列表。
        :param pdf_path: 输入 PDF 文件路径
        :return: 图像路径列表
        """
        images = convert_from_path(pdf_path)
        image_paths = []
        for i, image in enumerate(images):
            image_path = os.path.join(self.image_dir, f"page_{i + 1}.jpg")
            image.save(image_path, "JPEG")
            image_paths.append(image_path)
        return image_paths

    def _save_results(self, results, name_without_suff):
        """
        将文字识别结果保存为 JSON 格式。
        :param results: 文字识别结果
        :param name_without_suff: 文件名（不含扩展名）
        :return: JSON 文件路径
        """
        json_path = os.path.join(self.output_dir, f"{name_without_suff}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        # print(f"JSON 文件已生成：{json_path}")

    def _process_image(self, image_path):
        """
        处理单个图像文件。
        :param image_path: 输入图像路径
        :return: OCR 结果
        """
        ocr_result = self._call_ocr_service(image_path)
        if ocr_result.get("errorCode") != 0:
            logging.error(f"OCR 服务返回错误: {ocr_result.get('errorMsg')}")

        ocr_results = ocr_result.get("result", [])
        if not ocr_results:
            logging.warning("OCR 服务返回的结果中没有有效的文字检测结果")

        pruned_result = ocr_results['ocrResults'][0]["prunedResult"]
        results = [
            {"text": text, "bbox": box}
            for text, box in zip(pruned_result["rec_texts"], pruned_result["rec_polys"])
        ]
        return results

    def _process_pdf(self, pdf_path):
        """
        处理 PDF 文件。
        :param pdf_path: 输入 PDF 文件路径
        :return: OCR 结果列表
        """
        image_paths = self._convert_pdf_to_images(pdf_path)
        results = []
        for image_path in image_paths:
            result = self._process_image(image_path)
            results.append(result)

        # 删除生成的文件，释放空间
        if os.path.exists(self.image_dir):
            for file in os.listdir(self.image_dir):
                os.remove(os.path.join(self.image_dir, file))

        return results

    def _convert_to_llm_format(self, content, file_name, is_pdf=False, llm_text=True):
        """将提取的内容转换为 LLM 需要的 JSON 格式
        :param content: OCR 解析的文件内容
        :param file_name: 文件名
        :param is_pdf: 是否为 PDF 文件（PDF 是二维列表，图像是一维列表）
        """
        llm_json = {
            "file_name": file_name,
            "content": []
        }

        if is_pdf:
            # PDF 文件：内容是二维列表，每个子列表代表一页
            for page_idx, page_content in enumerate(content):
                page_text = []  # 用于存储当前页面的所有文本内容
                page_tables = []  # 用于存储当前页面的所有表格内容

                for item in page_content:
                    item_type = item.get("type", "text")  # 默认为文本类型
                    if item_type == "text":
                        text = item.get("text", "").strip()
                        if text:  # 如果文本不为空
                            page_text.append(text)
                    elif item_type == "table":
                        table_caption = item.get("table_caption", [""])[0] if item.get("table_caption") else ""
                        table_body = item.get("table_body", [])
                        page_tables.append({
                            "type": "table",
                            "table_caption": table_caption,
                            "table_body": table_body,
                            "page_idx": page_idx
                        })

                # 合并当前页面的所有文本内容
                if page_text:
                    combined_text = "，".join(page_text)  # 使用换行符合并文本
                    llm_json["content"].append({
                        "type": "text",
                        "title": "",  # 如果需要标题，可以根据需求提取或设置
                        "text": combined_text,
                        "page_idx": page_idx
                    })

                # 添加当前页面的表格内容
                llm_json["content"].extend(page_tables)

        else:
            # 图像文件：内容是一维列表，所有内容都在第一页
            page_idx = 0
            page_text = []  # 用于存储当前页面的所有文本内容
            page_tables = []  # 用于存储当前页面的所有表格内容

            for item in content:
                item_type = item.get("type", "text")  # 默认为文本类型
                if item_type == "text":
                    text = item.get("text", "").strip()
                    if text:  # 如果文本不为空
                        page_text.append(text)
                elif item_type == "table":
                    table_caption = item.get("table_caption", [""])[0] if item.get("table_caption") else ""
                    table_body = item.get("table_body", [])
                    page_tables.append({
                        "type": "table",
                        "table_caption": table_caption,
                        "table_body": table_body,
                        "page_idx": page_idx
                    })

            # 合并当前页面的所有文本内容
            if page_text:
                combined_text = "，".join(page_text)  # 使用换行符合并文本
                llm_json["content"].append({
                    "type": "text",
                    "title": "",  # 如果需要标题，可以根据需求提取或设置
                    "text": combined_text,
                    "page_idx": page_idx
                })

            # 添加当前页面的表格内容
            llm_json["content"].extend(page_tables)

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
        主流程：处理输入文件（图像或 PDF）。
        :param input_path: 输入文件路径
        :param llm_text:
        :return: OCR 结果
        """
        file_name = os.path.basename(input_path)
        name_without_suff = os.path.splitext(file_name)[0]
        if input_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            # print("处理图像文件...")
            results = self._process_image(input_path)
            llm_data = self._convert_to_llm_format(results, file_name, is_pdf=False, llm_text=llm_text)
        elif input_path.lower().endswith('.pdf'):
            # print("处理 PDF 文件...")
            results = self._process_pdf(input_path)
            llm_data = self._convert_to_llm_format(results, file_name, is_pdf=True, llm_text=llm_text)
        else:
            raise ValueError("不支持的文件类型，请提供图像或 PDF 文件。")

        if not self.delete_files:
             self._save_results(results, name_without_suff)

        return llm_data


# 示例用法
if __name__ == "__main__":
    # 加载配置文件
    from utils.utils import load_config
    config = load_config()

    ocr_processor = PaddleOCR(config)

    # 输入文件路径
    files = [
        "./data_test/img_v3_02kc_6e2bade0-a0ed-4529-8dfa-db73f379354g.jpg",
        "./data_test/2810号.pdf"
    ]
    merged = []
    for file in files:
        ocr_results = ocr_processor.process(file, llm_text=True)
        if ocr_results:
            merged.append(ocr_results)

    print(json.dumps(merged, ensure_ascii=False, indent=4))