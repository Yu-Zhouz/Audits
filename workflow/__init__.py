# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: __init__.py.py
@Time    : 2025/3/23 下午8:29
@Author  : ZhouFei
@Email   : zhoufei.net@outlook.com
@Desc    : 
@Usage   :
"""
import logging

from .workflow import Base_Workflow

def get_workflow(config):
    workflow_type = config.get("workflow_config").get("workflow_type", "mini")
    if workflow_type == "mini":
        from .workflow_mini import Workflow
        return Workflow(config)
    elif workflow_type == "lite":
        from .workflow_lite import Workflow
        return Workflow(config)
    elif workflow_type == "ultra":
        from .workflow_ultra import Workflow
        return Workflow(config)
    elif workflow_type == "pro":
        from .workflow_pro import Workflow
        return Workflow(config)
    elif workflow_type == "plus":
        from .workflow_plus import Workflow
        return Workflow(config)

    else:
        logging.error("Invalid workflow type")