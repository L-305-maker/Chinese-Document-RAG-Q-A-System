from typing import List,Optional
from dataclasses import field,dataclass
import re


@dataclass
class NormalizedQuery:
    original_query: str
    normalized_query: str
    language: str
    is_empty: bool
    is_valid: bool
    length: int
    is_too_long: bool


#检查query是否为空
def check_empty(query:str)->bool:
    return not query or not query.strip()


#检查query是否只有标点符号
def check_punctuation_only(query:str):
    return bool(re.fullmatch(r"[\W_]+",query.strip()))

 
#将全角符号转化为半角符号
def full_to_half(query:str)->str:
    result = []

    for char in query:
        code = ord(char)

        if code == 0x3000:
            code = 32

        elif 0xFF01 <= code and code <= 0xFF5E:
            code -= 0xFEE0

        result.append(chr(code))

    return "".join(result)


#在中文和英文/数字之间加空格
def add_space(query:str)->str:
    query = re.sub(r"([\u4e00-\u9fff])([A-Za-z0-9])",r"\1 \2",query)
    query = re.sub(r"([A-Za-z0-9])([\u4e00-\u9fff])",r"\1 \2",query)

    query = re.sub(r"\s+"," ",query)

    return query.strip()


#检查是什么语言
def detect_language(text: str) -> str:
    zh_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    en_count = len(re.findall(r"[A-Za-z]", text))

    if zh_count > 0 and en_count > 0:
        return "mixed"
    elif zh_count > 0:
        return "zh"
    elif en_count > 0:
        return "en"
    else:
        return "unknown"


#删除重复的标点符号
def delete_repaeted_punctuation(query:str)->str:
    query = re.sub(r"[?？]+", "？", query)
    query = re.sub(r"[!！]+", "！", query)
    query = re.sub(r"[.。]{2,}", "。", query)
    query = re.sub(r"[,，]{2,}", "，", query)

    return query


#删除无实际意义的装饰字符
def remove_noise_symbols(query: str) -> str:
    noise_chars = [
        "#", "*", "`", "~", "^",
        "👉", "👇", "✅", "❌", "🔥",
    ]
    for ch in noise_chars:
        query = query.replace(ch, "")
    return query.strip()


#删除常见的文具前缀
def remove_query_prefix(query:str)->str:
    QUERY_PREFIXES = [
    "请问",
    "麻烦问一下",
    "麻烦你告诉我",
    "能不能解释一下",
    "能否解释一下",
    "可以解释一下",
    "我想知道",
    "我想问一下",
    "帮我查一下",
    "帮我找一下",
    ]
    for prefix in QUERY_PREFIXES:
        if query.startswith(prefix):
            return query[len(prefix):].strip()
    return query


#进行总的初始化
def Normalize_Query(query:str)->str:
    if query is None:
        return ""
    
    query = str(query)
    query = query.strip()

    query = full_to_half(query)
    query = add_space(query)
    query = delete_repaeted_punctuation(query)
    query = remove_noise_symbols(query)
    query = remove_query_prefix(query)

    return query


#此处返回的是存储query属性的类,包括normalized_query
def normalized_query_quality(query: str, max_len: int = 512) -> NormalizedQuery:
    original_query = "" if query is None else str(query)
    normalized_query = Normalize_Query(original_query)
    is_too_long = len(normalized_query) > max_len

    is_empty = len(normalized_query.strip()) == 0
    punctuation_only = check_punctuation_only(normalized_query)
    is_valid = not is_empty and not punctuation_only  and not is_too_long

    language = detect_language(normalized_query)
    length = len(normalized_query)
    

    return NormalizedQuery(
        original_query=original_query,
        normalized_query=normalized_query,
        language=language,
        is_empty=is_empty,
        is_valid=is_valid,
        length=length,
        is_too_long=is_too_long
    )