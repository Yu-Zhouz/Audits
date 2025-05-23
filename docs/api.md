# **API接口说明文档**

## **概述**

本API提供审计结果查询功能，支持通过单个ID查询和通过ID列表批量查询。

## **版本**

- **API版本**: v1.0

- **服务地址**: `http://172.16.15.10:30108`

## **单ID查询**

通过单个ID查询审计结果。

- **请求方式**: GET 或 POST

- **请求地址**: `/api`

- **请求参数**:

	- `id` (必填): 审计任务ID，字符串类型。

- **返回结果**:

	- 成功时返回审计结果的JSON对象。
	
	- 失败时返回错误信息。

**示例请求**:

`GET http://172.16.15.10:30108/api?id=1188784685862354944`

**示例响应**:

```json
{
  "DSR": "郭文彬",
  "ID": "1188784685862354944",
  "JZCS": null,
  "JZMJ": null,
  "TBBH": null,
  "ZDMJ": 80
}
```

```json
null
```

**错误响应**:

```json
{
  "error": "Missing 'id' parameter"
}
```

## **ID列表查询**

通过ID列表批量查询审计结果。

- **请求方式**: GET 或 POST

- **请求地址**: `/api/bulk`

- **请求参数**:

	- GET请求: 使用 `ids` 参数，支持多个值。
	
	- POST请求: 使用 JSON 格式，包含 `ids` 字段。

- **返回结果**:

	- 成功时返回一个包含多个审计结果的JSON对象。
	
	- 失败时返回错误信息。


**示例请求**:

`GET http://172.16.15.10:30108/api/bulk?ids=1162708535117611008&ids=1187333480422309890&ids=1188784685862354944`

**示例POST请求**:


```json
{
  "ids": ["1162708535117611008", "1187333480422309890", "1188784685862354944"]
}
```

**示例响应**:

```json
[
  {
    "DSR": "龙门县庄加庄温泉度假村有限公司",
    "ID": "1162708535117611008",
    "JZCS": 5,
    "JZMJ": 7000,
    "TBBH": null,
    "ZDMJ": 41433
  },
  {
    "DSR": "钟瑞强",
    "ID": "1187333480422309890",
    "JZCS": 4,
    "JZMJ": 480,
    "TBBH": null,
    "ZDMJ": 120
  },
  {
    "DSR": "郭文彬",
    "ID": "1188784685862354944",
    "JZCS": null,
    "JZMJ": null,
    "TBBH": null,
    "ZDMJ": 80
  }
]
```

```json
[
  {
    "DSR": "龙门县庄加庄温泉度假村有限公司",
    "ID": "1162708535117611008",
    "JZCS": 5,
    "JZMJ": 7000,
    "TBBH": null,
    "ZDMJ": 41433
  },
  {
    "DSR": "郭文彬",
    "ID": "1188784685862354944",
    "JZCS": null,
    "JZMJ": null,
    "TBBH": null,
    "ZDMJ": 80
  }
]
```

**错误响应**:

```json
{
  "error": "Missing 'ids' parameter"
}
```

## **参数说明**

### 表格

|参数名|类型|描述|
|:-:|:-:|:-:|
|`id`|string|单个审计任务ID。|
|`ids`|list[string]|多个审计任务ID列表。|

## **返回字段说明**

### 表格

|字段名|类型|描述|
|:-:|:-:|:-:|
|`ID`|string|审计任务ID。|
|`DSR`|string|当事人姓名。|
|`TBBH`|string|图斑编号。|
|`JZCS`|integer|建筑层数。|
|`ZDMJ`|integer|占地面积。|
|`JZMJ`|integer|建筑面积。|

### **错误代码说明**

| 错误代码 |      描述      |
| :--: | :----------: |
| 400  | 请求参数缺失或格式错误。 |
