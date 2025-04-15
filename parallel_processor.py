# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: parallel_processor.py.py
@Time    : 2025/3/24 下午6:03
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 
@Usage   :
"""
import logging
import os
import shutil
import threading
import time
from datetime import datetime
from utils import setup_logging, get_scan_interval
from database import get_db, DataDownloader
from workflow import get_workflow

class ParallelProcessor:
    def __init__(self, config, process_initial_data=False, delete=True):

        self.config = config
        self.downloader = DataDownloader(self.config)
        self.workflow = get_workflow(self.config)
        self.data_dir = self.config.get("data_config", {}).get("data_dir")  # 数据目录
        self.timestamp_file = self.config.get("workflow_config", {}).get("last_check_time")  # 保存时间戳的文件名
        self.logger = setup_logging(self.config, log_name='audits')  # 日志记录器
        self.task_queue = self.downloader.get_task_queue()  # 使用 DataDownloader 的任务队列
        self.scan_interval = get_scan_interval(self.config)  # 使用时间扫描函数获取当前扫描间隔
        self.last_check_time = None
        self.running = True
        self.process_initial_data = process_initial_data  # 是否处理初始数据
        self.delete = delete  # 是否删除下载的文件

        # 在初始化时从文件读取时间戳
        self.load_last_check_time()

    def load_last_check_time(self):
        """从文件中加载上次检查时间"""
        if os.path.exists(self.timestamp_file):
            with open(self.timestamp_file, "r") as file:
                content = file.read().strip()
                if content:
                    self.last_check_time = content
                    logging.info(f"从文件加载上次检查时间: {self.last_check_time}")
                else:
                    self.last_check_time = None
                    logging.info("时间戳文件为空，设置上次检查时间为 None")
        else:
            self.last_check_time = None
            logging.info("时间戳文件不存在，设置上次检查时间为 None")

    def save_last_check_time(self, timestamp):
        """将上次检查时间保存到文件"""
        # 确保写入文件的是字符串格式的时间戳
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if isinstance(timestamp, datetime) else str(timestamp)
        with open(self.timestamp_file, "w") as file:
            file.write(timestamp_str)
        logging.info(f"保存时间戳到文件: {timestamp_str}")

    def download_task(self):
        """定期扫描数据库并下载新增任务"""
        logger = self.logger
        logger.info("下载线程已启动")
        while self.running:
            try:
                logging.info(
                    f"上次检查的时间戳: {self.last_check_time}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 重新开始检查...")
                # 判断条件
                if self.process_initial_data and self.last_check_time is None:
                    logging.info("正在处理初始数据...")
                    max_create_time = self.downloader.start_download(self.last_check_time)
                    if max_create_time is not None:
                        logging.info(f"发现新数据，更新时间戳: {max_create_time}")
                        self.last_check_time = max_create_time
                        # 保存时间戳到文件
                        self.save_last_check_time(max_create_time)
                    else:
                        logging.warning(f"初始数据处理未返回有效的时间戳, 当前时间戳 {self.last_check_time}")
                    self.process_initial_data = False  # 只处理一次初始数据
                else:
                    max_create_time = self.downloader.start_download(self.last_check_time)
                    if max_create_time != self.last_check_time:
                        logging.info(f"发现新数据，更新时间戳: {max_create_time}")
                        self.last_check_time = max_create_time
                        # 保存时间戳到文件
                        self.save_last_check_time(max_create_time)
                    else:
                        logging.info(f"没有新增数据，时间戳 {max_create_time} 保持不变，等待下一次检查...")
            except Exception as e:
                logging.error(f"下载任务时出错: {str(e)}")
            # 使用时间扫描函数获取当前扫描间隔
            self.scan_interval = get_scan_interval(self.config)  # 动态更新扫描间隔
            logging.info(f"下次检查将在 {self.scan_interval} 秒后...")
            time.sleep(self.scan_interval)

    def process_task(self):
        """处理任务队列中的任务"""
        logger = self.logger
        logger.info("处理线程已启动")
        # 为每个线程创建独立的数据库连接
        store_audit_result, _, _ = get_db(self.config)
        first_scan = True  # 添加一个标志，用于判断是否是第一次扫描
        while self.running:
            if not self.task_queue.empty():
                try:
                    # 打印队列第一条数据
                    # logger.info(f"队列中第一条数据: {self.task_queue.queue[0]}")
                    # 获取一个任务
                    time_start = time.time()
                    task_id, file_paths = self.task_queue.get()
                    logging.info(f"开始处理任务 {task_id}， 队列中剩余任务数: {self.task_queue.qsize()}")
                    # 识别
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
                    logging.error(f"处理任务 {task_id} 时出错: {str(e)}")
                    # 如果处理失败，将任务重新放回队列
                    self.downloader.add_task(task_id, file_paths)
            else:
                # 如果队列为空，等待一段时间
                if first_scan:
                    wait_time = 3  # 第一次扫描等待10秒
                    first_scan = False  # 标志设置为False，后续不再使用3秒等待
                else:
                    wait_time = self.scan_interval // 2
                logging.info(f"队列为空，等待 {wait_time} 秒...")
                time.sleep(wait_time)
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

        # 主线程可以在这里执行其他任务，或者等待中断信号
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            download_thread.join()
            for thread in processing_threads:
                thread.join()
            logging.info("程序已停止")

    # 删除指定ID下的文件
    def delete_data(self, task_id: str):
        """删除数据目录self.data_dir下的task_id文件夹"""
        try:
            shutil.rmtree(os.path.join(self.data_dir, task_id))
            logging.info(f"任务 {task_id} 处理完成，成功从队列中移除，删除数据目录 {os.path.join(self.data_dir, task_id)} 成功")
        except Exception as e:
            logging.error(f"删除数据目录 {os.path.join(self.data_dir, task_id)} 失败: {str(e)}")


if __name__ == "__main__":
    from utils import load_config, setup_logging
    # 假设你有一个配置文件 config.py
    config = load_config()

    processor = ParallelProcessor(config, process_initial_data=True)
    processor.start()
