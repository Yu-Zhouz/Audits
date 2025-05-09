# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: workflow.py
@Time    : 2025/3/21 下午4:14
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : Workflow基类
@Usage   :
"""
from collections import Counter

from fontTools.qu2cu.qu2cu import List
from sympy import Dict

from models import VLM


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
                "占地面积": None,
                "建筑面积": None
            }

    def init_models(self):
        pass

    def _update_building_area(self):
        """对占地面积和建筑面积进行判断更新"""
        occupied_area = self.results_dict['占地面积']
        building_levels = self.results_dict['建筑层数']

        # 检查是否有足够的数据计算建筑面积
        if (isinstance(occupied_area, (int, float)) and
            isinstance(building_levels, (int, float)) and
            occupied_area is not None and building_levels is not None and
            building_levels > 0):

            # 计算建筑面积
            self.results_dict['建筑面积'] = occupied_area * building_levels
        else:
            # 如果条件不足，则将建筑面积设为 None
            self.results_dict['建筑面积'] = None

    def _merge_results(self, results):
        vlm = VLM(self.config)
        # 使用列表推导式提取当事人字段
        names_merge = [item.get("当事人") for item in results if
                       item.get("当事人") is not None and item.get("当事人") != '']

        # 对每个字符串进行分割，假设公司名称之间用逗号分隔
        names_split = []
        for name in names_merge:
            names_split.extend(name.split(', '))

        # 去除空字符串并去重
        names_split = [name.strip() for name in names_split if name.strip()]
        name_counts = Counter(names_split)
        # 按照出现次数降序排序
        names = [name for name, count in name_counts.most_common()]
        if len(names) >= 3:
            names = names[:3]
        name_type = vlm.judge_name_type(names)

        if name_type == 1:
            # 对多材料企业信息的处理, 要求当事人字段结果合并，用,分隔，其余值的处理与else处理一致
            # 合并当事人字段
            merged_names = ", ".join(names) if names else None
            self.results_dict["当事人"] = str(merged_names) if merged_names else None  # 明确类型转换

            # 处理其他字段
            llm_field_values = {field: [] for field in self.results_dict.keys() if
                                field != "公章" and field != "当事人"}

            for item in results:
                if item is not None:
                    for field, value in item.items():
                        if field in llm_field_values:
                            # 如果值是列表，将其转换为字符串
                            if isinstance(value, list):
                                value = ", ".join(map(str, value))
                            if value is not None and value != "null" and value != '':
                                # 增加对图斑编号的判断和长度判断
                                if field == "图斑编号" and (
                                        not value.startswith("HZJGZW") or not (30 <= len(value) <= 33)):
                                    continue
                                llm_field_values[field].append(value)
                        if field == "公章":
                            if value is True:
                                self.results_dict["公章"] = True
                else:
                    # 公章设置为False, 其余值为None
                    self.results_dict["公章"] = False
                    for field in self.results_dict.keys():
                        if field != "公章":
                            self.results_dict[field] = None

            # 选择每个字段出现次数最多的值
            for field, values in llm_field_values.items():
                if values:
                    most_common_value = Counter(values).most_common(1)[0][0]  # 取出现次数最多的值
                    self.results_dict[field] = most_common_value
        else:
            # 提取 results 结果中出现次数最多的值
            llm_field_values = {field: [] for field in self.results_dict.keys() if field != "公章"}

            for item in results:
                if item is not None:
                    for field, value in item.items():
                        if field in llm_field_values:
                            # 如果值是列表，将其转换为字符串
                            if isinstance(value, list):
                                value = ", ".join(map(str, value))
                            if value is not None and value != "null" and value != '':
                                # 增加对图斑编号的判断和长度判断,
                                if field == "图斑编号" and (not value.startswith("HZJGZW") or not (30 <= len(value) <= 33)):
                                    continue
                                llm_field_values[field].append(value)
                        if field == "公章":
                            if value is True:
                                self.results_dict["公章"] = True
                else:
                    # 公章设置为False, 其余值为None
                    self.results_dict["公章"] = False
                    for field in self.results_dict.keys():
                        if field != "公章":
                            self.results_dict[field] = None

            # 选择每个字段出现次数最多的值
            for field, values in llm_field_values.items():
                if values:
                    most_common_value = Counter(values).most_common(1)[0][0]  # 取出现次数最多的值
                    self.results_dict[field] = most_common_value

        # 根据建筑面积和占地面积之间的关系吗，更新建筑面积
        if self.results_dict['占地面积'] is not None:
            if self.results_dict['建筑面积'] is None or self.results_dict['建筑面积'] <= self.results_dict['占地面积']:
                if self.results_dict['建筑层数'] is not None:
                    # 如果建筑层数有效，则重新计算建筑面积
                    self._update_building_area()
                else:
                    # 如果建筑层数无效，则将建筑面积设为 None
                    self.results_dict['建筑面积'] = None

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
            self._merge_results(llm_results)
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
        """比较结果并合并，对公章字段特殊处理"""
        results = {}  # 初始化一个空字典用于存储合并后的结果
        for field in results_worn.keys():  # 遍历 results_worn 的所有键
            # 特殊处理公章字段
            if field == '公章':
                # 如果任一字典中公章为True，则结果为True
                if (results_worn.get(field) is True) or (field in results_new and results_new.get(field) is True):
                    results[field] = True
                else:
                    results[field] = False
            # 处理其他字段
            elif field in results_new and results_new[field] is not None and results_new[field] != "null":
                # 检查 results_worn 中对应字段的值是否为空或无效
                if results_worn[field] is None or results_worn[field] == "null":
                    results[field] = results_new[field]  # 使用 results_new 的值
                else:
                    results[field] = results_worn[field]  # 保留 results_worn 的值
            else:
                results[field] = results_worn[field]  # 直接使用 results_worn 的值

        return results  # 返回合并后的结果字典

    def start_task(self, task_queue):
        pass
