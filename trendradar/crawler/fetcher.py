# coding=utf-8
"""
数据获取器模块

负责从 NewsNow API 抓取新闻数据，支持：
- 单个平台数据获取
- 批量平台数据爬取
- 自动重试机制
- 代理支持
"""

import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional, Union

import requests


class DataFetcher:
    """数据获取器"""

    # 默认 API 地址
    DEFAULT_API_URL = "https://newsnow.busiyi.world/api/s"

    # 默认请求头
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    }

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        """
        初始化数据获取器

        Args:
            proxy_url: 代理服务器 URL（可选）
            api_url: API 基础 URL（可选，默认使用 DEFAULT_API_URL）
        """
        self.proxy_url = proxy_url
        self.api_url = api_url or self.DEFAULT_API_URL

    def fetch_data(
        self,
        id_info: Union[str, Tuple[str, str]],
        max_retries: int = 2,
        min_retry_wait: int = 3,
        max_retry_wait: int = 5,
    ) -> Tuple[Optional[str], str, str]:
        """
        获取指定ID数据，支持重试

        Args:
            id_info: 平台ID 或 (平台ID, 别名) 元组
            max_retries: 最大重试次数
            min_retry_wait: 最小重试等待时间（秒）
            max_retry_wait: 最大重试等待时间（秒）

        Returns:
            (响应文本, 平台ID, 别名) 元组，失败时响应文本为 None
        """
        if isinstance(id_info, tuple):
            id_value, alias = id_info
        else:
            id_value = id_info
            alias = id_value

        url = f"{self.api_url}?id={id_value}&latest"

        proxies = None
        if self.proxy_url:
            proxies = {"http": self.proxy_url, "https": self.proxy_url}

        retries = 0
        while retries <= max_retries:
            try:
                response = requests.get(
                    url,
                    proxies=proxies,
                    headers=self.DEFAULT_HEADERS,
                    timeout=10,
                )
                response.raise_for_status()

                data_text = response.text
                data_json = json.loads(data_text)

                status = data_json.get("status", "未知")
                if status not in ["success", "cache"]:
                    raise ValueError(f"响应状态异常: {status}")

                status_info = "最新数据" if status == "success" else "缓存数据"
                print(f"获取 {id_value} 成功（{status_info}）")
                return data_text, id_value, alias

            except Exception as e:
                retries += 1
                if retries <= max_retries:
                    base_wait = random.uniform(min_retry_wait, max_retry_wait)
                    additional_wait = (retries - 1) * random.uniform(1, 2)
                    wait_time = base_wait + additional_wait
                    print(f"请求 {id_value} 失败: {e}. {wait_time:.2f}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"请求 {id_value} 失败: {e}")
                    return None, id_value, alias

        return None, id_value, alias

    def crawl_websites(
        self,
        ids_list: List[Union[str, Tuple[str, str]]],
        request_interval: int = 100,
        max_workers: int = 5,
    ) -> Tuple[Dict, Dict, List]:
        """
        并发爬取多个网站数据

        Args:
            ids_list: 平台ID列表，每个元素可以是字符串或 (平台ID, 别名) 元组
            request_interval: 请求间隔（毫秒）
            max_workers: 最大并发爬虫数

        Returns:
            (结果字典, ID到名称的映射, 失败ID列表) 元组
        """
        results = {}
        id_to_name = {}
        failed_ids = []

        # 构建 ID 映射
        for id_info in ids_list:
            if isinstance(id_info, tuple):
                id_value, name = id_info
            else:
                id_value = id_info
                name = id_value
            id_to_name[id_value] = name

        def _fetch_single(id_info):
            """抓取单个平台数据"""
            if isinstance(id_info, tuple):
                id_value = id_info[0]
            else:
                id_value = id_info

            response, _, _ = self.fetch_data(id_info)
            if not response:
                return id_value, None

            try:
                data = json.loads(response)
                platform_results = {}
                for index, item in enumerate(data.get("items", []), 1):
                    title = item.get("title")
                    if title is None or isinstance(title, float) or not str(title).strip():
                        continue
                    title = str(title).strip()
                    url = item.get("url", "")
                    mobile_url = item.get("mobileUrl", "")

                    if title in platform_results:
                        platform_results[title]["ranks"].append(index)
                    else:
                        platform_results[title] = {
                            "ranks": [index],
                            "url": url,
                            "mobileUrl": mobile_url,
                        }
                return id_value, platform_results
            except json.JSONDecodeError:
                print(f"解析 {id_value} 响应失败")
                return id_value, None
            except Exception as e:
                print(f"处理 {id_value} 数据出错: {e}")
                return id_value, None

        actual_workers = min(max_workers, len(ids_list))
        print(f"并发爬取 {len(ids_list)} 个平台，最大并发数: {actual_workers}")

        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            future_to_id = {executor.submit(_fetch_single, id_info): id_info for id_info in ids_list}
            for future in as_completed(future_to_id):
                id_value, platform_results = future.result()
                if platform_results is not None:
                    results[id_value] = platform_results
                else:
                    failed_ids.append(id_value)

        print(f"成功: {list(results.keys())}, 失败: {failed_ids}")
        return results, id_to_name, failed_ids
