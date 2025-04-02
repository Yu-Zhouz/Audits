# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: db_downloader.py.py
@Time    : 2025/3/24 上午9:56
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 数据库单线程下载类
@Usage   :
"""
import logging
import cx_Oracle
import json
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DataDownloader:
    def __init__(self, config):
        """
        初始化下载类
        :param config: 配置文件
        """
        self.config = config
        self.db_config = config.get("db_download_config", {})
        self.data_dir = config.get("data_config", {}).get("data_dir")
        self.check_dir_exist(self.data_dir)
        self.connection = None
        self.cursor = None
        self.connect_db()
        self.last_processed_id = 0  # 初始值为0，表示下载所有符合条件的文件
        self.task_queue = {} # 存储下载任务的队列字典
        self.retries = self.db_config.get("retries", 3)

    def connect_db(self):
        """
        连接数据库
        """
        try:
            dsn = cx_Oracle.makedsn(self.db_config['host'], self.db_config['port'], self.db_config['sid'])
            self.connection = cx_Oracle.connect(self.db_config['user'], self.db_config['password'], dsn)
            self.cursor = self.connection.cursor()
            logging.info("数据库连接成功")
        except cx_Oracle.DatabaseError as e:
            logging.error(f"数据库连接失败: {str(e)}")
            self.reconnect_db()  # 尝试重新连接
        except Exception as e:
            logging.error(f"处理过程中发生错误: {str(e)}")
            self.reconnect_db()  # 尝试重新连接

    def reconnect_db(self):
        """
        重新连接数据库
        """
        logging.info("尝试重新连接数据库...")
        for _ in range(self.retries):  # 最多尝试retries次
            try:
                self.connect_db()
                if self.connection and self.cursor:
                    logging.info("数据库重新连接成功")
                    return
            except Exception as e:
                logging.error(f"重连失败: {str(e)}")
                time.sleep(5)  # 等待5秒后再次尝试
        logging.error("数据库重新连接失败，程序将退出")
        raise Exception("数据库重新连接失败")

    def check_dir_exist(self, dir_path: str):
        """创建目录如果不存在"""
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    def close_db(self):
        """
        关闭数据库连接
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logging.info("数据库连接已关闭")

    def download_file(self, file_url, file_path):
        """
        下载文件，支持重试
        """
        session = requests.Session()
        retry_strategy = Retry(
            total=self.retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        # TODO:增加下载失败然后重新下载
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
                time.sleep(2)  # 等待2秒后重试

    def process_record(self, row_dict):
        """处理单条记录
        :param row_dict: 单条记录的字典
        """
        record_id = str(row_dict['ID'])  # 获取ID字段的值

        # 下载佐证材料
        sczzcl = row_dict['SCZZCL'] or '[]'
        raw_materials = json.loads(sczzcl)

        output_dir = os.path.join(self.data_dir, str(record_id))
        self.check_dir_exist(output_dir)

        time_start = time.time()
        file_paths = []
        for idx, material in enumerate(raw_materials, 1):
            file_name = material['fileName']
            file_id = material['id']
            file_url = f'http://163.179.247.76:8086/ibps/components/upload/download.htm?downloadId={file_id}'
            file_path = os.path.join(output_dir, file_name)
            if self.download_file(file_url, file_path):
                file_paths.append(file_path)

        logging.info(f"下载任务 {record_id} 已保存到{output_dir}, 用时{time.time() - time_start}")
        if file_paths:
            self.task_queue[record_id] = file_paths

    def download(self, last_check_time=None):
        """
        下载文件，支持重试
        """
        self.task_queue.clear()  # 清空旧数据
        # sql = """
        # SELECT x.ID, y.TU_BAN_BIAN_HAO_, y.TU_BIAO_ZUO_LAO_, y.CREATE_TIME_,
        #        y.MJ, x.XZLWDD, x.CDTBLX, x.ZDMJ, x.YDMJ, x.DSR, x.JSMJ, x.SCZZCL
        # FROM hzxc.YSWFTB y
        # LEFT JOIN hzxc.XCGKQK x ON x.PARENT_ID_ = y.id
        # WHERE y.SFWFTB = '2' AND DQHJ = '市两违办核查'
        # """
        # TODO: 用于测试
        sql = """
                SELECT x.ID, y.TU_BAN_BIAN_HAO_, y.TU_BIAO_ZUO_LAO_, y.CREATE_TIME_,
                       y.MJ, x.XZLWDD, x.CDTBLX, x.ZDMJ, x.YDMJ, x.DSR, x.JSMJ, x.SCZZCL
                FROM hzxc.YSWFTB y
                LEFT JOIN hzxc.XCGKQK x ON x.PARENT_ID_ = y.id
                WHERE y.SFWFTB = '2'  AND x.ID IN (
            '1162708535117611009',
            '1188784685929463808',
            '1188784733442539520',
            '1190349497310380032',
            '1190672681331064832'
          )
                """
        params = {}
        if last_check_time:
            sql += " AND y.CREATE_TIME_ > :last_check_time"
            params = {'last_check_time': last_check_time}

        sql += " ORDER BY y.CREATE_TIME_"

        self.cursor.execute(sql, params)
        columns = [col[0] for col in self.cursor.description]
        max_create_time = last_check_time

        for row in self.cursor:
            row_dict = dict(zip(columns, row))
            current_create_time = row_dict['CREATE_TIME_']

            if not max_create_time or current_create_time > max_create_time:
                max_create_time = current_create_time

            self.process_record(row_dict)

        return max_create_time, self.task_queue  # 返回时间和任务队列
