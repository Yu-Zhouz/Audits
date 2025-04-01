# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: utils.py
@Time    : 2025/3/12 下午2:14
@Author  : ZhouFei
@Email   : zhoufei.net@outlook.com
@Desc    : 
@Usage   :
"""
import logging
import os
import sys
from datetime import datetime

import yaml


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "../config/config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def load_examples(example_file):
    examples_path = os.path.join(os.path.dirname(__file__), example_file)
    with open(examples_path, "r", encoding="utf-8") as f:
        examples = yaml.safe_load(f)
    return examples

def suppress_print():
    """屏蔽 print 输出"""
    sys.stdout = open(os.devnull, 'w')

def restore_print():
    """恢复 print 输出"""
    sys.stdout = sys.__stdout__

def setup_logging(config, log_name='api'):
    """
    配置日志模块。
    :param config: 配置信息，包含日志级别和日志文件路径。
    :param api: 是否为 API 日志。如果为 True，则日志文件名会包含 "api"。
    """
    # 获取配置信息
    log_file_base = config.get("logging_config", {}).get("file")
    log_file = os.path.join(log_file_base, "audits")
    if log_name:
        # 在 log_file 目录下根据日期生成日志文件名
        log_files = os.path.join(log_file_base, log_name)
    else:
        log_files = log_file

    # 日期命名
    current_date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    os.makedirs(log_files, exist_ok=True)
    log_file = os.path.join(log_files, f"{current_date}.log")

    level_str = config.get("logging_config", {}).get("level", "INFO")
    level = getattr(logging, level_str.upper(), logging.INFO)  # 将字符串转换为日志级别常量

    # 创建日志格式
    log_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # 配置日志记录器
    logger = logging.getLogger()
    if logger.hasHandlers():  # 如果已经存在日志处理器，则先清除
        logger.handlers.clear()  # 清空默认的日志处理器
    logger.setLevel(level)

    # 添加控制台日志处理器
    ch = logging.StreamHandler()
    ch.setFormatter(log_format)
    logger.addHandler(ch)

    # 如果指定了日志文件，添加文件日志处理器
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)  # 确保日志文件的目录存在
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

    logger.info(f"{log_name} 日志已初始化，级别为 {logging.getLevelName(level)}。")
    return logger