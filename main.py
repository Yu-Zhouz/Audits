# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: main.py
@Time    : 2025/3/12 上午11:36
@Author  : ZhouFei
@Email   : zhoufei.net@gmail.com
@Desc    : 主函数
@Usage   :
"""
from utils import load_config
from parallel_processor import ParallelProcessor

if __name__ == "__main__":
    config = load_config()

    processor = ParallelProcessor(config, process_initial_data=True, delete=True)
    processor.start()
