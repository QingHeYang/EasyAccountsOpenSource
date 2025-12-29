"""
EasyAccounts 工具定义
Function Calling 格式的工具定义
"""

from typing import List, Dict, Any


# EasyAccounts 工具定义列表
EASYACCOUNTS_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "accounts",
            "description": "这个工具是用来查询用户有多少资金账户的，如果用户需要查询账户ID请使用该工具，不需要参数，直接返回一个json列表，包含账户名称、账户ID、账户余额",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "types",
            "description": "这个工具是用来获取所有账单分类(标签）信息的，如果用户需要查询分类ID，请使用该工具，不需要参数，直接返回一个json列表，包含分类ID、名称、父子关系等。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "current_date",
            "description": "这个工具是获取当前服务器时间，如果用户询问的问题中包含日期、周期、时间段，请使用该工具，不需要参数，直接返回一个yyyy-MM-dd格式的文本。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "year_statistics",
            "description": (
                "账单系统年统计信息，包含当年的每个月的收入支出盈余数据，如果用户询问具体某年的某月的收入支出概述，"
                "请调用该工具，流水详情请调用flows工具，需要传入年份year，此数据请从current_date工具获取年份并酌情修改，返回年统计信息json。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "年份，必填"
                    }
                },
                "required": ["year"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "flows",
            "description": (
                "这个工具可以根据条件查询流水，如果用户询问具体的流水内容，"
                "需要调用该工具,如果用户询问具体某年的某月的收入支出概述，请调用year_statistics工具，"
                "该工具可以组合多种参数，实现流水查询，返回值包含具体的流水列表和对应的收入支出汇总"
                "如果用户问到具体的某一项业务，请先调用types工具获取分类，考虑分类中是否可能是用户询问的分类，如果不是，在考虑拆分关键字，"
                "用户问题可能但不限于有如下情况:"
                "1. 某段时间的收入支出情况；"
                "2. 询问一些生活细节内容（note），优先根据分类查询，该接口支持模糊查询，所以简化关键字查询，如：'我什么时候给孩子买的社保'，则note字段传入'社保'，但是只支持一个关键字，如果关键字查询为空，不妨先调用types工具获取分类，然后根据分类查询；"
                "3. 某一个分类的流水情况，传入types,这个字段是数组，传入多个类型id，该id需要调用types工具获取；"
                "4. 我想看看我花了多少钱，关于收入、支出、内部转账、全部内容，修改handle字段为0、1、2、3；"
                "5. 上个季度我赚了多少钱？则需要具体查询当前日期，然后计算出对应的时间点，查询当前日期请使用current_date工具；"
                "6. 我这个月微信花了多少？需要获取微信的ID，使用accounts工具获取，需要获取时间，使用current_date工具获取，然后传入startDate和endDate；"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "accountId": {
                        "type": "integer",
                        "description": "账户ID，如果用户询问具体账户的流水，需要传入账户ID，使用accounts工具获取，可以为空"
                    },
                    "handle": {
                        "type": "integer",
                        "description": "收支类型，0：收入，1：支出，2：内部转账，3：全部，不可以为空，默认3"
                    },
                    "startDate": {
                        "type": "string",
                        "description": "开始日期，格式yyyy-MM-dd"
                    },
                    "endDate": {
                        "type": "string",
                        "description": "结束日期，格式yyyy-MM-dd，可以为空"
                    },
                    "note": {
                        "type": "string",
                        "description": "备注，谨慎使用该字段，如果查询不到，清空该字段后，查询出来全部，只支持一个关键字，如果多个关键词，请下一次查询第二个关键字，该字段为模糊查询，所以传入关键字即可，尽量简短，可以为空，查询时优先考虑types查询，如果分类中没有，再考虑note字段"
                    },
                    "singleMonth": {
                        "type": "boolean",
                        "description": "是否单月，快捷字段，如果用户问的一整个月，则传入true，无需传入endDate,开始日期传入当月1号，可以为空"
                    },
                    "types": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "流水类型ID列表，如果用户询问具体类型的流水，需要传入类型ID，使用types工具获取，可以为空数组"
                    },
                    "analysis": {
                        "type": "boolean",
                        "description": "是否分析，传入true后每一笔流水可以给出对应的百分比，如果用户询问哪项最多/最少/占比，请传入true，否则传入false，默认false"
                    },
                    "orderBy": {
                        "type": "integer",
                        "description": "按金额排序，0：升序，1：降序，2：按时间排序，默认3"
                    }
                },
                "required": ["handle"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_flow",
            "description": (
                "添加一条流水记录到账单系统。"
                "可以记录收入、支出或内部转账。"
                "使用前请先调用accounts获取账户ID，调用types获取分类ID。"
                "日期格式为yyyy-MM-dd，如果用户没有指定日期，请使用current_date获取当前日期。"
                "金额必须是数字格式的字符串，如'100.00'。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "accountId": {
                        "type": "integer",
                        "description": "账户ID，必填。使用accounts工具获取"
                    },
                    "typeId": {
                        "type": "integer",
                        "description": "分类ID，必填。使用types工具获取"
                    },
                    "actionId": {
                        "type": "integer",
                        "description": "收支动作ID，必填。需从types工具返回的action.id字段获取（如15、16等），不是handle值。每个分类都有对应的actionId"
                    },
                    "money": {
                        "type": "string",
                        "description": "金额，必填。格式如'100.00'"
                    },
                    "fDate": {
                        "type": "string",
                        "description": "流水日期，必填。格式yyyy-MM-dd"
                    },
                    "note": {
                        "type": "string",
                        "description": "备注，可选"
                    },
                    "accountToId": {
                        "type": "integer",
                        "description": "转入账户ID，内部转账时必填。使用accounts工具获取"
                    },
                    "collect": {
                        "type": "boolean",
                        "description": "是否收藏，可选，默认false"
                    }
                },
                "required": ["accountId", "typeId", "actionId", "money", "fDate"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_flow",
            "description": (
                "更新已有的流水记录。"
                "需要提供流水ID和要更新的字段。"
                "使用前请先通过flows工具查询获取流水ID。"
                "更新时需要提供完整的流水信息，不仅仅是要修改的字段。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "flowId": {
                        "type": "integer",
                        "description": "流水ID，必填。通过flows工具查询获取"
                    },
                    "accountId": {
                        "type": "integer",
                        "description": "账户ID，必填。使用accounts工具获取"
                    },
                    "typeId": {
                        "type": "integer",
                        "description": "分类ID，必填。使用types工具获取"
                    },
                    "actionId": {
                        "type": "integer",
                        "description": "收支动作ID，必填。需从types工具返回的action.id字段获取（如15、16等），不是handle值"
                    },
                    "money": {
                        "type": "string",
                        "description": "金额，必填。格式如'100.00'"
                    },
                    "fDate": {
                        "type": "string",
                        "description": "流水日期，必填。格式yyyy-MM-dd"
                    },
                    "note": {
                        "type": "string",
                        "description": "备注，可选"
                    },
                    "accountToId": {
                        "type": "integer",
                        "description": "转入账户ID，内部转账时必填"
                    },
                    "collect": {
                        "type": "boolean",
                        "description": "是否收藏，可选，默认false"
                    }
                },
                "required": ["flowId", "accountId", "typeId", "actionId", "money", "fDate"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "make_excel",
            "description": (
                "根据流水查询条件生成Excel报表文件。"
                "参数与flows工具完全一致，只是输出结果为Excel文件而不是JSON数据。"
                "生成的Excel文件会包含所有符合条件的流水记录，并自动计算汇总信息。"
                "需要提供Excel文件名称，不需要扩展名，系统会自动添加.xlsx后缀。"
                "如果用户要求导出、生成报表或生成Excel，请使用此工具而不是flows工具。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "excelName": {
                        "type": "string",
                        "description": "Excel文件名称，必填。不需要扩展名。例如：'2025年9月账单报表'"
                    },
                    "accountId": {
                        "type": "integer",
                        "description": "账户ID，如果用户询问具体账户的流水，需要传入账户ID，使用accounts工具获取，可以为空"
                    },
                    "handle": {
                        "type": "integer",
                        "description": "收支类型，0：收入，1：支出，2：内部转账，3：全部，不可以为空，默认3"
                    },
                    "startDate": {
                        "type": "string",
                        "description": "开始日期，格式yyyy-MM-dd"
                    },
                    "endDate": {
                        "type": "string",
                        "description": "结束日期，格式yyyy-MM-dd，可以为空"
                    },
                    "note": {
                        "type": "string",
                        "description": "备注关键字，用于筛选流水，可以为空"
                    },
                    "singleMonth": {
                        "type": "boolean",
                        "description": "是否单月，快捷字段，如果用户问的一整个月，则传入true，无需传入endDate,开始日期传入当月1号，可以为空"
                    },
                    "types": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "流水类型ID列表，如果用户询问具体类型的流水，需要传入类型ID，使用types工具获取，可以为空数组"
                    },
                    "collect": {
                        "type": "boolean",
                        "description": "是否只导出收藏的流水，默认false"
                    }
                },
                "required": ["excelName", "handle"]
            }
        }
    }
]


def get_tool_names() -> List[str]:
    """
    获取所有EasyAccounts工具名称列表
    
    Returns:
        工具名称列表
    """
    return [tool["function"]["name"] for tool in EASYACCOUNTS_TOOLS]