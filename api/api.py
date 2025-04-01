# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: api.py
@Time    : 2025/3/18 下午5:31
@Author  : ZhouFei
@Email   : zhoufei.net@outlook.com
@Desc    : api接口
@Usage   :
"""
import os
import sys
import oracledb
from flask import Flask, request, jsonify



# 获取项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from utils import load_config
from database import get_audit_result

# 加载配置文件
config = load_config()
# 获取 LLM 识别服务的配置
llm_config = config.get("results_db_config", {})
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Oracle 数据库配置
ORACLE_USER = llm_config.get("user")
ORACLE_PASSWORD = llm_config.get("password")
ORACLE_HOST = llm_config.get("host")
ORACLE_PORT = llm_config.get("port")
ORACLE_SID = llm_config.get("sid")

# Flask 应用配置
FLASK_HOST = '0.0.0.0'  # 默认监听所有 IP
FLASK_PORT = 8090  # 默认端口


# 创建数据库连接
def get_db_connection():
    dsn = oracledb.makedsn(ORACLE_HOST, ORACLE_PORT, sid=ORACLE_SID)
    conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=dsn)
    return conn


# 查询数据
def query_data(task_id):
    try:
        # 使用 audit_results.py 中的 get_audit_result 函数查询 SQLite 数据库
        result = get_audit_result(config, task_id)
        if result:
            return result
        else:
            return None
    except Exception as e:
        print(f"查询过程中发生错误: {e}")
        return None


# Flask 路由
@app.route('/api', methods=['GET', 'POST'])
def get_data():
    task_id = request.args.get('id')  # 从 GET 请求的查询参数获取 id
    if not task_id:
        task_id = request.json.get('id')  # 从 POST 请求的 JSON 数据中获取 id

    # 如果仍然没有获取到 task_id，返回错误
    if not task_id:
        return jsonify({"error": "Missing 'id' parameter"}), 400

    # 打印请求的 IP 地址
    print(f"请求的 IP 地址: {request.remote_addr}， 响应的 task_id {task_id}")

    data = query_data(task_id)
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "Data not found"}), 404


if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)