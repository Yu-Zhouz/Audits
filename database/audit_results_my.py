# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: audit_results_my.py
@Time    : 2025/3/18 下午5:55
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 用于将模型识别的字典结果储存到数据库（MySQL版本）
@Usage   : 字典示例
{
  "id": "122222224558485",
  "公章": true,
  "当事人": "张三",
  "图斑编号": "HZJGZW202401-441322122510Z0006",
  "建筑层数": 3,
  "占地面积": 120,
  "建筑面积": 200,
}
"""
import logging
import threading
from typing import Dict, Optional, List
import mysql.connector
from mysql.connector import Error, IntegrityError
from utils import retry_on_error

# 数据库操作类
class AuditDatabase:
    def __init__(self, config):
        self.config = config
        self.db_config = config.get("results_db_config", {})
        """初始化数据库连接"""
        self.conn = self.connect_db()
        self.create_table()
        self.lock = threading.Lock()  # 保持线程锁

    def connect_db(self) -> mysql.connector.MySQLConnection:
        """连接到 MySQL 数据库"""
        try:
            return mysql.connector.connect(
                host=self.db_config.get("host"),
                port=self.db_config.get("port"),
                user=self.db_config.get("user"),
                password=self.db_config.get("password"),
                database=self.db_config.get("database"),
                charset='utf8mb4'
            )
        except Error as e:
            logging.error(f"数据库连接失败: {e}")
            raise

    def create_table(self):
        """创建表（如果不存在）"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_results (
                id VARCHAR(255) PRIMARY KEY,
                公章 BOOLEAN,
                当事人 TEXT,
                图斑编号 TEXT,
                建筑层数 VARCHAR(50),
                占地面积 DECIMAL(38, 4),
                建筑面积 DECIMAL(38, 4)
            )
            """)
            self.conn.commit()
        finally:
            cursor.close()

    def insert_data(self, data: Dict):
        with self.lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO data_results 
                (id, 公章, 当事人, 图斑编号, 建筑层数, 占地面积, 建筑面积)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    data["id"],
                    data["公章"],
                    data["当事人"],
                    data["图斑编号"],
                    data["建筑层数"],
                    data["占地面积"],
                    data["建筑面积"]
                ))
                self.conn.commit()
                logging.info("数据插入成功！")
            except IntegrityError:
                logging.info("已存在id，更新数据...")
                try:
                    cursor.execute("""
                    UPDATE data_results SET
                        公章 = %s,
                        当事人 = %s,
                        图斑编号 = %s,
                        建筑层数 = %s,
                        占地面积 = %s,
                        建筑面积 = %s
                    WHERE id = %s
                    """, (
                        data["公章"],
                        data["当事人"],
                        data["图斑编号"],
                        data["建筑层数"],
                        data["占地面积"],
                        data["建筑面积"],
                        data["id"]
                    ))
                    self.conn.commit()
                    logging.info("数据更新成功！")
                except Error as e:
                    logging.error(f"更新失败: {e}")
                    self.conn.rollback()
            except Error as e:
                logging.error(f"数据库错误: {e}")
                self.conn.rollback()
            finally:
                cursor.close()

    def query_data(self, task_id: str) -> Optional[Dict]:
        with self.lock:
            cursor = self.conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT * FROM data_results WHERE id = %s",
                    (task_id,)
                )
                row = cursor.fetchone()
                return {
                    "ID": row["id"],
                    # "GZ": bool(row["公章"]),  # 转换数据库值到布尔类型
                    "DSR": row["当事人"],
                    "TBBH": row["图斑编号"],
                    "JZCS": row["建筑层数"],
                    "ZDMJ": row["占地面积"],
                    "JZMJ": row["建筑面积"]
                } if row else None
            except Error as e:
                logging.error(f"查询失败: {e}")
                return None
            finally:
                cursor.close()

    def query_data_by_ids(self, task_ids: List[str]) -> List[Optional[Dict]]:
        with self.lock:
            cursor = self.conn.cursor(dictionary=True)
        try:
            if not task_ids:  # 处理空列表情况
                return []
            
            # 构建IN查询占位符
            format_strings = ','.join(['%s'] * len(task_ids))
            query = f"SELECT * FROM data_results WHERE id IN ({format_strings})"
            cursor.execute(query, tuple(task_ids))
            
            # 获取并转换结果
            rows = cursor.fetchall()
            translated_results = {}
            for row in rows:
                translated = {
                    "ID": row["id"],
                    # "GZ": bool(row["公章"]),  # 转换数据库值到布尔类型
                    "DSR": row.get("当事人"),
                    "TBBH": row.get("图斑编号"),
                    "JZCS": row.get("建筑层数"),
                    "ZDMJ": row.get("占地面积"),
                    "JZMJ": row.get("建筑面积")
                }
                translated_results[row['id']] = translated
            
            # 按原始顺序返回，并过滤掉不存在的项
            return [translated_results[tid] for tid in task_ids if tid in translated_results]
            
        except Error as e:
            logging.error(f"批量查询失败: {e}")
            return []
        finally:
            cursor.close()

    def close(self):
        self.conn.close()

@retry_on_error(retries=5)
def store_audit_result(config: Dict, data: Dict):
    db = AuditDatabase(config)
    try:
        db.insert_data(data)
    except Exception as e:
        logging.error(f"存储失败: {e}")
    finally:
        db.close()

@retry_on_error(retries=5)
def query_data(config, task_id):
    db = AuditDatabase(config)
    try:
        return db.query_data(task_id)
    except Exception as e:
        logging.error(f"查询异常: {e}")
        return None
    finally:
        db.close()

@retry_on_error(retries=5)
def query_data_by_ids(config, task_ids):
    db = AuditDatabase(config)
    try:
        return db.query_data_by_ids(task_ids)
    except Exception as e:
        logging.error(f"批量查询异常: {e}")
        return []
    finally:
        db.close()