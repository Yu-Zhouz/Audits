# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: db_downloader_mt.py.py
@Time    : 2025/3/24 上午9:56
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 数据库多线程下载类
@Usage   :
"""
import datetime
import threading
import time
import logging
import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import cx_Oracle
import queue


class DataDownloader:
    def __init__(self, config):
        self.config = config
        self.db_config = config.get("db_download_config", {})
        self.data_dir = config.get("data_config", {}).get("data_dir")
        self.check_dir_exist(self.data_dir)
        self.task_queue = queue.Queue()
        self.lock = threading.Lock()
        self.retries = self.db_config.get("retries", 3)
        self.num_threads = self.db_config.get("num_threads", 16)
        self.scan_interval = self.db_config.get("scan_interval", 300)   # 定义扫描时间
        self.connection = None  # 数据库
        self.cursor = None  # 游标
        self.download_threads = []  # 线程列表
        self.running = True
        self.processed_tasks = set()  # 已处理任务记录

    def connect_db(self):
        try:
            dsn = cx_Oracle.makedsn(self.db_config['host'], self.db_config['port'], self.db_config['sid'])
            self.connection = cx_Oracle.connect(self.db_config['user'], self.db_config['password'], dsn)
            self.cursor = self.connection.cursor()
            logging.info("数据库连接成功")
        except cx_Oracle.DatabaseError as e:
            logging.error(f"数据库连接失败: {str(e)}")
            self.reconnect_db()
        except Exception as e:
            logging.error(f"处理过程中发生错误: {str(e)}")
            self.reconnect_db()

    def reconnect_db(self):
        logging.info("尝试重新连接数据库...")
        for _ in range(self.retries):
            try:
                self.connect_db()
                if self.connection and self.cursor:
                    logging.info("数据库重新连接成功")
                    return
            except Exception as e:
                logging.error(f"重连失败: {str(e)}")
                time.sleep(5)
        logging.error("数据库重新连接失败，程序将退出")
        raise Exception("数据库重新连接失败")

    def check_dir_exist(self, dir_path: str):
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    def close_db(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logging.info("数据库连接已关闭")

    def download_file(self, file_url, file_path):
        session = requests.Session()
        retry_strategy = Retry(
            total=self.retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        attempt = 0
        while attempt < self.retries:
            try:
                response = session.get(file_url, stream=True, verify=False, timeout=(30, 120))
                response.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return True
            except Exception as e:
                attempt += 1
                logging.error(f"下载失败: {str(e)}，尝试 {attempt}/{self.retries}")
                if attempt >= self.retries:
                    logging.error(f"文件 {file_path} 下载失败，重试次数已用尽")
                    return False
                time.sleep(2)

    def process_record(self, row_dict):
        record_id = str(row_dict['ID'])
        sczzcl = row_dict['SCZZCL'] or '[]'
        raw_materials = json.loads(sczzcl)
        output_dir = os.path.join(self.data_dir, record_id)
        self.check_dir_exist(output_dir)

        file_paths = []
        time_start = time.time()
        for material in raw_materials:
            file_name = material['fileName']
            file_id = material['id']
            file_url = f'http://163.179.247.76:8086/ibps/components/upload/download.htm?downloadId={file_id}'
            file_path = os.path.join(output_dir, file_name)
            if self.download_file(file_url, file_path):
                file_paths.append(file_path)

        # TODO: 自定义排序键函数
        def sort_key(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                return 0, ext, file_path  # 图像文件优先
            elif ext == '.pdf':
                return 1, ext, file_path  # PDF 文件次之
            else:
                return 2, ext, file_path  # 其他文件最后

        # 对 file_paths 进行排序
        file_paths.sort(key=sort_key)

        time_end = time.time()
        if file_paths:
            with self.lock:
                if record_id not in self.processed_tasks:
                    logging.info(f"下载任务 {record_id} 已保存到 {output_dir}, 用时 {time_end - time_start}")
                    self.task_queue.put((record_id, file_paths))
                    self.processed_tasks.add(record_id)

    def get_latest_create_time(self):
        """获取数据库中所有记录的最晚时间戳"""
        try:
            if not self.connection or not self.cursor:
                self.connect_db()

            sql = "SELECT MAX(y.UPDATE_TIME_) AS LATEST_TIME FROM hzxc.YSWFTB y WHERE y.SFWFTB = '2' AND DQHJ = '市两违办核查'"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            self.cursor.close()

            return result[0]  # 返回最晚时间戳
        except Exception as e:
            logging.error(f"获取最晚时间戳时出错: {str(e)}")
            self.reconnect_db()
            return None

    def download_with_threading(self, last_check_time=None):
        try:
            if not self.connection or not self.cursor:
                self.connect_db()

            sql = """
            SELECT y.ID, y.TU_BAN_BIAN_HAO_, y.TU_BIAO_ZUO_LAO_, y.UPDATE_TIME_,
                   y.MJ, x.XZLWDD, x.CDTBLX, x.ZDMJ, x.YDMJ, x.DSR, x.JSMJ, x.SCZZCL 
            FROM hzxc.YSWFTB y 
            LEFT JOIN hzxc.XCGKQK x ON x.PARENT_ID_ = y.id 
            WHERE y.SFWFTB = '2' AND DQHJ = '市两违办核查'
            """
            if last_check_time is not None:
                # 确保 last_check_time 是字符串格式
                last_check_time_str = last_check_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(last_check_time,
                                                                                                  datetime.datetime) else last_check_time
                sql += f" AND y.UPDATE_TIME_ > TO_DATE('{last_check_time_str}', 'YYYY-MM-DD HH24:MI:SS')"
            sql += " ORDER BY y.UPDATE_TIME_ DESC"

            self.cursor.execute(sql)
            columns = [col[0] for col in self.cursor.description]
            rows = self.cursor.fetchall()
            self.cursor.close()

            # 检查是否有新增数据
            if not rows:
                logging.info(f"查询结束，没有新增数据")
                return last_check_time

            time_start = time.time()
            # 创建任务队列并填充记录
            task_queue = queue.Queue()
            for row in rows:
                task_queue.put(row)

            # 启动处理线程
            self.download_threads = []
            for _ in range(self.num_threads):
                thread = threading.Thread(target=self.process_task_worker, args=(task_queue, columns))
                thread.start()
                self.download_threads.append(thread)

            # 等待队列处理完成
            task_queue.join()
            time_end = time.time()

            # 返回最后一条记录的时间
            max_update_time = max(row['UPDATE_TIME_'] for row in rows)
            logging.info(f"已下载 {len(rows)} 条新增数据，获取最新时间戳: {max_update_time} , 用时 {time_end - time_start}")

            return max_update_time

        except Exception as e:
            logging.error(f"下载任务时出错: {str(e)}")
            self.reconnect_db()
            # 如果下载出错，返回原始时间戳
            return last_check_time

    def download(self, id_list=None):
        """
        根据传入的ID列表下载文件
        :param id_list: 固定的ID列表
        """
        try:
            if not self.connection or not self.cursor:
                self.connect_db()

            id_str = ", ".join(f"'{id}'" for id in id_list)
            sql = f"""SELECT y.ID,y.TU_BAN_BIAN_HAO_,y.UPDATE_TIME_,y.TU_BIAO_ZUO_LAO_,y.MJ,x.XZLWDD,
            x.CDTBLX,x.ZDMJ,x.YDMJ,x.DSR,x.JSMJ,x.SCZZCL FROM hzxc.YSWFTB y LEFT JOIN  hzxc.XCGKQK x ON 
            x.PARENT_ID_ = y.id WHERE y.SFWFTB = '2' AND y.ID IN ({id_str})"""

            self.cursor.execute(sql)
            columns = [col[0] for col in self.cursor.description]
            rows = self.cursor.fetchall()
            self.cursor.close()

            # 创建任务队列并填充记录
            task_queue = queue.Queue()
            for row in rows:
                task_queue.put(row)

            # 启动处理线程
            self.download_threads = []
            for _ in range(self.num_threads):
                thread = threading.Thread(target=self.process_task_worker, args=(task_queue, columns))
                thread.start()
                self.download_threads.append(thread)

            # 等待队列处理完成
            task_queue.join()

        except Exception as e:
            logging.error(f"下载任务时出错: {str(e)}")
            self.reconnect_db()

    def process_task_worker(self, task_queue, columns):
        while True:
            try:
                row = task_queue.get(timeout=1)
                row_dict = dict(zip(columns, row))
                self.process_record(row_dict)
                task_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                logging.error(f"处理记录失败: {e}")
                task_queue.task_done()

    def start_download(self, last_check_time=None):
        return self.download_with_threading(last_check_time)

    def get_task_queue(self):
        return self.task_queue

    def add_task(self, task_id, file_paths):
        with self.lock:
            if task_id not in self.processed_tasks:
                self.task_queue.put((task_id, file_paths))
                self.processed_tasks.add(task_id)

    def task_done(self):
        with self.lock:
            self.task_queue.task_done()