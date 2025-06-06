# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: audit_results.py
@Time    : 2025/3/18 下午5:55
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 用于将模型识别的字典结果储存到数据库
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
import sqlite3
import threading
from typing import Dict, Optional
from utils import retry_on_error


# 数据库操作类
class AuditDatabase:
    def __init__(self, config):
        self.config = config
        self.db_config = config.get("results_db_config", {})
        """初始化数据库连接"""
        self.db_name = self.db_config.get("db_name")
        self.conn = self.connect_db()
        self.create_table()
        self.lock = threading.Lock()  # 添加锁机制

    def connect_db(self) -> sqlite3.Connection:
        """连接到 SQLite 数据库"""
        return sqlite3.connect(self.db_name)

    def create_table(self):
        """创建存储审计结果的表"""
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_results (
            id TEXT PRIMARY KEY,
            公章 BOOLEAN,
            当事人 TEXT,
            图斑编号 TEXT,
            建筑层数 INTEGER,
            占地面积 INTEGER,
            建筑面积 INTEGER
        )
        """)
        self.conn.commit()

    def insert_data(self, data: Dict):
        with self.lock:  # 使用锁确保线程安全
            cursor = self.conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO data_results (id, 公章, 当事人, 图斑编号, 建筑层数, 占地面积, 建筑面积)
                VALUES (?, ?, ?, ?, ?, ?, ?)
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
            except sqlite3.IntegrityError:
                logging.info("已存在id，更新数据...")
                try:
                    cursor.execute("""
                    UPDATE data_results
                    SET 公章 = ?, 当事人 = ?, 图斑编号 = ?, 建筑层数 = ?, 占地面积 = ?, 建筑面积 = ?
                    WHERE id = ?
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
                except Exception as e:
                    logging.error(f"更新数据时发生错误：{e}")
            except Exception as e:
                logging.error(f"插入数据时发生未知错误：{e}")

    def query_data(self, task_id: str) -> Optional[Dict]:
        with self.lock:  # 使用锁确保线程安全
            cursor = self.conn.cursor()
            try:
                cursor.execute("SELECT * FROM data_results WHERE id = ?", (task_id,))
                row = cursor.fetchone()
                if row:
                    return {
                    "ID": row[0],
                    # "GZ": bool(row[1]),        # "公章"
                    "DSR": row[2],             # "当事人"
                    "TBBH": row[3],            # "图斑编号"
                    "JZCS": row[4],            # "建筑层数"
                    "ZDMJ": row[5],            # "占地面积"
                    "JZMJ": row[6],            # "建筑面积"
                }
                else:
                    return None
            except Exception as e:
                print(f"查询异常: {e}")
                return None
            finally:
                cursor.close()

    def query_data_by_ids(self, task_ids: list) -> list:
        """根据多个 task_id 获取审计结果"""
        with self.lock:  # 使用锁确保线程安全
            cursor = self.conn.cursor()
            try:
                # 构造 SQL 查询语句
                placeholders = ", ".join(["?"] * len(task_ids))
                query = f"SELECT * FROM data_results WHERE id IN ({placeholders})"
                cursor.execute(query, task_ids)
                rows = cursor.fetchall()

                # 将查询结果转换为字典列表
                results = []
                for row in rows:
                    results.append({
                        "ID": row[0],
                        # "GZ": bool(row[1]),        # "公章"
                        "DSR": row[2],   # "当事人"
                        "TBBH": row[3],  # "图斑编号"
                        "JZCS": row[4],  # "建筑层数"
                        "ZDMJ": row[5],  # "占地面积"
                        "JZMJ": row[6],  # "建筑面积"
                    })
                return results
            except Exception as e:
                print(f"查询异常: {e}")
                return []
            finally:
                cursor.close()

    def close(self):
        self.conn.close()


# 使用装饰器添加重试机制
@retry_on_error(retries=5)
def store_audit_result(config: Dict, data: Dict):
    """
    将审计结果存储到数据库中
    """
    # 初始化数据库
    db = AuditDatabase(config)
    # 插入数据
    try:
        db.insert_data(data)
    except:
        logging.error("数据库插入数据失败")
    # 关闭数据库连接
    finally:
        db.close()


# 单id查询数据
@retry_on_error(retries=5)
def query_data(config, task_id):
    """根据 task_id 获取审计结果"""
    # 初始化数据库
    db = AuditDatabase(config)
    try:
        result = db.query_data(task_id)
        if result:
            return result
        else:
            return None
    except Exception as e:
        print(f"查询过程中发生错误: {e}")
        return None
    finally:
        db.close()


# 多ID查询数据
@retry_on_error(retries=5)
def query_data_by_ids(config, task_ids):
    # 初始化数据库
    db = AuditDatabase(config)
    try:
        # 使用 audit_results.py 中的 query_data_by_ids 函数查询 SQLite 数据库
        result = db.query_data_by_ids(task_ids)
        if result:
            return result
        else:
            return None
    except Exception as e:
        print(f"查询过程中发生错误: {e}")
        return []
    finally:
        db.close()