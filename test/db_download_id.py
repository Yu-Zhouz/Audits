# -*- coding: utf-8 -*-
"""
@Project : Audits
@FileName: download_data.py
@Time    : 2025/3/17 下午4:46
@Author  : ZhouFei
@Email   : zhoufei.net@outlook.com
@Desc    : 从数据库下载指定id的佐证材料
@Usage   : python download_data.py --id 1227190829324435458 --output ./test_output
"""
import cx_Oracle
import json
import requests
import os
import argparse


def check_dir_exist(dir_path: str):
    """创建目录如果不存在"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)


def download_patch_review_info(record_id: str, output_base_dir: str = "./output"):
    # 数据库连接配置
    dsn = cx_Oracle.makedsn(
        host='10.10.20.101',
        port=1521,
        sid='orcl'
    )

    try:
        # 创建数据库连接
        connection = cx_Oracle.connect(
            user='SJCPB',
            password='SJcp#2025',
            dsn=dsn
        )
        cursor = connection.cursor()

        # 参数化查询
        sql = """
        SELECT y.ID,
               y.TU_BAN_BIAN_HAO_,
               y.TU_BIAO_ZUO_LAO_,
               y.MJ,
               x.XZLWDD,
               x.CDTBLX,
               x.ZDMJ,
               x.YDMJ,
               x.DSR,
               x.JSMJ,
               x.SCZZCL 
        FROM hzxc.YSWFTB y 
        LEFT JOIN hzxc.XCGKQK x ON x.PARENT_ID_ = y.id 
        WHERE y.SFWFTB = '2' AND y.ID = :record_id
        """
        cursor.execute(sql, {"record_id": record_id})

        # 获取列名
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()

        if not row:
            print(f"未找到ID为{record_id}的记录")
            return

        row_dict = dict(zip(columns, row))

        sczzcl = row_dict['SCZZCL'] or '[]'  # 处理空值情况

        # 创建输出目录
        output_dir = os.path.join(output_base_dir, f"{record_id}")
        check_dir_exist(output_dir)

        # 处理佐证材料
        materials = []
        raw_materials = json.loads(sczzcl)

        print(f"\n开始处理id {record_id}")
        print(f"找到 {len(raw_materials)} 个佐证材料")

        # 下载佐证材料
        for idx, material in enumerate(raw_materials, 1):
            file_name = material['fileName']
            file_id = material['id']
            file_url = f'http://163.179.247.76:8086/ibps/components/upload/download.htm?downloadId={file_id}'

            try:
                response = requests.get(file_url, stream=True, verify=False, timeout=30)
                response.raise_for_status()

                file_path = os.path.join(output_dir, file_name)
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                materials.append({
                    'fileName': file_name,
                    'file_download_url': file_url,
                    'status': '下载成功'
                })
                print(f"成功下载 ({idx}/{len(raw_materials)}) {file_name}")
            except Exception as e:
                materials.append({
                    'fileName': file_name,
                    'file_download_url': file_url,
                    'status': f'下载失败: {str(e)}'
                })
                print(f"({idx}/{len(raw_materials)}) {file_name} 下载失败: {str(e)}")

    except cx_Oracle.DatabaseError as e:
        print(f"数据库连接失败: {str(e)}")
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="下载指定ID的佐证材料")
    parser.add_argument("--id", default= '1319719191950917632', help="要查询的记录ID")
    parser.add_argument("--output", default="./test_output", help="输出目录路径")
    args = parser.parse_args()

    print("=== 开始数据下载任务 ===")
    download_patch_review_info(record_id=args.id, output_base_dir=args.output)
    print("\n=== 所有数据下载完成 ===")