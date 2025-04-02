# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: seal_recognition.py
@Time    : 2025/3/12 上午11:01
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 使用 PaddleX 框架的印章识别产线检测佐证材料中的印章
@Usage   : 提取印章内容并判断是否包含合法公章
"""
import json
import logging
import os
import base64
import time
import requests
from pdf2image import convert_from_path

class SealExtractor:
    def __init__(self, config):
        """
        初始化印章提取器。
        :param config: 配置文件
        """
        self.output_dir = os.path.join(config.get("data_config", {}).get("output_dir"), "paddle")
        self.image_dir = os.path.join(self.output_dir, "images")
        self.service_url = config.get("seal_config",{}).get("service_url")
        self.delete_files = config.get("data_config", {}).get("delete_files")
        self.pdf_max_pages = config.get("vlm_config", {}).get("pdf_max_pages", 10)
        self._prepare_directories()
        # logging.info(f"Seal 服务已经初始化，服务器地址为： {self.service_url}")

    def _prepare_directories(self):
        """创建必要的输出目录"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)


    def _call_seal_recognition_service(self, image_path, max_retries=10, delay=3):
        """
        调用印章识别服务。
        :param image_path: 输入图像的路径
        :param max_retries: 最大重试次数
        :param delay: 每次重试之间的延迟秒数
        :return: 识别结果
        """
        with open(image_path, "rb") as file:
            image_data = file.read()
        encoded_image = base64.b64encode(image_data).decode("utf-8")

        payload = {
            "file": encoded_image,
            "fileType": 1  # 图像文件类型（1 表示图片）
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(self.service_url, json=payload)
                response.raise_for_status()
                result = response.json()
                # print("印章识别成功：")
                return result
            except requests.exceptions.RequestException as e:
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
        :return: 图像列表
        """
        images = convert_from_path(pdf_path)
        image_paths = []
        for i, image in enumerate(images):
            image_path = os.path.join(self.image_dir, f"page_{i + 1}.jpg")
            image.save(image_path, "JPEG")
            image_paths.append(image_path)

        if self.pdf_max_pages is not None:
            image_paths = image_paths[:self.pdf_max_pages]

        return image_paths

    def _process_image(self, image_path):
        """
        处理单个图像文件。
        :param image_path: 输入图像路径
        :return: 印章识别结果
        """
        result = self._call_seal_recognition_service(image_path)
        return result

    def _process_pdf(self, pdf_path):
        """
        处理 PDF 文件。
        :param pdf_path: 输入 PDF 文件路径
        :return: 印章识别结果列表
        """
        image_paths = self._convert_pdf_to_images(pdf_path)
        results = []
        for image_path in image_paths:
            result = self._call_seal_recognition_service(image_path)
            if result:
                results.append(result)

        # 删除生成的文件，释放空间
        if os.path.exists(self.image_dir):
            for file in os.listdir(self.image_dir):
                os.remove(os.path.join(self.image_dir, file))

        return results

    def _save_results(self, result, name_without_suff):
        """
        保存印章识别结果。
        :param result: 印章识别结果
        :param name_without_suff: 文件名
        """
        # 保存识别结果为 JSON 文件
        json_path = os.path.join(self.output_dir, f"{name_without_suff}_seal.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        # print(f"印章识别结果已保存到 {json_path}")

    def _convert_to_llm_format(self, results):
        llm_data = []
        if isinstance(results, list):
            for result in results:
                seal_rec_results = result.get("result", {}).get("sealRecResults", [])
                for item in seal_rec_results:
                    pruned_result = item.get("prunedResult", {})
                    seal_res_list = pruned_result.get("seal_res_list", [])
                    for seal_res in seal_res_list:
                        if seal_res.get("text_type") == "seal":  # 确保只提取印章类型
                            llm_data.append({
                                "seal_text": seal_res.get("rec_texts", [""])[0],  # 提取第一个识别文本
                                "seal_score": seal_res.get("rec_scores", [0.0])[0],  # 提取第一个识别分数
                            })
        else:
            seal_rec_results = results.get("result", {}).get("sealRecResults", [])
            for item in seal_rec_results:
                pruned_result = item.get("prunedResult", {})
                seal_res_list = pruned_result.get("seal_res_list", [])
                for seal_res in seal_res_list:
                    if seal_res.get("text_type") == "seal":  # 确保只提取印章类型
                        llm_data.append({
                            "seal_text": seal_res.get("rec_texts", [""])[0],
                            "seal_score": seal_res.get("rec_scores", [0.0])[0],
                        })
        return llm_data

    def process(self, input_path):
        """
        主流程：处理输入文件（图像或 PDF）。
        """
        name_without_suff = os.path.splitext(os.path.basename(input_path))[0]
        if input_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            # print("处理图像文件...")
            results = self._process_image(input_path)
        elif input_path.lower().endswith('.pdf'):
            # print("处理 PDF 文件...")
            results = self._process_pdf(input_path)
        else:
            logging.error("不支持的文件类型，请提供图像或 PDF 文件。")

        if not self.delete_files:
            self._save_results(results, name_without_suff)

        llm_data = self._convert_to_llm_format(results)
        return llm_data


# 示例用法
if __name__ == "__main__":
    # 加载配置文件
    from utils.utils import load_config
    config = load_config()

    # 输入文件路径
    files = [
        "./data/input/1162708535117611009/1698716638425_1698716632455.jpg",
        "./data_test/img_v3_02kc_6e2bade0-a0ed-4529-8dfa-db73f379354g.jpg",
        "./data_test/2810号.pdf"
    ]

    # 初始化印章提取器
    extractor = SealExtractor(config)

    merged = []
    for file in files:
        seal_result = extractor.process(file)
        if seal_result:
            merged.append(seal_result)

    print(json.dumps(merged, ensure_ascii=False, indent=4))