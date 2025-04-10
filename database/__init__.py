import logging
from .db_downloader_mt import DataDownloader


def get_db(config):
    db_type = config.get("results_db_config", {}).get("db_type", "mysql")
    if db_type == "mysql":
        logging.info("使用mysql数据库")
        from .audit_results_my import store_audit_result, query_data, query_data_by_ids
    elif db_type == "sqlite":
        logging.info("使用sqlite数据库")
        from .audit_results import store_audit_result, query_data, query_data_by_ids
    else:
        raise ValueError("Invalid db_type")

    return store_audit_result, query_data, query_data_by_ids

def execute_query_data(config, *args, **kwargs):
    _, query_data, _ = get_db(config)
    return query_data(*args, **kwargs)

def execute_query_data_by_ids(config, *args, **kwargs):
    _, _, query_data_by_ids = get_db(config)
    return query_data_by_ids(*args, **kwargs)
