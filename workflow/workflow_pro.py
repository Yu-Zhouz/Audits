# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: workflow_pro.py
@Time    : 2025/3/18 下午2:26
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 使用LLM和MinerU和PaddleX的图像和文本双工作流
@Usage   :
"""
import copy
import logging
from models import LLM, MinerUOCR, PaddleOCR, SealExtractor
from workflow import Base_Workflow


class Workflow(Base_Workflow):
    def init_models(self):
        # 加载模型
        try:
            mineru_ocr = MinerUOCR(self.config)
            paddle_ocr = PaddleOCR(self.config)
            seal_extractor = SealExtractor(self.config)
            logging.info("所有模型初始化成功！")
            return mineru_ocr, paddle_ocr, seal_extractor
        except Exception as e:
            logging.error(f"模型初始化失败！错误信息：{str(e)}")

    # 开始任务
    def start_task(self, task_queue):
        """
        开始任务
        :param task_queue: 任务队列
        :return:
        """
        for task_id, input_paths in task_queue.items():
            # TODO: 每个任务需要重新初始化模型，因为每个任务是一个独立的对话
            miner_ocr, paddle_ocr, seal_extractor = self.init_models()

            # 更新字典id, 并初始化其它值
            self.results_dict = {
                "id": task_id,
                "公章": False,
                "当事人": None,
                "图斑编号": None,
                "建筑层数": None,
                "占地面积": None
            }
            seal_results, miner_results, paddle_results, llm_m_results, llm_p_results = [], [], [], [], []  # 识别结果
            for input_path in input_paths:
                # 防止上下文过长,每次重新初始化一个LLM模型
                llm_m = LLM(self.config)
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

                        # llm 提取minerUOCR识别结果
                        logging.info(f"开始对任务 {task_id} 中的文件 {input_path} 进行llm提取...")
                        llm_m_result = llm_m.process(miner_text)
                        if llm_m_result:
                            llm_m_results.append(llm_m_result)
                        else:
                            logging.error(f"任务 {task_id}  在第一阶段的llm中处理失败！")

                except Exception as e:
                    logging.error(f"任务 {task_id} 中的文件 {input_path} 处理失败！错误信息：{str(e)}")

            # 开始对结果进行后处理合并
            logging.info(f"开始对 {task_id} 结果进行后处理！")
            empty_count = self.post_process(seal_results, llm_m_results)
            results_miner = copy.deepcopy(self.results_dict)
            if empty_count > self.max_empty_count:
                logging.info(f"任务 {task_id} 中空字段数量大于 {self.max_empty_count} ，使用PaddlexOCR识别！")
                for input_path in input_paths:
                    llm_p = LLM(self.config)
                    try:
                        # paddleOCR 识别
                        logging.info(f"开始对任务 {task_id} 中的文件 {input_path} 进行paddleOCR识别...")
                        paddle_text = paddle_ocr.process(input_path)
                        if paddle_text:
                            paddle_results.append(paddle_text)

                            # llm 提取paddleOCR识别结果
                            logging.info(f"开始对任务 {task_id} 中的文件 {input_path} 进行llm提取...")
                            llm_p_result = llm_p.process(paddle_text)
                            if llm_p_result:
                                llm_p_results.append(llm_p_result)
                            else:
                                logging.error(f"任务 {task_id} 在第二阶段的llm中处理失败！")

                    except Exception as e:
                        logging.error(f"任务 {task_id} 中的文件 {input_path} 处理失败！错误信息：{str(e)}")

                logging.info(f"开始对 {task_id} 结果进行后处理！")
                self.post_process(seal_results, llm_p_results)
                results_paddle = copy.deepcopy(self.results_dict)
                results = self._mergers_comparison(results_miner, results_paddle)
                # 更新空值的结果
                for key, value in results.items():
                    if self.results_dict[key] is None or self.results_dict[key] == "null":
                        self.results_dict[key] = value
            # logging.info("开始保存结果！")
            # 将结果添加到列表results_list中
            # results_list.append(self.results_dict)

        return self.results_dict


if __name__ == "__main__":
    from utils.utils import load_config
    config = load_config()
    workflow = Workflow(config)
    # # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    task_queue = {
        "1162708535117611009": ["/sxs/zhoufei/Audits/Audits/data/input/1162708535117611009/1698716638425_1698716632455.jpg", "/sxs/zhoufei/Audits/Audits/data/input/1162708535117611009/9069f4ccc594cf31e57f8a8c48c8648.jpg"],
    }
    workflow.start_task(task_queue)