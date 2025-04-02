# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: llm_extraction.py
@Time    : 2025/3/12 上午11:03
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 调用 vLLM 框架的QwQ-32B模型用于提取文本信息为固定的json格式输出。
@Usage   :
"""
import json
import logging
import time
from openai import OpenAI
from utils.utils import load_examples



# class LLM:
#     def __init__(self, config):
#         """初始化LLM"""
#         self.key = ['当事人', '图斑编号', '建筑层数', '占地面积']
#         self.service_url = config.get("llm_config", {}).get("service_url")
#         self.example_file = config.get("llm_config", {}).get("example_file")
#         self.model = config.get("llm_config", {}).get("model", "QwQ-32B")
#         self.api_key = "EMPTY"  # 使用空字符串或任意值，因为 vLLM 不需要 API key
#         self.prompt = []
#
#     def init_client(self):
#         """初始化OpenAI客户端"""
#         client = OpenAI(
#             api_key=self.api_key,
#             base_url=self.service_url,
#         )
#         return client
#
#     def init_prompt(self):
#         """初始化对话内容"""
#         task_description = """
#                             你的任务是从OCR文字识别结果中提取指定的关键信息。OCR结果用```包围，关键信息用[]包围。需要注意OCR结果可能存在识别问题，需结合上下文语义判断。
#                             返回结果使用json格式，key为指定的关键信息，value为提取结果。若无对应key，value设为“未找到相关信息”。请只输出json格式结果!,简化思考过程,不需要过度思考
#                             """
#         task_response = "好的，我会根据您提供的OCR结果提取关键信息并以JSON格式返回。"
#         example_guide = """我会提供不同场景下的OCR识别结果和要提取的关键信息示例，每个例子由[START]和[END]包围，请学习这些例子中的字段。"""
#         example_response = "好的，请提供OCR识别结果和关键信息示例，我会根据内容进行提取。"
#
#         self.add_dialog(task_description, task_response)
#         self.add_dialog(example_guide, example_response)
#
#     def add_dialog(self, user_content, bot_content):
#         """添加对话内容"""
#         self.prompt.append({"role": "user", "content": user_content})
#         self.prompt.append({"role": "assistant", "content": bot_content})
#
#     def example_chat(self):
#         """加载示例对话"""
#         example_data = load_examples(self.example_file)
#         for data in example_data.items():
#             user_content = f"[START]{data[0]}[END]"
#             bot_content = json.dumps(data[1]['关键信息项及结果'], ensure_ascii=False)
#             self.add_dialog(user_content, bot_content)
#
#     def eb_pred(self, max_retries=10, delay=3):
#         """调用模型"""
#         client = self.init_client()
#         for attempt in range(max_retries):
#             try:
#                 response = client.chat.completions.create(
#                     model=self.model,
#                     messages=self.prompt,
#                     temperature=0.0,
#                     top_p=1.0,
#                     max_tokens=1024,
#                     extra_body={
#                         "repetition_penalty": 1.05,
#                     },
#                 )
#                 response_data = response.choices[0].message.content
#                 return response_data
#             except Exception as e:
#                 logging.error(f"尝试 {attempt + 1} 次,失败: {e}")
#                 if attempt < max_retries - 1:
#                     logging.info(f"在 {delay} 秒后重试...")
#                     time.sleep(delay)
#                 else:
#                     logging.error("达到最大重试次数。")
#                     raise
#
#     def process(self, ocr_text):
#         """开始对话并提取关键信息"""
#         self.init_prompt()
#         self.example_chat()
#         # TODO:文本长度分段处理
#         # print(f"输入文本长度{len(ocr_text)}")
#         prompt = f"""结合上面的例子，提取下面信息：
#                     OCR文字：```{ocr_text}```
#                     要抽取的关键信息：{self.key}。
#                     在返回结果时使用json格式，包含多个key-value对，key值为我指定的关键信息值唯一，value值为所抽取的结果。
#                     如果认为OCR识别结果中没有关键信息key，则将value赋值为“None”。请只输出json格式的结果，不要包含其它多余文字！
#                     """
#         self.add_dialog(prompt, "")
#
#         response_data = self.eb_pred()
#         if response_data:
#             try:
#                 logging.debug(f"原始响应数据: {response_data}")
#                 # 从 </think> 之后开始提取内容
#                 json_start = response_data.find("</think>") + len("</think>")
#                 if json_start != -1:
#                     # 提取 </think> 之后的内容
#                     json_content = response_data[json_start:].strip()
#                     # 去除多余的 Markdown 格式（三个```）
#                     json_content = json_content.strip("```")
#                     # 去除多余的前缀（如 "json"）
#                     json_content = json_content.strip("json").strip()
#                     # 验证返回结果是否为 JSON 格式
#                     logging.debug(f"解析后的 JSON 内容: {json_content}")
#                     result = json.loads(json_content)
#                     # return json.dumps(result, ensure_ascii=False, indent=4)
#                     # 返回字典格式
#                     return result
#                 else:
#                     logging.error("未找到 </think> 标记，无法提取 JSON 内容")
#             except json.JSONDecodeError:
#                 logging.error("返回结果不是有效的 JSON 格式")
#                 return None
#
#
# if __name__ == "__main__":
#     # 加载配置文件
#     from utils.utils import load_config
#     config = load_config()
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#     # 示例 OCR 结果
#     ocr_text = "\n\n<html><body><table><tr><td>图斑号</td><td colspan=\"5\">HZJGZW202401-441322122510Z0006</td></tr><tr><td>当事人姓名（附 户口本）</td><td>张伟东、张利明 张群光、张主光</td><td>家庭成员（附 户口本）</td><td colspan=\"3\"></td></tr><tr><td>占地面积</td><td>408.05M</td><td>建筑面积</td><td colspan=\"3\">层数 408.05M</td></tr><tr><td>建设时间 （年／月）</td><td>2023.10</td><td>坐落位置</td><td colspan=\"3\">杨村镇水华寨村</td></tr><tr><td>建筑性质</td><td>永久口临时</td><td>建筑类型</td><td colspan=\"3\">新建口加建口拆旧建新</td></tr><tr><td colspan=\"3\">是否符合“一户一宅”</td><td colspan=\"3\">是 口否</td></tr><tr><td colspan=\"3\">是否本村村民自建自住自用</td><td colspan=\"3\">是 口否</td></tr><tr><td>变化图斑简要说明</td><td colspan=\"5\">惠龙高速拆迁户，村内无其他住房，急需建房满足日常居住。</td></tr><tr><td>村委会意见</td><td>以上情况属实 特此证明</td><td></td><td>负责人签名：法伟 2024年6月1日</td><td></td><td></td></tr></table></body></html>\n\n"
#     # 示例配置
#     llm = LLM(config)
#     result = llm.process(ocr_text)
#     if result:
#         print("提取结果：", result)
#     else:
#         print("未成功提取关键信息")

import json
import logging
import time
from openai import OpenAI


class LLM:
    def __init__(self, config):
        """初始化LLM"""
        self.key = ['当事人', '图斑编号', '建筑层数', '占地面积']
        self.service_url = config.get("llm_config", {}).get("service_url")
        self.model = config.get("llm_config", {}).get("model", "QwQ-32B")
        self.api_key = "EMPTY"  # 使用空字符串或任意值，因为 vLLM 不需要 API key
        self.prompt = []

    def init_client(self):
        """初始化OpenAI客户端"""
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.service_url,
        )
        return client

    def init_prompt(self):
        """初始化对话内容"""
        task_description = """你的任务是从OCR文字识别结果中提取指定的关键信息。OCR结果用```包围，关键信息用[]包围。需要注意OCR结果可能存在识别问题，需结合上下文语义判断。
                            返回结果使用json格式，key为指定的关键信息，value为提取结果。若无对应key，value设为“未找到相关信息”。
                            请只输出json格式结果!,简化思考过程,不需要过度思考
                            """
        task_response = "好的，我会根据您提供的OCR结果提取关键信息并以JSON格式返回。"

        self.add_dialog(task_description, task_response)

    def add_dialog(self, user_content, bot_content):
        """添加对话内容"""
        self.prompt.append({"role": "user", "content": user_content})
        self.prompt.append({"role": "assistant", "content": bot_content})

    def eb_pred(self, max_retries=5, delay=3):
        """调用模型"""
        client = self.init_client()
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=self.prompt,
                    temperature=0.0,
                    top_p=1.0,
                    max_tokens=1024,
                    extra_body={
                        "repetition_penalty": 1.05,
                    },
                )
                response_data = response.choices[0].message.content
                return response_data
            except Exception as e:
                logging.error(f"尝试 {attempt + 1} 次,失败: {e}")
                if attempt < max_retries - 1:
                    logging.info(f"在 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    logging.error("达到最大重试次数。")
                    raise

    # 数据后处理
    @staticmethod
    def _post_process(response_data):
        try:
            logging.debug(f"原始响应数据: {response_data}")
            # 从 </think> 之后开始提取内容
            json_start = response_data.find("</think>") + len("</think>")
            if json_start != -1:
                # 提取 </think> 之后的内容
                json_content = response_data[json_start:].strip()
                # 去除多余的 Markdown 格式（三个```）
                json_content = json_content.strip("```")
                # 去除多余的前缀（如 "json"）
                json_content = json_content.strip("json").strip()
                # 验证返回结果是否为 JSON 格式
                logging.debug(f"解析后的 JSON 内容: {json_content}")
                result = json.loads(json_content)
                # return json.dumps(result, ensure_ascii=False, indent=4)
                # 返回字典格式
                return result
            else:
                logging.error("未找到 </think> 标记，无法提取 JSON 内容")
        except json.JSONDecodeError:
            logging.error("返回结果不是有效的 JSON 格式")
            return None

    def process(self, ocr_text):
        """开始对话并提取关键信息"""
        self.init_prompt()
        # TODO:文本长度分段处理
        # print(f"输入文本长度{len(ocr_text)}")
        prompt = f"""从以下OCR文字中提取关键信息：
                    OCR文字：```{ocr_text}```
                    要抽取的关键信息：{self.key}。所有值均唯一,不能存在多个；特别是当事人只有一个当事人,不存在多个人；建筑层数和占地面积是数值，不需要加单位。
                    在返回结果时使用json格式，包含多个key-value对，key值为我指定的关键信息值唯一，value值为所抽取的结果
                    如果认为OCR识别结果中没有关键信息key，则将value赋值为“None”。请只输出json格式的结果，不要包含其它多余文字！
                    """
        self.add_dialog(prompt, "")
        response_data = self.eb_pred()

        if response_data:
            results = self._post_process(response_data)
            return results
        else:
            return None



if __name__ == "__main__":
    # 加载配置文件
    from utils.utils import load_config
    config = load_config()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # 示例 OCR 结果
    ocr_text = "\n\n<html><body><table><tr><td>图斑号</td><td colspan=\"5\">HZJGZW202401-441322122510Z0006</td></tr><tr><td>当事人姓名（附 户口本）</td><td>张伟东、张利明 张群光、张主光</td><td>家庭成员（附 户口本）</td><td colspan=\"3\"></td></tr><tr><td>占地面积</td><td>408.05M</td><td>建筑面积</td><td colspan=\"3\">层数 408.05M</td></tr><tr><td>建设时间 （年／月）</td><td>2023.10</td><td>坐落位置</td><td colspan=\"3\">杨村镇水华寨村</td></tr><tr><td>建筑性质</td><td>永久口临时</td><td>建筑类型</td><td colspan=\"3\">新建口加建口拆旧建新</td></tr><tr><td colspan=\"3\">是否符合“一户一宅”</td><td colspan=\"3\">是 口否</td></tr><tr><td colspan=\"3\">是否本村村民自建自住自用</td><td colspan=\"3\">是 口否</td></tr><tr><td>变化图斑简要说明</td><td colspan=\"5\">惠龙高速拆迁户，村内无其他住房，急需建房满足日常居住。</td></tr><tr><td>村委会意见</td><td>以上情况属实 特此证明</td><td></td><td>负责人签名：法伟 2024年6月1日</td><td></td><td></td></tr></table></body></html>\n\n"
    # 示例配置
    llm = LLM(config)
    result = llm.process(ocr_text)
    if result:
        print("提取结果：", result)
    else:
        print("未成功提取关键信息")