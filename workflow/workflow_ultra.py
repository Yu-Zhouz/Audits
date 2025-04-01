# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: workflow_ultra.py.py
@Time    : 2025/3/23 下午8:28
@Author  : ZhouFei
@Email   : zhoufei.net@outlook.com
@Desc    : 使用VLM和MinerU的多模态和文本的双工作流
@Usage   :
"""
import logging
from models import MinerUOCR, SealExtractor, VLM
from workflow.workflow import Base_Workflow


class Workflow(Base_Workflow):
    def init_models(self):
        # 加载模型
        try:
            mineru_ocr = MinerUOCR(self.config)
            seal_extractor = SealExtractor(self.config)
            logging.info("所有模型初始化成功！")
            return mineru_ocr, seal_extractor
        except Exception as e:
            logging.error(f"模型初始化失败！错误信息：{str(e)}")

    # 开始任务
    def start_task(self, task_queue, max_empty_count=2):
        """
        开始任务
        :param task_queue: 任务队列
        :return:
        """
        results_list = []
        # logging.info("开始处理任务！")
        logging.getLogger("httpx").setLevel(logging.WARNING)  # 如果使用httpx
        for task_id, input_paths in task_queue.items():
            # TODO: 每个任务需要重新初始化模型，因为每个任务是一个独立的对话
            miner_ocr, seal_extractor = self.init_models()
            # logging.info(f"开始处理任务{task_id}！")

            # 更新字典id, 并初始化其它值
            self.results_dict = {
                "id": task_id,
                "公章": False,
                "当事人": None,
                "图斑编号": None,
                "建筑层数": None,
                "占地面积": None
            }
            seal_results, miner_results, paddle_results, vlm_results, llm_m_results, llm_p_results = [], [], [], [], [], []  # 识别结果
            vlm = VLM(self.config)
            # TODO: 添加对文件名称列表的提取
            vlm.process_file_list(input_paths)
            for input_path in input_paths:
                try:
                    # 处理文件
                    vlm_result = vlm.process(input_path)
                    vlm_results.append(vlm_result)
                except Exception as e:
                    logging.error(f"任务 {task_id} 中的文件 {input_path} 在第一阶段中处理失败！错误信息：{str(e)}")

            # 开始对结果进行后处理合并
            logging.info(f"开始对 {task_id} 结果进行后处理！")
            self._many_results(vlm_results)
            empty_count = self.post_process(seal_results, vlm_results)
            results_vlm = self.results_dict
            if empty_count >= self.max_empty_count:
                # 防止上下文过长,每次重新初始化一个VLM模型
                vlm_m = VLM(self.config)
                for input_path in input_paths:
                    try:
                        # 识别印章
                        logging.info(f"开始对任务 {task_id} 中的文件 {input_path} 进行印章识别...")
                        seal_result = seal_extractor.process(input_path)
                        if seal_result:
                            seal_results.append(seal_result)

                        # minerUOCR 识别
                        logging.info(f"开始对任务 {task_id} 中的文件 {input_path} 进行minerUOCR识别...")
                        miner_text = miner_ocr.process(input_path, llm_text=True)
                        if miner_text:
                            miner_results.append(miner_text)

                            # vlm 提取minerUOCR识别结果
                            logging.info(f"开始对任务 {task_id} 中的文件 {input_path} 进行vlm提取...")
                            llm_m_result = vlm_m.process_text(miner_text)
                            if llm_m_result:
                                llm_m_results.append(llm_m_result)
                            else:
                                logging.error(f"任务 {task_id}  在第二阶段的vlm中处理失败！")

                    except Exception as e:
                        logging.error(f"任务 {task_id} 中的文件 {input_path} 处理失败！错误信息：{str(e)}")

                # 开始对结果进行后处理合并
                logging.info(f"开始对 {task_id} 结果进行后处理！")
                self.post_process(seal_results, llm_m_results)
                results_miner = self.results_dict
                results = self._mergers_comparison(results_vlm, results_miner)
                # 将结果添加到字典results中
                self.results_dict.update(results)

            # logging.info("开始保存结果！")
            # 将结果添加到列表results_list中
            # results_list.append(self.results_dict)

        return self.results_dict


if __name__ == "__main__":
    from utils.utils import load_config
    config = load_config()
    workflow = Workflow(config)
    task_queue = {
        "task_id": ["./data/input/1554522.png", "./data/input/2558636.pdf"],
        "0000002": ["./data/input/1554523", ]
    }
    workflow.start_task(task_queue)