# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: api.py
@Time    : 2025/3/18 下午5:31
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : api接口
@Usage   :
"""
import os
import sys
import oracledb
from flask import Flask, request, jsonify
from gevent import pywsgi


# 获取项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from utils import load_config
from database import query_data, query_data_by_ids

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



# Flask 路由, 用于获取单个数据
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

    data = query_data(config, task_id)
    return jsonify(data)  # 如果查询不到数据，返回 None

# Flask 路由, 用于获取多个数据
@app.route('/api/bulk', methods=['GET', 'POST'])
def get_bulk_data():
    # 从 GET 请求的查询参数获取 ids
    task_ids = request.args.getlist('ids')  # 支持多个 ids 参数
    if not task_ids:
        # 从 POST 请求的 JSON 数据中获取 ids
        task_ids = request.json.get('ids') if request.json else None

    # 如果仍然没有获取到 task_ids，返回错误
    if not task_ids:
        return jsonify({"error": "Missing 'ids' parameter"}), 400

    # 打印请求的 IP 地址
    print(f"请求的 IP 地址: {request.remote_addr}， 响应的 task_ids {task_ids}")

    data = query_data_by_ids(config, task_ids)
    return jsonify(data)  # 如果查询不到数据，返回空列表


if __name__ == '__main__':
    # app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)
    # 生产部署使用 gevent 的 WSGIServer 启动 Flask 应用
    server = pywsgi.WSGIServer((FLASK_HOST, FLASK_PORT), app)
    server.serve_forever()
