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
# log_level = 'DEBUG'
log_level = 'INFO'
filename = os.path.basename(__file__)
log_dir = os.path.join('logs', env_name, filename.split('.')[0])
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, '{time:YYYY-MM-DD}.log')
logger.add(sys.stderr, level=log_level)
logger.add(log_file, level=log_level, rotation="00:00", enqueue=True, serialize=False, encoding="utf-8")

app = FastMCP("github-tools", host='0.0.0.0', port=int(os.getenv("PORT", 4001)))

REPO_API = "https://api.github.com/search/repositories"


class GitHubSearchError(Exception):
    pass


def _auth_headers(token: Optional[str]):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-repo-search/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


@app.tool()
def search_github_repos(
        query: str,
        token: Optional[str] = None,
        per_page: int = 10,
        max_pages: int = 1
) -> list[dict]:
    """
    使用 GitHub API 搜索仓库

    :param query: 仓库检索关键词（如 "qwen3"）
    :param token: GitHub API token（可选，提升 rate limit）
    :param per_page: 每页返回的仓库数量，默认 10
    :param max_pages: 最多请求多少页，默认 1
    :return: 仓库搜索结果列表，每个元素包含以下字段：
        [
          {
            "name": 仓库名,
            "owner_name": 仓库所有者,
            "full_name": 完整仓库名 (owner/name),
            "description": 仓库描述,
            "url": 仓库主页 URL,
            "created_at": 创建时间,
            "updated_at": 更新时间,
            "pushed_at": 最近推送时间,
            "language": 主要编程语言,
            "has_issues": 是否启用 issues,
            "has_projects": 是否启用 projects,
            "has_downloads": 是否启用下载,
            "has_wiki": 是否启用 wiki,
            "has_pages": 是否启用 pages,
            "has_discussions": 是否启用讨论,
            "archived": 是否已归档,
            "disabled": 是否禁用,
            "license": 许可证信息,
            "topics": 主题标签,
            "visibility": 仓库可见性,
            "forks": fork 数,
            "open_issues": 未解决 issue 数,
            "watchers": 关注数,
            "default_branch": 默认分支,
            "score": 匹配得分
          },
          ...
        ]
    """
    if not query:
        raise GitHubSearchError("query 不能为空")

    logger.info(f"query: {query}")
    logger.info(f"per_page: {per_page}")
    logger.info(f"max_pages: {max_pages}")

    headers = _auth_headers(token)
    all_items = []

    for page in range(1, max_pages + 1):
        params = {
            "q": f"in:name {query} stars:>=1 fork:false -is:archived",
            "per_page": per_page,
            "page": page,
            "sort": "stars",
            "order": "desc",
        }

        resp = requests.get(REPO_API, headers=headers, params=params, timeout=20)

        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            time.sleep(2)
            resp = requests.get(REPO_API, headers=headers, params=params, timeout=20)

        if resp.status_code != 200:
            raise GitHubSearchError(f"请求失败 {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        items = data.get("items", [])
        all_items.extend(items)

        if len(items) < per_page:
            break

    results = [
        {
            "name": r["name"],
            "owner_name": r["owner"]["login"],
            "full_name": r["full_name"],
            "description": r["description"],
            "url": r["html_url"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "pushed_at": r["pushed_at"],
            "language": r["language"],
            "has_issues": r["has_issues"],
            "has_projects": r["has_projects"],
            "has_downloads": r["has_downloads"],
            "has_wiki": r["has_wiki"],
            "has_pages": r["has_pages"],
            "has_discussions": r["has_discussions"],
            "archived": r["archived"],
            "disabled": r["disabled"],
            "license": r["license"],
            "topics": r["topics"],
            "visibility": r["visibility"],
            "forks": r["forks"],
            "open_issues": r["open_issues"],
            "watchers": r["watchers"],
            "default_branch": r["default_branch"],
            "score": r["score"],
            # "owner": r["owner"],
        }
        for r in all_items
    ]

    logger.info(f'results\n{pformat(results)}')
    logger.info('-' * 100)

    return results


@app.tool()
def get_github_readme(owner: str, repo: str):
    """
    获取指定 GitHub 仓库的 README 内容

    :param owner: 仓库所有者（用户名或组织名），如 QwenLM
    :param repo: 仓库名，如 Qwen3
    :return: README 文件的原始文本内容（若获取失败则返回 None）
    """
    logger.info(f"owner/repo: {owner}/{repo}")

    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {"Accept": "application/vnd.github.v3.raw"}

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        readme_content = resp.text

        logger.info(f"readme_content_length: {len(readme_content)}")
        logger.info(f"readme_content: {readme_content}")
        logger.info('-' * 100)

        return readme_content
    else:
        try:
            err_json = resp.json()
        except Exception:
            err_json = {"text": resp.text}
        logger.error(f"获取失败: {resp.status_code} {err_json}")
        return None


if __name__ == '__main__':
    # transport = "stdio"
    transport = "sse"
    app.run(transport=transport)
