# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: single_processor.py
@Time    : 2025/3/31 下午6:36
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 单ID或ID列表处理器
@Usage   :
"""
import logging
import os
import shutil
import threading
import time
from datetime import datetime
from utils import setup_logging
from database import get_db, DataDownloader
from workflow import get_workflow


class ParallelProcessor:
    def __init__(self, config, task_id_list=None, delete=True):

        self.config = config
        self.task_id_list = task_id_list
        self.downloader = DataDownloader(config)
        self.workflow = get_workflow(config)
        self.data_dir = config.get("data_config", {}).get("data_dir")  # 数据目录
        self.logger = setup_logging(config, log_name='audits_sin')  # 日志记录器
        self.task_queue = self.downloader.get_task_queue()  # 使用 DataDownloader 的任务队列
        self.running = True
        self.delete = delete  # 是否删除下载的文件
        self.scan_interval = 3
        self.download_completed = False  # 新增标志，表示下载是否完成

    def download_task(self):
        """下载指定id列表任务"""
        logger = self.logger
        logger.info("下载线程已启动")
        try:
            logging.info(f"开始下载数据...")
            self.downloader.download(self.task_id_list)
            # 下载完成后设置标志
            self.download_completed = True
            logger.info("所有任务下载完成，下载线程将退出")
        except Exception as e:
            logger.error(f"下载任务时出错: {str(e)}")

        # 不再需要循环，下载完成后线程自然结束

    def process_task(self):
        """处理任务队列中的任务"""
        logger = self.logger
        logger.info("处理线程已启动")
        # 为每个线程创建独立的数据库连接
        store_audit_result, _, _ = get_db(self.config)
        while self.running:
            if not self.task_queue.empty():
                try:
                    # 打印队列第一条数据
                    # logger.info(f"队列中第一条数据: {self.task_queue.queue[0]}")
                    # 获取一个任务
                    time_start = time.time()
                    task_id, file_paths = self.task_queue.get()
                    logging.info(f"开始处理任务 {task_id}")
                    # 提取
                    results = self.workflow.start_task({task_id: file_paths})
                    # 保存结果到数据库
                    time_end = time.time()
                    if results.get('id') is not None:
                        store_audit_result(self.config, results)
                        logging.info(f"任务 {task_id} 的结果已保存到数据库, 用时 {time_end - time_start}")
                    else:
                        logging.warning(f"任务 {task_id} 没有返回结果")
                    # 标记任务完成
                    self.downloader.task_done()
                    # 删除数据
                    if self.delete:
                        self.delete_data(task_id)
                except Exception as e:
                    logging.error(f"处理任务时出错: {str(e)}")
                    # 如果处理失败，将任务重新放回队列
                    self.downloader.add_task(task_id, file_paths)
            else:
                # 如果队列为空且下载完成，等待一小段时间确保没有新任务，然后退出
                if self.download_completed:
                    logging.info("队列为空且下载已完成，等待确认...")
                    time.sleep(2)  # 短暂等待，确保没有新任务进入队列
                    if self.task_queue.empty():
                        logging.info("所有任务已处理完毕，处理线程将退出")
                        break
                # 如果队列为空但下载未完成，等待新任务
                logging.info("队列为空，等待中...")
                time.sleep(self.scan_interval)

    def start(self):
        # 启动下载线程
        download_thread = threading.Thread(target=self.download_task, daemon=True)
        download_thread.start()

        # 启动多个处理线程
        num_processing_threads = 1  # 可以根据需要调整线程数量
        processing_threads = []
        for _ in range(num_processing_threads):
            thread = threading.Thread(target=self.process_task, daemon=True)
            thread.start()
            processing_threads.append(thread)

        # 主线程等待所有任务完成
        try:
            # 等待下载线程完成
            download_thread.join()
            logging.info("下载线程已完成")

            # 等待处理线程完成
            for thread in processing_threads:
                thread.join()
            logging.info("所有处理线程已完成")

            logging.info("所有任务已完成，程序正常退出")
        except KeyboardInterrupt:
            self.running = False
            logging.info("接收到中断信号，程序将停止")
            download_thread.join()
            for thread in processing_threads:
                thread.join()
            logging.info("程序已停止")

    # 删除指定ID下的文件
    def delete_data(self, task_id: str):
        """删除数据目录self.data_dir下的task_id文件夹"""
        try:
            shutil.rmtree(os.path.join(self.data_dir, task_id))
            logging.info(
                f"任务 {task_id} 处理完成，成功从队列中移除，删除数据目录 {os.path.join(self.data_dir, task_id)} 成功")
        except Exception as e:
            logging.error(f"删除数据目录 {os.path.join(self.data_dir, task_id)} 失败: {str(e)}")


if __name__ == "__main__":
    from utils import load_config, setup_logging

    # 假设你有一个配置文件 config.py
    config = load_config()
    task_id_list = ["1230441438601281536"]
    processor = ParallelProcessor(config, task_id_list)
    processor.start()













'''import logging
import threading
import time
from datetime import datetime

from database import DataDownloader
from database.audit_results import AuditDatabase
from workflow import get_workflow

class ParallelProcessor:
    def __init__(self, config, process_initial_data=False):
        self.config = config
        self.downloader = DataDownloader(config)
        self.workflow = get_workflow(config)
        self.database = AuditDatabase(config)
        self.task_queue = {}
        self.last_check_time = None
        self.running = True
        self.process_initial_data = process_initial_data  # 是否处理初始数据

    def download_task(self):
        """定期扫描数据库并下载新增任务"""
        while self.running:
            try:
                # 如果需要处理初始数据，并且这是第一次运行，则不传入 last_check_time
                logging.info(f"上次檢查时间: {self.last_check_time}, 当前时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 开始检查...")
                if self.process_initial_data and self.last_check_time is None:
                    logging.info("正在处理初始数据...")
                    max_create_time, new_tasks = self.downloader.download()
                    logging.info(f"发现新数据，更新时间戳: {max_create_time}")
                    self.process_initial_data = False  # 只处理一次初始数据
                else:
                    max_create_time, new_tasks = self.downloader.download(self.last_check_time)
                    logging.info(f"发现新数据，更新时间戳: {max_create_time}")
                if new_tasks:
                    # 更新最后检查时间
                    if max_create_time is not None:
                        self.last_check_time = max_create_time
                    # 将新任务添加到任务队列
                    self.task_queue.update(new_tasks)
                    logging.info(f"新增任务已添加到队列，当前队列大小: {len(self.task_queue)}")
            except Exception as e:
                logging.error(f"下载任务时出错: {str(e)}")
            # 定时扫描，例如每分钟扫描一次
            time.sleep(30)
            logging.info(f"下次检查将在30秒后...")

    def process_task(self):
        """处理任务队列中的任务"""
        while self.running:
            if self.task_queue:
                try:
                    # 获取一个任务
                    task_id, file_paths = self.task_queue.popitem()
                    logging.info(f"开始处理任务 {task_id}")

                    # 模型识别
                    results = self.workflow.start_task({task_id: file_paths})

                    # 保存结果到数据库
                    if results:
                        self.database.insert_data(results)
                        logging.info(f"任务 {task_id} 的结果已保存到数据库")
                    else:
                        logging.warning(f"任务 {task_id} 没有返回结果")
                except Exception as e:
                    logging.error(f"处理任务时出错: {str(e)}")
                    # 如果处理失败，将任务重新放回队列
                    self.task_queue[task_id] = file_paths
            else:
                # 如果队列为空，等待一段时间
                time.sleep(1)

    def start(self):
        # 启动下载线程
        download_thread = threading.Thread(target=self.download_task, daemon=True)
        download_thread.start()

        # TODO:启动多个处理线程
        num_processing_threads = 1  # 可以根据需要调整线程数量
        processing_threads = []
        for _ in range(num_processing_threads):
            thread = threading.Thread(target=self.process_task, daemon=True)
            thread.start()
            processing_threads.append(thread)

        # 主线程可以在这里执行其他任务，或者等待中断信号
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            download_thread.join()
            for thread in processing_threads:
                thread.join()
            self.database.close()
            logging.info("程序已停止")


if __name__ == "__main__":
    from utils import load_config, setup_logging
    # 假设你有一个配置文件 config.py
    config = load_config()
    # 初始化日志
    setup_logging(config, api=False)

    processor = ParallelProcessor(config, process_initial_data=True)
    processor.start()
'''