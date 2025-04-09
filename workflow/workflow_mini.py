# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: workflow_mini.py
@Time    : 2025/3/21 下午4:07
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 只使用VLM模型单条流
@Usage   :
"""
import logging
from models import VLM
from workflow import Base_Workflow

class Workflow(Base_Workflow):
    def init_models(self):
        # 加载模型
        try:
            vlm = VLM(self.config)
            logging.info("所有模型初始化成功！")
            return vlm
        except Exception as e:
            logging.error(f"模型初始化失败！错误信息：{str(e)}")

    def start_task(self, task_queue):
        """
        开始任务
        :param task_queue: 任务队列
        :return:
        """
        logging.getLogger("httpx").setLevel(logging.WARNING)  # 如果使用httpx
        for task_id, input_paths in task_queue.items():
            # TODO: 每个任务需要重新初始化模型，因为每个任务是一个独立的对话
            vlm = self.init_models()

            # 更新字典id, 并初始化其它值
            self.results_dict = {
                "id": task_id,
                "公章": False,
                "当事人": None,
                "图斑编号": None,
                "建筑层数": None,
                "占地面积": None,
                "建筑面积": None
            }

            vlm_results = [] # 存储vlm结果
            for input_path in input_paths:
                try:
                    # 处理文件
                    vlm_result = vlm.process(input_path)
                    vlm_results.append(vlm_result)
                except Exception as e:
                    logging.error(f"任务 {task_id} 中的文件 {input_path} 处理失败！错误信息：{str(e)}")

            # 开始对结果进行后处理合并
            logging.info(f"开始对 {task_id} 结果进行后处理！")
            self._many_results(vlm_results)

        return self.results_dict
