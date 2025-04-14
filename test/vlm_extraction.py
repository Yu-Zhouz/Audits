# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: vlm_extraction.py
@Time    : 2025/3/20 上午9:35
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 利用vlm大模型Qwen/Qwen2.5-VL-7B-Instruct完成图像和pdf信息的抽取
@Usage   : prompt接口参考https://www.cnblogs.com/fasterai/p/18553752， Prompt构建参考https://github.com/Acmesec/PromptJailbreakManual?tab=readme-ov-file#prompt%E7%BC%96%E5%86%99%E6%96%B9%E6%B3%95%E6%80%BB%E7%BB%93
"""



# OpenAI SDK
import logging
import os
import time
import json
import base64
from openai import OpenAI, OpenAIError
from pdf2image import convert_from_path
from PIL import Image
Image.MAX_IMAGE_PIXELS = 1000000000

class VLM:
    def __init__(self, config):
        self.config = config.get("vlm_config", {})
        self.output_dir = os.path.join(config.get("data_config", {}).get("output_dir"), "vlm")
        self.image_dir = os.path.join(self.output_dir, "images")
        self._prepare_directories()
        self.service_url = self.config.get("service_url")
        self.model = self.config.get("model", "Qwen2.5-VL-32B")
        self.pdf_max_pages = self.config.get("pdf_max_pages", 10)
        self.key = ['公章', '当事人', '图斑编号', '建筑层数', '占地面积', '建筑面积']
        self.api_key = "EMPTY"  # 使用空字符串或任意值，因为 vLLM 不需要 API key
        # logging.info(f"VLM 服务已经初始化，服务器地址为： {self.service_url}")

        self.last_result = None  # 添加变量用于记录上一次模型识别的结果

    def init_client(self):
        """初始化OpenAI客户端"""
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.service_url,
        )
        return client

    def _prepare_directories(self):
        """创建必要的输出目录"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

    @staticmethod
    def _encode_image(image_path):
        """
        将图像文件编码为 base64 字符串。
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logging.error(f"编码图像 {image_path} 时发生错误：{e}")
            return ""

    @staticmethod
    def _resize_image(image, max_size=1024):
        """等比缩放图像到最大尺寸"""
        width, height = image.size
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * max_size / width)
            else:
                new_height = max_size
                new_width = int(width * max_size / height)
            image = image.resize((new_width, new_height), Image.LANCZOS)
        return image

    def _compress_image(self, input_path, output_path, quality=100, max_size=2048):
        """压缩图像文件并保存为 JPEG 格式"""
        with Image.open(input_path) as img:
            # 转换为 RGB 模式（如果图像是 PNG 或其他模式）
            if img.mode != 'RGB':
                img = img.convert('RGB')
                # 等比缩放图像
            max_size = max(max_size, 512)
            img = self._resize_image(img, max_size=max_size)
            # 保存为 JPEG 格式，指定质量
            img.save(output_path, "JPEG", quality=quality)

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

    def _vlm_service(self, prompt, max_retries=5, delay=3, initial_quality=100, is_image_request=True):
        """调用模型"""

        # 如果有上一次的结果，将其作为上下文信息添加到prompt中
        if self.last_result:
            prompt.append({"type": "text", "text": f"""根据上一个的结果：{self.last_result}，继续补充空缺的关键信息；
            如果公章为True则不再更新，如果为False则继续查找公章，只要有公章则为True；
            如果遇到人员名单明细表或者多个当事人名单的统计表，则不能更新当事人信息，需要根据上一个结果的当事人字段查询其余补充空缺信息；
            如果再次出现身份证、户口本、产权证书则更新当事人信息"""})

        # 验证 prompt 格式
        if not isinstance(prompt, list):
            logging.error("Prompt 格式错误，必须是列表。")
            return ""

        # 构造请求数据
        messages = [
            {
                "role": "system",
                "content": "你是一个文件解析助手，需要从我指定的关键信息中抽取结果"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        client = self.init_client()

        current_quality = initial_quality
        min_quality = 30  # 设置一个最低质量阈值，避免无限降低质量
        max_size_ratio = 4
        for attempt in range(max_retries):
            try:
                # 使用OpenAI API
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0,
                    top_p=1.0,
                    max_tokens=512,
                    extra_body={
                        "repetition_penalty": 1.05,
                    },
                )
                response_data = response.choices[0].message.content
                return response_data
            except Exception as e:
                logging.error(f"请求失败，正在重试（{attempt + 1}/{max_retries}）... 错误信息：{e}")
                if attempt < max_retries - 1 and is_image_request:
                    # 在重试之前，尝试重新压缩图像并转换为Base64
                    if hasattr(self, '_image_path') and callable(self._process_image):  # 确保存在_image_path和_process_image方法
                        image_path = getattr(self, '_image_path', None)  # 获取_image_path属性的值
                        if image_path:
                            # 逐步降低图像质量
                            current_quality = max(current_quality - 20, min_quality)
                            logging.info(f"尝试重新压缩图像，降低质量：{current_quality}，图像最大分辨率：{512 * max_size_ratio}")
                            compressed_image_path = os.path.join(self.image_dir, f"compressed_{current_quality}.jpg")
                            self._compress_image(image_path, compressed_image_path, quality=current_quality, max_size=512*max_size_ratio)
                            encoded_image = self._encode_image(compressed_image_path)
                            if encoded_image:
                                # 更新prompt中的图像URL
                                prompt[0] = {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
                                }
                                messages[1]["content"] = prompt
                            else:
                                logging.error("重新压缩图像并转换为Base64失败。")
                    time.sleep(delay)
                    delay *= 1  # 每次重试增加延迟
                    max_size_ratio -= 1
                else:
                    logging.error("请求失败，已超过最大重试次数。")
                    return ""

    def _process_image(self, image_path):
        """处理图像文件"""
        # 设置_image_path属性
        self._image_path = image_path

        # 将图像文件编码为 base64 字符串
        encoded_image = self._encode_image(image_path)
        if encoded_image:
            prompt = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}

                },
                {"type": "text", "text": f"""要抽取的关键信息：{self.key}, 其中公章为bool类型，只要有公章则为True；
                                    当事人只有一位人，不存在多个当事人，需要从身份证、户口本、产权证书、施工牌等文件中提取,
                                    如果没有自然人名称可提取申请文件中的企业名称、项目单位、申报单位、实施主体或项目负责单位的名称（唯一）；
                                    建筑层数和占地面积都为int类型，不需要加单位;
                                    图斑编号的格式为：HZJGZWYYYYMM-XXXXXXXXXXXXZNNNN，即不是身份证号，也不是农宅施编号，严格以HZJGZW开头的编号格式。
                                    在返回结果时使用json格式，包含多个key-value对，key值为我指定的关键信息值唯一，value值为所抽取的结果。
                                    如果认为图像中没有关键信息key，则将value赋值为“null”。请只输出json格式的结果，不要包含其它多余文字！"""}
            ]
            results = self._vlm_service(prompt, max_retries=5, delay=3, is_image_request=True)

            return results
        else:
            logging.error("图像文件编码失败。")

    def _process_pdf(self, pdf_path):
        """处理 PDF 文件"""
        # 将 PDF 转换为图像列表
        image_paths = self._convert_pdf_to_images(pdf_path)
        results = []

        # TODO: 指定最大页数,限制最大页数
        if self.pdf_max_pages is not None:
            image_paths = image_paths[:self.pdf_max_pages]

        for image_path in image_paths:
            results.append(self._process_image(image_path))

        return results

    # 数据后处理
    def _post_process(self, response_data):
        try:
            if len(response_data) < 8:
                logging.warning("返回结果过短，可能解析失败。")
                return {
                    "公章": False,
                    "当事人": None,
                    "图斑编号": None,
                    "建筑层数": None,
                    "占地面积": None,
                    "建筑面积": None
                }
            else:
                # 去除多余的 Markdown 格式（三个```）
                json_content = response_data.strip("```")
                # 去除多余的前缀（如 "json"）
                json_content = json_content.strip("json").strip()
                # 替换非标准的 null 为 JSON 标准的 null
                # 验证返回结果是否为 JSON 格式
                result = json.loads(json_content)
                # 将 JSON 中的 null 替换为 None
                for key, value in result.items():
                    if value is None or value == "null":
                        result[key] = None
                # 特别处理公章字段：如果为 None，则替换为 False
                if result["公章"] is None or result["公章"] == "null":
                    result["公章"] = False

                # 返回处理后的字典
                return result
        except json.JSONDecodeError as e:
            logging.error(f"返回结果不是有效的 JSON 格式: {e}")
            return None

    def process(self, input_path):
        """
        主流程：处理输入文件（图像或 PDF）。
        :param input_path: 输入文件路径
        """
        results = {}
        if input_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            # logging.info("处理图像文件...")
            response_data = self._process_image(input_path)
            results = self._post_process(response_data)
        elif input_path.lower().endswith('.pdf'):
            # logging.info("处理 PDF 文件...")
            response_data = self._process_pdf(input_path)
            if response_data:
                # 初始化一个字典来存储每个字段的值
                aggregated_results = {key: [] for key in self.key}
                for result in response_data:
                    result_ = self._post_process(result)
                    if result_:
                        for key in self.key:
                            if key in result_:
                                aggregated_results[key].append(result_[key])

                # 对每个字段取最常见值
                final_results = {}
                for key, values in aggregated_results.items():
                    if values:
                        most_common_value = max(set(values), key=values.count)
                        final_results[key] = most_common_value
                    else:
                        final_results[key] = None
                results = final_results
        else:
            raise ValueError("不支持的文件类型，请提供图像或 PDF 文件。")

        # 更新 last_result
        self.last_result = results

        # 删除生成的文件，释放空间
        if os.path.exists(self.image_dir):
            for file in os.listdir(self.image_dir):
                os.remove(os.path.join(self.image_dir, file))

        return results

    # TODO:专门针对文本的处理
    def process_text(self, ocr_text):
        """
        处理提取的文本，提取关键信息。
        使用 VLM 模型的 API 进行情感分析和信息抽取。
        """
        prompt = [
            {"type": "text", "text": f"""OCR文字：```{ocr_text}```"""},
            {"type": "text", "text": f"""要抽取的关键信息：{self.key}, 其中公章为bool类型，只要有公章则为True；
                                当事人只有一位人，不存在多个当事人，需要从身份证、户口本、产权证书、施工牌等文件中提取,
                                如果没有自然人名称可提取申请文件中的企业名称、项目单位、申报单位、实施主体或项目负责单位的名称（唯一）；
                                建筑层数和占地面积都为int类型，不需要加单位;
                                图斑编号的格式为：HZJGZWYYYYMM-XXXXXXXXXXXXZNNNN，即不是身份证号，也不是农宅施编号，严格以HZJGZW开头的编号格式。
                                在返回结果时使用json格式，包含多个key-value对，key值为我指定的关键信息值唯一，value值为所抽取的结果。
                                如果认为图像中没有关键信息key，则将value赋值为“null”。请只输出json格式的结果，不要包含其它多余文字！"""}
        ]

        try:
            response = self._vlm_service(prompt, max_retries=5, delay=3, is_image_request=False)
            # 结果后处理
            results = self._post_process(response)
            return results
        except OpenAIError as e:  # 捕获 OpenAI 库的异常
            logging.error(f"处理文本时发生网络问题：{e}")
            return ""
        except Exception as e:
            logging.error(f"处理文本时发生错误：{e}")
            return ""


    # TODO:专门处理文件名列表
    def process_file_list(self, file_list):
        """
        处理文件名列表，提取关键信息。
        使用 VLM 模型的 API 进行情感分析和信息抽取。
        """
        prompt = [
            {"type": "text", "text": f"""文件名列表：{file_list}"""},
            {"type": "text", "text": f"""从上述文件名列表中的图像或pdf文件名中提取：'当事人'。
                                当事人只有一位人，一般为人名,例如：黄逸凡。
                                在返回结果时使用json格式，包含多个key-value对，key值为我指定的关键信息值唯一，value值为所抽取的结果。
                                如果认为图像中没有关键信息key，则将value赋值为“null”。请只输出json格式的结果，不要包含其它多余文字！"""}
        ]

        try:
            response = self._vlm_service(prompt, max_retries=3, delay=1, is_image_request=False)
            # 结果后处理
            try:
                # 去除多余的 Markdown 格式（三个```）
                json_content = response.strip("```")
                # 去除多余的前缀（如 "json"）
                json_content = json_content.strip("json").strip()
                # 替换非标准的 null 为 JSON 标准的 null
                # 验证返回结果是否为 JSON 格式
                result = json.loads(json_content)
                results = {
                    "公章": False,
                    "当事人": result.get("当事人", None),
                    "图斑编号": None,
                    "建筑层数": None,
                    "占地面积": None,
                    "建筑面积": None
                }

                # 更新 last_result
                self.last_result = results
                return results
            except json.JSONDecodeError as e:
                logging.error(f"返回结果不是有效的 JSON 格式: {e}")
        except OpenAIError as e:  # 捕获 OpenAI 库的异常
            logging.error(f"处理文件列表时发生网络问题：{e}")
        except Exception as e:
            logging.error(f"处理文件列表时发生错误：{e}")



if __name__ == "__main__":
    # 加载配置文件
    from utils.utils import load_config
    config = load_config()

    # 创建 VLM 实例
    vlm = VLM(config)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # 如果使用httpx
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 测试处理文件名列表
    # file_list = ["./test_output/1225053238252797952/1713922689967_1713922669370.jpg",
    #              "./test_output/1225053238252797952/1713922807311_1713922799638.jpg",
    #              "./test_output/1225053238252797952/1713922821143_1713922813914.jpg",
    #              "./test_output/1225053238252797952/1723102470128_1723102463912.jpg",
    #              "./test_output/1225053238252797952/mmexport1714028313059.jpg",
    #              "./test_output/1225053238252797952/Screenshot_20231030_105243.jpg",
    #              "./test_output/1225053238252797952/Screenshot_20231030_105314.jpg",
    #              "./test_output/1225053238252797952/Screenshot_20231030_105332.jpg",
    #              "./test_output/1225053238252797952/纪要20236号人员名单明细.pdf"]
    # file_list = ["./test_output/1230441506888744960/1714615444154_IMG_20240502_100320.jpg",
    #              "./test_output/1230441506888744960/mmexport1714619807231.jpg",
    #              "./test_output/1230441506888744960/Screenshot_20231030_105243.jpg",
    #              "./test_output/1230441506888744960/三栋镇农村住宅建设管理工作领导小组联席会议纪要(2023年6号）.pdf",
    #              "./test_output/1230441506888744960/冯远才.pdf",
    #              "./test_output/1230441506888744960/纪要20236号人员名单明细.pdf"]
    # file_list = ["./test_output/1212003154116214785/佐证2.pdf",
    #             "./test_output/1212003154116214785/县、镇证明.pdf",
    #             "./test_output/1212003154116214785/过后明细.pdf",
    #              "./test_output/1212003154116214785/过后纪要.pdf"]
    file_list = ["./test_output/1296873620546519040/（已压缩）林源盛一户一档.pdf"]
    results = vlm.process_file_list(file_list)
    print("处理结果：", results)

    for file_path in file_list:
        if os.path.isfile(file_path):
            results = vlm.process(file_path)
            print(f"{file_path} 的处理结果：{results}")
        else:
            print(f"文件 {file_path} 不存在！")














# requests 接口
# # -*- coding: utf-8 -*-
# """
# @Project : Audits
# @FileName: vlm_extraction.py
# @Time    : 2025/3/20 上午9:35
# @Author  : ZhouFei
# @Email   : zhoufei.net@gmail.com
# @Desc    : 利用vlm大模型Qwen/Qwen2.5-VL-7B-Instruct完成图像和pdf信息的抽取
# @Usage   :
# """
# import logging
# import os
# import time
# import requests
# import json
# import base64
# from pdf2image import convert_from_path
#
#
# class VLM:
#     def __init__(self, config):
#         self.config = config.get("vlm_config", {})
#         self.output_dir = os.path.join(config.get("data_config", {}).get("output_dir"), "vlm")
#         self.image_dir = os.path.join(self.output_dir, "images")
#         self._prepare_directories()
#         self.service_url = self.config.get("service_url")
#         self.model = self.config.get("model", "Qwen2.5-VL-7B")
#         self.key = ['公章', '当事人', '图斑编号', '建筑层数', '占地面积', '建筑面积']
#         # logging.info(f"VLM 服务已经初始化，服务器地址为： {self.service_url}")
#
#     def _prepare_directories(self):
#         """创建必要的输出目录"""
#         os.makedirs(self.output_dir, exist_ok=True)
#         os.makedirs(self.image_dir, exist_ok=True)
#
#     def _encode_image(self, image_path):
#         """
#         将图像文件编码为 base64 字符串。
#         """
#         try:
#             with open(image_path, "rb") as image_file:
#                 return base64.b64encode(image_file.read()).decode('utf-8')
#         except Exception as e:
#             logging.error(f"编码图像 {image_path} 时发生错误：{e}")
#             return ""
#
#     def _convert_pdf_to_images(self, pdf_path):
#         """
#         将 PDF 转换为图像列表。
#         :param pdf_path: 输入 PDF 文件路径
#         :return: 图像路径列表
#         """
#         images = convert_from_path(pdf_path)
#         image_paths = []
#         for i, image in enumerate(images):
#             image_path = os.path.join(self.image_dir, f"page_{i + 1}.jpg")
#             image.save(image_path, "JPEG")
#             image_paths.append(image_path)
#         return image_paths
#
#     def _vlm_service(self, prompt, max_retries=10, delay=3):
#         """调用模型"""
#         prompt.append(
#             {"type": "text", "text": f"""要抽取的关键信息：{self.key},其中公章为bool类型，只要有公章则为True；
#                     当事人只有一位人，不是单位名称，也不存在多个当事人；建筑层数和占地面积都为int类型，不需要加单位。
#                     在返回结果时使用json格式，包含多个key-value对，key值为我指定的关键信息值唯一，value值为所抽取的结果。
#                     如果认为图像中没有关键信息key，则将value赋值为“null”。请只输出json格式的结果，不要包含其它多余文字！"""}
#         )
#         # 构造请求数据
#         data = {
#             "model": self.model,
#             "messages": [
#                 {
#                     "role": "system",
#                     "content": "你是一个文件解析助手，需要从我指定的关键信息中抽取结果"
#                 },
#                 {
#                     "role": "user",
#                     "content": prompt
#                 }
#             ],
#             "temperature": 0.7,
#             "top_p": 0.8,
#             "repetition_penalty": 1.05,
#             "max_tokens": 1024
#         }
#         for attempt in range(max_retries):
#             try:
#                 response = requests.post(
#                     self.service_url + "/chat/completions",
#                     json=data,
#                     # timeout=(100, 300)  # 设置超时时间
#                 )
#                 response.raise_for_status()  # 检查请求是否成功
#                 response_data = response.json().get("choices", [])[0].get("message", {}).get("content", "")
#                 return response_data
#             except requests.exceptions.RequestException as e:
#                 logging.error(f"请求失败，正在重试（{attempt + 1}/{max_retries}）... 错误信息：{e}")
#                 if attempt < max_retries - 1:
#                     time.sleep(delay)
#                 else:
#                     logging.error("请求失败，已超过最大重试次数。")
#                     return ""
#
#     def _process_image(self, image_path):
#         """处理图像文件"""
#         # 将图像文件编码为 base64 字符串
#         encoded_image = self._encode_image(image_path)
#         if encoded_image:
#             prompt = [
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
#                 }
#             ]
#             results = self._vlm_service(prompt, max_retries=5, delay=5)
#             return results
#         else:
#             logging.error("图像文件编码失败。")
#
#     def _process_pdf(self, pdf_path):
#         """处理 PDF 文件"""
#         # 将 PDF 转换为图像列表
#         image_paths = self._convert_pdf_to_images(pdf_path)
#         results = []
#
#         # 如果 PDF 页数较少，一次性输入模型解析
#         if 1 < len(image_paths) <= 5:
#             logging.info(f"PDF共{len(image_paths)}页，尝试一次性输入模型解析...")
#             encoded_images = [self._encode_image(image_path) for image_path in image_paths]
#             prompt = []
#             for encoded_image in encoded_images:
#                 if encoded_image:
#                     prompt.append(
#                         {
#                             "type": "image_url",
#                             "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
#                         }
#                     )
#                 else:
#                     logging.error("图像文件编码失败。")
#             results.append(self._vlm_service(prompt, max_retries=10, delay=3))
#         else:
#             # 如果 PDF 页数较多，逐页处理
#             logging.info("逐页处理...")
#             for image_path in image_paths:
#                 results.append(self._process_image(image_path))
#
#         # 删除生成的文件，释放空间
#         if os.path.exists(self.image_dir):
#             for file in os.listdir(self.image_dir):
#                 os.remove(os.path.join(self.image_dir, file))
#
#         return results
#
#     # 数据后处理
#     def _post_process(self, response_data):
#         try:
#             # 去除多余的 Markdown 格式（三个```）
#             json_content = response_data.strip("```")
#             # 去除多余的前缀（如 "json"）
#             json_content = json_content.strip("json").strip()
#             # 替换非标准的 null 为 JSON 标准的 null
#             # 验证返回结果是否为 JSON 格式
#             result = json.loads(json_content)
#             # 将 JSON 中的 null 替换为 None
#             for key, value in result.items():
#                 if value is None:
#                     result[key] = None
#             # 特别处理公章字段：如果为 None，则替换为 False
#             if result.get("公章") is None:
#                 result["公章"] = False
#
#             # 返回处理后的字典
#             return result
#         except json.JSONDecodeError as e :
#             logging.error(f"返回结果不是有效的 JSON 格式: {e}")
#             return None
#
#     def process(self, input_path):
#         """
#         主流程：处理输入文件（图像或 PDF）。
#         :param input_path: 输入文件路径
#         """
#         results = {}
#         if input_path.lower().endswith(('.jpg', '.jpeg', '.png')):
#             # logging.info("处理图像文件...")
#             response_data = self._process_image(input_path)
#             results = self._post_process(response_data)
#         elif input_path.lower().endswith('.pdf'):
#             # logging.info("处理 PDF 文件...")
#             response_data = self._process_pdf(input_path)
#             if response_data:
#                 # 初始化一个字典来存储每个字段的值
#                 aggregated_results = {key: [] for key in self.key}
#                 for result in response_data:
#                     result_ = self._post_process(result)
#                     if result_:
#                         for key in self.key:
#                             if key in result_:
#                                 aggregated_results[key].append(result_[key])
#
#                 # 对每个字段取最常见值
#                 final_results = {}
#                 for key, values in aggregated_results.items():
#                     if values:
#                         most_common_value = max(set(values), key=values.count)
#                         final_results[key] = most_common_value
#                     else:
#                         final_results[key] = None
#                 results = final_results
#         else:
#             raise ValueError("不支持的文件类型，请提供图像或 PDF 文件。")
#
#         return results
#
#     # TODO:专门针对文本的处理
#     def process_text(self, ocr_text):
#         """
#         处理提取的文本，提取关键信息。
#         使用 VLM 模型的 API 进行情感分析和信息抽取。
#         """
#         prompt = [
#             {"type": "text", "text": f"""OCR文字：```{ocr_text}```"""},
#         ]
#
#         try:
#             response = self._vlm_service(prompt, max_retries=10, delay=3)
#             # 结果后处理
#             results = self._post_process(response)
#             return results
#         except requests.exceptions.RequestException as e:
#             logging.error(f"处理文本时发生网络问题：{e}")
#             return ""
#         except Exception as e:
#             logging.error(f"处理文本时发生错误：{e}")
#             return ""
#
#
# if __name__ == "__main__":
#     # 加载配置文件
#     from utils.utils import load_config
#     config = load_config()
#
#     # 创建 VLM 实例
#     vlm = VLM(config)
#
#     # 测试处理图像文件
#     image_path = "./data_test/img_v3_02kc_6e2bade0-a0ed-4529-8dfa-db73f379354g.jpg"
#     result = vlm.process(image_path)
#     print("处理结果：", result)
#
#     # 测试处理 PDF 文件
#     pdf_path = "./data_test/2810号.pdf"
#     results = vlm.process(pdf_path)
#     print("处理结果：", results)
