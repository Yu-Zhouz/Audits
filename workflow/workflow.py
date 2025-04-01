# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: workflow.py
@Time    : 2025/3/21 下午4:14
@Author  : ZhouFei
@Email   : zhoufei.net@outlook.com
@Desc    : Workflow基类
@Usage   :
"""
from collections import Counter

from fontTools.qu2cu.qu2cu import List
from sympy import Dict


class Base_Workflow:
    def __init__(self, config):
        self.config = config
        self.max_empty_count = self.config.get("workflow_config", {}).get("max_empty_count", 2)
        self.results_dict = {
                "id": None,
                "公章": False,
                "当事人": None,
                "图斑编号": None,
                "建筑层数": None,
                "占地面积": None
            }

    def init_models(self):
        pass

    def _many_results(self, results):
        # 提取 results 结果中出现次数最多的值
        llm_field_values = {field: [] for field in self.results_dict.keys() if field != "公章"}
        # 提取 results 结果中出现次数最多的值
        for item in results:
            if item is not None:
                for field, value in item.items():
                    if field in llm_field_values and value is not None and value != "null":
                        llm_field_values[field].append(value)
                    if field == "公章":
                        if value is True:
                            self.results_dict["公章"] = True
            else:
                # 公章设置为Flase, 其余值为None
                self.results_dict["公章"] = False
                for field in self.results_dict.keys():
                    if field != "公章":
                        self.results_dict[field] = None

        # 选择每个字段出现次数最多的值
        for field, values in llm_field_values.items():
            if values:
                most_common_value = Counter(values).most_common(1)[0][0]  # 取出现次数最多的值
                self.results_dict[field] = most_common_value


    # 开始对结果后处理
    def post_process(self, seal_results: List[List[Dict]], llm_results: List[Dict]) -> int:
        """
        后处理函数，合并印章识别结果和 LLM 结果。
        :param seal_results: 印章识别结果（二维列表）
        :param llm_results: LLM 结果（一维列表）
        :return: 合并后的结果和空字段的数量
        """

        # 判断印章是否存在
        if seal_results and any(seal_results):  # 如果有印章识别结果
            self.results_dict["公章"] = True
        else:
            self.results_dict["公章"] = False

        # 提取 LLM 结果中出现次数最多的值
        if llm_results:
            self._many_results(llm_results)
            # 如果有值为null则修改为None
            for field, value in self.results_dict.items():
                if value == "null":  # 检查是否为 null 或 None
                    self.results_dict[field] = None
        else:
            # 除公章和id以外全部为None
            for field in self.results_dict.keys():
                if field != "公章" and field != "id":
                    self.results_dict[field] = None

        # 统计空字段的数量
        empty_count = sum(1 for value in self.results_dict.values() if value is None or value == "")

        return empty_count

    @staticmethod
    def _mergers_comparison(results_worn, results_new):
        """比较结果并合并"""
        results = {}  # 初始化一个空字典用于存储合并后的结果
        for field in results_worn.keys():  # 遍历 results_worn 的所有键
            # 如果 results_new 包含该字段且值有效（非 None 且不等于 "null"）
            if field in results_new and results_new[field] is not None and results_new[field] != "null":
                # 检查 results_worn 中对应字段的值是否为空或无效
                if results_worn[field] is None or results_worn[field] == "null":
                    results[field] = results_new[field]  # 使用 results_new 的值
                else:
                    results[field] = results_worn[field]  # 保留 results_worn 的值
            else:
                results[field] = results_worn[field]  # 直接使用 results_worn 的值

        return results  # 返回合并后的结果字典
    # @staticmethod
    # def _mergers_comparison(results_worn, results_new):
    #     """比较结果并合并"""
    #     results = {}
    #     for field in results_worn.keys():
    #         if field in results_new and results_new[field] is not None and results_new[field] != "null":
    #             if results_new[field] != results_worn[field]:
    #                 results[field] = results_new[field]  # 优先取results_new的值
    #             else:
    #                 results[field] = results_worn[field]
    #         else:
    #             results[field] = results_worn[field]
    #
    #     return results

    def start_task(self, task_queue):
        pass
