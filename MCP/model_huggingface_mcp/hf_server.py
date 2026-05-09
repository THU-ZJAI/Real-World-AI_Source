# -*- coding: utf-8 -*-
import os
import sys
import time
from pprint import pformat
from typing import Optional

import requests
from loguru import logger
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

env_name = 'dev'
logger.remove()
log_level = 'INFO'
filename = os.path.basename(__file__)
log_dir = os.path.join('logs', env_name, filename.split('.')[0])
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, '{time:YYYY-MM-DD}.log')
logger.add(sys.stderr, level=log_level)
logger.add(log_file, level=log_level, rotation="00:00", enqueue=True, serialize=False, encoding="utf-8")

app = FastMCP("huggingface-tools", host='0.0.0.0', port=int(os.getenv("PORT", 4003)))

HF_API = "https://huggingface.co/api/models"


class HuggingFaceSearchError(Exception):
    pass


def _auth_headers(token: Optional[str]):
    headers = {
        "Accept": "application/json",
        "User-Agent": "huggingface-model-search/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@app.tool()
def search_huggingface_models(
        query: str,
        token: Optional[str] = None,
        per_page: int = 10,
        max_pages: int = 1,
        filter: Optional[str] = None
) -> list[dict]:
    """
    使用 Hugging Face API 搜索模型

    :param query: 模型检索关键词（如 "bert-base"）
    :param token: Hugging Face API token（可选，提升 rate limit）
    :param per_page: 每页返回的模型数量，默认 10
    :param max_pages: 最多请求多少页，默认 1
    :param filter: 模型过滤器（如 "text-generation"、"pytorch" 等）
    :return: 模型搜索结果列表，每个元素包含以下字段：
        [
          {
            "id": 模型ID,
            "author": 模型作者,
            "downloads": 下载次数,
            "tags": 模型标签列表,
            "pipeline_tag": 任务类型,
            "likes": 点赞数,
            "private": 是否私有,
            "downloads_all_time": 总下载次数,
            "last_modified": 最后修改时间,
            "created_at": 创建时间,
            "modelId": 模型ID,
            "sha": 哈希值,
            "siblings": 文件列表,
            "cardData": 模型卡片数据
          },
          ...
        ]
    """
    if not query:
        raise HuggingFaceSearchError("query 不能为空")

    logger.info(f"query: {query}")
    logger.info(f"per_page: {per_page}")
    logger.info(f"max_pages: {max_pages}")
    logger.info(f"filter: {filter}")

    headers = _auth_headers(token)
    all_items = []

    for page in range(1, max_pages + 1):
        params = {
            "search": query,
            "limit": per_page,
            "full": "true",
            "sort": "downloads",
            "direction": "-1"
        }

        if filter:
            params["filter"] = filter

        resp = requests.get(HF_API, headers=headers, params=params, timeout=20)

        if resp.status_code == 429:  # Rate limit
            time.sleep(2)
            resp = requests.get(HF_API, headers=headers, params=params, timeout=20)

        if resp.status_code != 200:
            raise HuggingFaceSearchError(f"请求失败 {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        items = data
        all_items.extend(items)

        if len(items) < per_page:
            break

    logger.info(f'Found {len(all_items)} models')
    return all_items


@app.tool()
def get_huggingface_model_readme(repo_id: str, token: Optional[str] = None):
    """
    获取指定 Hugging Face 模型的 README 内容

    :param repo_id: 模型仓库ID（如 "deepseek-ai/DeepSeek-OCR"、"zai-org/GLM-4.6"、"google-bert/bert-base-uncased" 等完整仓库路径）
    :param token: Hugging Face API token（可选，提升 rate limit）
    :return: README 文件的原始文本内容（若获取失败则返回 None）
    """
    logger.info(f"repo_id: {repo_id}")

    url = f"https://huggingface.co/{repo_id}/raw/main/README.md"
    headers = {"User-Agent": "huggingface-model-readme/1.0"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        readme_content = resp.text
        logger.info(f"readme_content: {len(readme_content)} chars")
        return readme_content
    else:
        try:
            err_json = resp.json()
        except Exception:
            err_json = {"text": resp.text}
        logger.error(f"获取失败: {resp.status_code} {err_json}")
        return None


@app.tool()
def get_huggingface_model_card(repo_id: str, token: Optional[str] = None):
    """
    获取指定 Hugging Face 模型的完整模型卡片信息

    :param repo_id: 模型仓库ID（如 "deepseek-ai/DeepSeek-OCR"、"zai-org/GLM-4.6"、"google-bert/bert-base-uncased" 等完整仓库路径）
    :param token: Hugging Face API token（可选，提升 rate limit）
    :return: 模型卡片数据的JSON格式（若获取失败则返回 None）
    """
    logger.info(f"repo_id: {repo_id}")

    url = f"https://huggingface.co/api/models/{repo_id}"
    headers = _auth_headers(token)

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        model_data = resp.json()
        logger.info(f"model_data retrieved successfully")
        return model_data
    else:
        try:
            err_json = resp.json()
        except Exception:
            err_json = {"text": resp.text}
        logger.error(f"获取失败: {resp.status_code} {err_json}")
        return None


if __name__ == '__main__':
    transport = "sse"
    app.run(transport=transport)
