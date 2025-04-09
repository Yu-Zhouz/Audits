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
  "占地面积": 120
}
"""
import logging
import sqlite3
import threading
from typing import Dict, Optional


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
            占地面积 INTEGER
        )
        """)
        self.conn.commit()

    def insert_data(self, data: Dict):
        with self.lock:  # 使用锁确保线程安全
            cursor = self.conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO data_results (id, 公章, 当事人, 图斑编号, 建筑层数, 占地面积)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    data["id"],
                    data["公章"],
                    data["当事人"],
                    data["图斑编号"],
                    data["建筑层数"],
                    data["占地面积"]
                ))
                self.conn.commit()
                logging.info("数据插入成功！")
            except sqlite3.IntegrityError:
                logging.info("插入数据失败，尝试更新数据...")
                try:
                    cursor.execute("""
                    UPDATE data_results
                    SET 公章 = ?, 当事人 = ?, 图斑编号 = ?, 建筑层数 = ?, 占地面积 = ?
                    WHERE id = ?
                    """, (
                        data["公章"],
                        data["当事人"],
                        data["图斑编号"],
                        data["建筑层数"],
                        data["占地面积"],
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
                    "GZ": bool(row[1]),        # "公章"
                    "DSR": row[2],             # "当事人"
                    "TBBH": row[3],            # "图斑编号"
                    "JZCS": row[4],            # "建筑层数"
                    "ZDMJ": row[5]             # "占地面积"
                }
                    return None
            except Exception as e:
                print(f"查询异常: {e}")
                return None
            finally:
                cursor.close()

    def close(self):
        self.conn.close()

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
    db.close()

def get_audit_result(config: Dict, task_id: str) -> Optional[Dict]:
    """根据 task_id 获取审计结果"""
    # 初始化数据库
    db = AuditDatabase(config)
    try:
        result = db.query_data(task_id)
        return result
    except Exception as e:
        print(f"查询过程中发生错误: {e}")
        return None
    finally:
        db.close()


# 测试代码
if __name__ == "__main__":
    # 示例数据
    data = {
        "id": "122222224558489",
        "公章": True,
        "当事人": "五六",
        "图斑编号": "HZJGZW202401-441322122510Z0006",
        "建筑层数": 3,
        "占地面积": 123
    }

    config = {
        "results_db_config": {
            "db_name": "../database/audit_results.db"
        }
    }

    # 调用封装的函数
    store_audit_result(config, data)

    # 查询测试
    result = get_audit_result(config, "122222224558489")
    print(result)