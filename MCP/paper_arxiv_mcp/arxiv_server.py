# -*- coding: utf-8 -*-
import json
import os
import re
import sys
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlencode, quote_plus, urljoin, urlparse, parse_qs

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from loguru import logger
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

env_name = 'dev'
logger.remove()
log_level = 'INFO'
log_dir = os.path.join('logs', env_name, os.path.basename(__file__).split('.')[0])
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, '{time:YYYY-MM-DD}.log')
logger.add(sys.stderr, level=log_level)
logger.add(log_file, level=log_level, rotation="00:00", enqueue=True, serialize=False, encoding="utf-8")

app = FastMCP("arxiv-tools", host='0.0.0.0', port=int(os.getenv("PORT", 4002)))

DEFAULT_HEADERS = {
    "User-Agent": os.getenv('User_Agent') or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
}
logger.info(f"DEFAULT_HEADERS: {DEFAULT_HEADERS}\n\n")

ARXIV_DIR = os.getenv('ARXIV_DIR') or 'files'
if not os.path.exists(ARXIV_DIR):
    os.makedirs(ARXIV_DIR, exist_ok=True)

_ARXIV_NEW_ID = re.compile(r"^(?:arXiv:)?(\d{4}\.\d{4,5})(?:v\d+)?$")
_ARXIV_OLD_ID = re.compile(r"^(?:arXiv:)?([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?$", re.IGNORECASE)


def _build_session(timeout: int = 15, retries: int = 3, backoff: float = 1.0) -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    ad = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=50)
    s.mount("http://", ad)
    s.mount("https://", ad)

    # 更像真实浏览器（尤其是 Accept / Accept-Language 很关键）
    s.headers.update(DEFAULT_HEADERS)
    _orig = s.request
    def _with_timeout(method, url, **kw):
        kw.setdefault("timeout", timeout)
        return _orig(method, url, **kw)
    s.request = _with_timeout  # type: ignore
    return s


def _extract_arxiv_id_from_r(r_value: str) -> Optional[str]:
    r_value = r_value.strip()
    m = _ARXIV_NEW_ID.match(r_value)
    if m:
        return m.group(1)
    m = _ARXIV_OLD_ID.match(r_value)
    if m:
        return m.group(1)
    return None


def _extract_arxiv_id_from_input(arxiv_input: str) -> str:
    """
    从输入中提取arxiv_id，支持多种格式：
    - 直接的arxiv_id：2507.01006, arxiv:2507.01006
    - abs页面URL：https://arxiv.org/abs/2507.01006
    - PDF页面URL：https://arxiv.org/pdf/2507.01006

    :param arxiv_input: arXiv ID 或 URL
    :return: 清理后的 arxiv_id
    """
    arxiv_input = arxiv_input.strip()

    # 如果是URL格式，提取arxiv_id
    if arxiv_input.startswith('http'):
        # 解析URL
        parsed = urlparse(arxiv_input)

        # 确保是arxiv.org域名
        if 'arxiv.org' not in parsed.netloc:
            raise ValueError(f"Invalid arXiv URL: {arxiv_input}")

        # 提取路径部分
        path = parsed.path

        # 处理abs页面URL: /abs/2507.01006
        if '/abs/' in path:
            arxiv_id = path.split('/abs/')[-1]
            # 移除版本号（如v1、v2等）
            arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
            return arxiv_id

        # 处理PDF页面URL: /pdf/2507.01006
        elif '/pdf/' in path:
            arxiv_id = path.split('/pdf/')[-1]
            # 移除版本号（如v1、v2等）
            arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
            return arxiv_id

        else:
            raise ValueError(f"Unable to extract arXiv ID from URL: {arxiv_input}")

    # 如果是直接的arxiv_id格式
    else:
        # 移除arxiv:前缀（如果存在）
        if arxiv_input.lower().startswith('arxiv:'):
            arxiv_input = arxiv_input[6:]

        # 验证arxiv_id格式
        if not (_ARXIV_NEW_ID.match(arxiv_input) or _ARXIV_OLD_ID.match(arxiv_input)):
            raise ValueError(f"Invalid arXiv ID format: {arxiv_input}")

        return arxiv_input


def _to_abs_url(href: Optional[str]) -> Optional[str]:
    if not href:
        return None
    if "arxiv.org" in href:
        href = href.strip()
        if "/pdf/" in href:
            return href.replace("/pdf/", "/abs/").removesuffix(".pdf")
        return href
    if "paper.jsp" in href:
        qs = parse_qs(urlparse(href).query)
        r_val = (qs.get("r") or [None])[0]
        arxiv_id = _extract_arxiv_id_from_r(r_val or "")
        if arxiv_id:
            return f"https://arxiv.org/abs/{arxiv_id}"
    return None


def _to_pdf_url(abs_url: Optional[str]) -> Optional[str]:
    if not abs_url:
        return None
    if "arxiv.org/abs/" in abs_url:
        return abs_url.replace("/abs/", "/pdf/")
    return None


def _arxiv_fulltext_search(
        keywords: List[str],
        in_field: str = "",
        startat: Optional[int] = None,
        qid: Optional[str] = None,
        base: str = "https://search.arxiv.org/",
        session: Optional[requests.Session] = None,
) -> Tuple[str, str]:
    if session is None:
        session = _build_session()
    query = " ".join(k.strip() for k in keywords if k and k.strip())
    params = {"query": query}
    if in_field:
        params["in"] = in_field
    if startat is not None:
        params["startat"] = str(startat)
    if qid:
        params["qid"] = qid
    url = base + "?" + urlencode(params, quote_via=quote_plus)
    resp = session.get(url)
    resp.raise_for_status()
    return url, resp.text


def _parse_fulltext_results(html_text: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html_text, "html.parser")
    out: Dict[str, Any] = {
        "hits_text": "",
        "qid": None,
        "results": [],
        "next_url": None,
    }
    p = soup.find("p", class_="results")
    if p:
        out["hits_text"] = p.get_text(" ", strip=True)
        a = p.find("a", href=True)
        if a and "qid=" in a["href"]:
            qs = parse_qs(urlparse(a["href"]).query)
            out["qid"] = (qs.get("qid") or [None])[0]

    for td in soup.select("td.snipp"):
        a_title = td.find("a", class_="title", href=True)
        a_abs = td.find("a", class_="url", href=True)
        sp_snip = td.find("span", class_="snippet")

        title, authors, year = "", "", None
        if a_title:
            sp_author = a_title.find("span", class_="author")
            sp_title = a_title.find("span", class_="title")
            sp_year = a_title.find("span", class_="year")
            if sp_author:
                authors = sp_author.get_text(" ", strip=True)
            if sp_title:
                title = sp_title.get_text(" ", strip=True)
            if sp_year:
                try:
                    year = int(sp_year.get_text(strip=True))
                except Exception:
                    year = None

        url_intermediate = a_title["href"].strip() if a_title else None
        raw_url = a_abs["href"].strip() if a_abs else None
        url_abs = _to_abs_url(raw_url) or _to_abs_url(url_intermediate)
        url_pdf = _to_pdf_url(url_abs)
        snippet = sp_snip.get_text(" ", strip=True) if sp_snip else ""

        if title or url_abs or url_intermediate:
            out["results"].append({
                "title": title,
                "authors": authors,
                "year": year,
                "url_abs": url_abs,
                "url_pdf": url_pdf,
                "url_intermediate": url_intermediate,
                "snippet": snippet,
            })

    next_a = soup.find("a", string=lambda s: s and "Next" in s)
    if next_a and next_a.has_attr("href"):
        out["next_url"] = urljoin("https://search.arxiv.org/", next_a["href"])
        if not out["qid"]:
            qs = parse_qs(urlparse(out["next_url"]).query)
            out["qid"] = (qs.get("qid") or [None])[0]

    return out


def _extract_arxiv_info(html_content):
    """Extract comprehensive information from ArXiv HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract title
    title_element = soup.find('h1', class_='title mathjax')
    title = title_element.text.replace('Title:', '').strip() if title_element else ""

    # Extract abstract
    abstract_element = soup.find('blockquote', class_='abstract mathjax')
    abstract = abstract_element.text.replace('Abstract:', '').strip() if abstract_element else ""

    # Extract authors
    authors = []
    authors_div = soup.find('div', class_='authors')
    if authors_div:
        author_links = authors_div.find_all('a')
        authors = [author.text.strip() for author in author_links]

    # Extract arXiv ID from meta tags
    arxiv_id = ""
    arxiv_id_meta = soup.find('meta', {'name': 'citation_arxiv_id'})
    if arxiv_id_meta:
        arxiv_id = arxiv_id_meta.get('content', '')

    # Extract version from URL
    current_version = "v1"  # Default version
    og_url = soup.find('meta', {'property': 'og:url'})
    if og_url:
        url_content = og_url.get('content', '')
        version_match = re.search(r'v(\d+)', url_content)
        if version_match:
            current_version = f"v{version_match.group(1)}"

    # Extract category path (breadcrumbs)
    category_path = ""
    breadcrumb_div = soup.find('div', class_='header-breadcrumbs')
    if breadcrumb_div:
        # Extract all links in the breadcrumb
        breadcrumb_links = breadcrumb_div.find_all('a')
        if breadcrumb_links:
            # Skip the first link (home) and extract text from others
            breadcrumb_parts = []
            for link in breadcrumb_links[1:]:  # Skip home link
                text = link.text.strip()
                if text and text != arxiv_id:  # Skip the arXiv ID at the end
                    breadcrumb_parts.append(text)
            if breadcrumb_parts:
                category_path = " > ".join(breadcrumb_parts)

    # Extract subjects information (structured format)
    subjects = []
    primary_subject = ""
    subject_codes = []

    # First, extract from subheader (most complete subject information)
    subheader_div = soup.find('div', class_='subheader')
    if subheader_div:
        subheader_h1 = subheader_div.find('h1')
        if subheader_h1:
            # Extract the full subject hierarchy from subheader
            full_subject = subheader_h1.text.strip()
            primary_subject = full_subject

    # Extract detailed subjects from metatable
    metatable = soup.find('div', class_='metatable')
    if metatable:
        subjects_td = metatable.find('td', class_='tablecell subjects')
        if subjects_td:
            # Parse subjects like "Computation and Language (cs.CL); Machine Learning (cs.LG)"
            subjects_text = subjects_td.text.strip()
            subject_parts = [s.strip() for s in subjects_text.split(';') if s.strip()]

            for subject_part in subject_parts:
                # Parse format: "Subject Name (cs.XX)"
                match = re.search(r'^(.+?)\s*\(([^)]+)\)$', subject_part)
                if match:
                    subject_name = match.group(1).strip()
                    subject_code = match.group(2).strip()

                    subjects.append({
                        "name": subject_name,
                        "code": subject_code
                    })
                    subject_codes.append(subject_code)
                else:
                    # Handle case where there's just a code without parentheses
                    if re.match(r'^[a-z]+\.[A-Z]+$', subject_part):
                        subjects.append({
                            "name": subject_part,  # Use code as name if no display name
                            "code": subject_part
                        })
                        subject_codes.append(subject_part)
                    else:
                        # Just a name without code
                        subjects.append({
                            "name": subject_part,
                            "code": ""
                        })

    # Also extract subject codes from arXiv ID span as fallback
    arxiv_id_span = soup.find('span', class_='arxivid')
    if arxiv_id_span and not subject_codes:
        subject_match = re.search(r'\[(.*?)\]', arxiv_id_span.text)
        if subject_match:
            subject_code = subject_match.group(1)
            subject_codes.append(subject_code)
            subjects.append({
                "name": subject_code,
                "code": subject_code
            })

    # Extract submission date and last revised date from dateline
    submission_date = ""
    last_revised_date = ""
    dateline_div = soup.find('div', class_='dateline')
    if dateline_div:
        dateline_text = dateline_div.text
        # Pattern matches: [Submitted on 1 Jul 2025 (v1), last revised 15 Aug 2025 (this version, v5)]
        summary_match = re.search(r'Submitted on (\d{1,2} \w+ \d{4}) \(v1\), last revised (\d{1,2} \w+ \d{4}) \(this version, v(\d+)\)', dateline_text)
        if summary_match:
            submission_date = summary_match.group(1)
            last_revised_date = summary_match.group(2)
        else:
            # Fallback: try to extract individual dates
            submitted_match = re.search(r'Submitted on (\d{1,2} \w+ \d{4})', dateline_text)
            if submitted_match:
                submission_date = submitted_match.group(1)
            revised_match = re.search(r'last revised (\d{1,2} \w+ \d{4})', dateline_text)
            if revised_match:
                last_revised_date = revised_match.group(1)

    # Extract DOI
    doi = ""
    doi_element = soup.find('td', class_='tablecell arxivdoi')
    if doi_element:
        doi_link = doi_element.find('a')
        if doi_link:
            doi = doi_link.text.strip()

    # Extract PDF URL
    pdf_url = ""
    pdf_meta = soup.find('meta', {'name': 'citation_pdf_url'})
    if pdf_meta:
        pdf_url = pdf_meta.get('content', '')
    else:
        # Fallback to link search
        pdf_link = soup.find('a', {'href': re.compile(r'/pdf/\d+\.\d+')})
        if pdf_link:
            pdf_url = "https://arxiv.org" + pdf_link['href']

    # Extract submission history (submitter moved to top level)
    submission_history = []
    history_div = soup.find('div', class_='submission-history')
    if history_div:
        # Look for version information
        history_text = history_div.text

        # Extract version details and convert size to integer, date to ISO format
        version_pattern = r'\[v(\d+)\]\s+(\w+, \d{1,2} \w+ \d{4} \d{2}:\d{2}:\d{2} UTC) \(([\d,]+) KB\)'
        version_matches = re.findall(version_pattern, history_text)

        for version, date_str, size_str in version_matches:
            # Convert size string to integer (remove commas)
            size_kb = int(size_str.replace(',', ''))

            # Convert date to ISO format (simplified conversion)
            try:
                from datetime import datetime
                # Parse date like "Mon, 12 Jun 2017 17:57:34 UTC"
                date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S UTC')
                date_iso = date_obj.isoformat() + 'Z'
            except:
                date_iso = date_str  # Fallback to original string

            history_entry = {
                "version": f"v{version}",
                "date": date_iso,
                "size_kb": size_kb
            }
            submission_history.append(history_entry)

    # Extract submitter information (structured format)
    submitter = ""
    if history_div:
        submitter_match = re.search(r'From: ([^\[\]]+)', history_div.text)
        if submitter_match:
            submitter = submitter_match.group(1).strip()

    # Extract cite as information
    cite_as = []
    arxiv_id_link = soup.find('td', class_='tablecell arxivid')
    if arxiv_id_link:
        cite_text = arxiv_id_link.text.strip()
        cite_as.append(cite_text)

    # Extract comments (if any)
    comments = ""
    comments_element = soup.find('td', class_='comments mathjax')
    if comments_element:
        comments = comments_element.text.strip()

    # Extract journal reference (if any)
    journal_ref = ""
    journal_element = soup.find('td', class_='tablecell jref')
    if journal_element:
        journal_ref = journal_element.text.strip()

    # Extract ACM classification (if any)
    acm_class = ""
    acm_element = soup.find('td', class_='tablecell acm-class')
    if acm_element:
        acm_class = acm_element.text.strip()

    # Extract MSC classification (if any)
    msc_class = ""
    msc_element = soup.find('td', class_='tablecell msc-class')
    if msc_element:
        msc_class = msc_element.text.strip()

    return {
        "arxiv_id": arxiv_id,
        "current_version": current_version,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "comments": comments,
        "category_path": category_path,
        "subjects": subjects,
        "subject_codes": subject_codes,
        "primary_subject": primary_subject,
        "submission_date": submission_date,
        "last_revised_date": last_revised_date,
        "submission_history": submission_history,
        "submitter": submitter,
        "cite_as": cite_as,
        "doi": doi,
        "journal_reference": journal_ref,
        "acm_classification": acm_class,
        "msc_classification": msc_class,
        "pdf_url": pdf_url,
        "num_authors": len(authors)
    }


def _arxiv_id_to_url(arxiv_id: str) -> str:
    """
    将 arXiv ID 转换为 abs 页面 URL

    :param arxiv_id: arXiv ID，可以是 2507.01006 或 arxiv:2507.01006 格式
    :return: arXiv 摘要页面 URL
    """
    arxiv_id = arxiv_id.strip()
    if arxiv_id.startswith('arxiv:'):
        arxiv_id = arxiv_id[6:]  # 移除 'arxiv:' 前缀

    return f"https://arxiv.org/abs/{arxiv_id}"


@app.tool()
def get_arxiv_abs_page(arxiv_id):
    """
    获取 arXiv 摘要页面的详细信息并返回结构化的 JSON 数据

    :param arxiv_id: arXiv ID，例如 2507.01006 或 arxiv:2507.01006，
                    或者URL例如 https://arxiv.org/abs/2507.01006 或 https://arxiv.org/pdf/2507.01006
    :return: 包含论文详细信息的字典，包括标题、作者、摘要、提交历史等所有字段
    """
    logger.info(f"arxiv_id: {arxiv_id}")

    # 使用新的辅助函数提取arxiv_id
    clean_arxiv_id = _extract_arxiv_id_from_input(arxiv_id)
    logger.info(f"Extracted arxiv_id: {clean_arxiv_id}")

    url = _arxiv_id_to_url(clean_arxiv_id)
    logger.info(f"Constructed URL: {url}")

    sess = _build_session(timeout=30)

    # Make request
    resp = sess.get(url)
    resp.raise_for_status()

    # Extract information
    arxiv_info = _extract_arxiv_info(resp.content)

    logger.info(f"Extracted info for {arxiv_info.get('arxiv_id', 'unknown')}: {arxiv_info.get('title', 'no title')[:50]}...")
    logger.info(f"arxiv_info: {json.dumps(arxiv_info, ensure_ascii=False)}")

    return arxiv_info


@app.tool()
def download_arxiv_pdf(arxiv_id):
    """
    使用流式下载的方式从 arXiv 获取并保存 PDF 文件，返回文件的绝对路径

    :param arxiv_id: arXiv ID，例如 2507.01006 或 arxiv:2507.01006，
                    或者URL例如 https://arxiv.org/abs/2507.01006 或 https://arxiv.org/pdf/2507.01006
    :return: 保存到 ARXIV_DIR 下的文件绝对路径（例如：/absolute/path/to/files/2507.01006.pdf）
    """
    logger.info(f"arxiv_id: {arxiv_id}")

    if not ARXIV_DIR:
        raise RuntimeError("环境变量 ARXIV_DIR 未设置")
    os.makedirs(ARXIV_DIR, exist_ok=True)

    # 使用新的辅助函数提取arxiv_id
    clean_arxiv_id = _extract_arxiv_id_from_input(arxiv_id)
    logger.info(f"Extracted arxiv_id: {clean_arxiv_id}")

    url = f"https://arxiv.org/pdf/{clean_arxiv_id}.pdf"
    logger.info(f"Constructed PDF URL: {url}")

    filename = f"{clean_arxiv_id}.pdf"
    save_file = os.path.join(ARXIV_DIR, filename)
    absolute_path = os.path.abspath(save_file)

    logger.info(f"{filename} downloading...")

    sess = _build_session(timeout=30)
    with sess.get(url, stream=True) as resp:
        resp.raise_for_status()
        with open(save_file, "wb") as f:
            for chunk in resp.iter_content(chunk_size=128 * 1024):
                if chunk:
                    f.write(chunk)

    logger.info(f"{filename} downloaded")

    return absolute_path


@app.tool()
def search_arxiv_fulltext(
        keywords: str,
        # 限定搜索字段（如 "title" / "author" / "abstract"），默认空字符串表示不限定
        # in_field: str = "",
        # 结果起始位置（分页偏移，整型，可选）
        # startat: Optional[int] = None,
        #  查询会话 ID，用于延续同一检索会话翻页（可选）
        # qid: Optional[str] = None,
) -> dict:
    """
    在 arXiv 的“全文搜索”页发起查询并解析首屏结果，返回**结果条目列表**（而非整页元信息）

    :param keywords: 关键词列表，例如"glm-4.5|GSM8K"
    :return: `List[Dict]` 结果条目列表，每个条目包含如下键（字段可能因页面差异略有缺失）：
             - "title": 论文标题（str）
             - "authors": 作者列表示例字符串（str）
             - "snippet": 摘要片段/命中上下文（str，可能含换行）
             - "year": 年份（int）
             - "url_abs": arXiv 摘要页 URL（str）
             - "url_pdf": PDF 下载 URL（str）
             - "url_intermediate": 全文检索站点的中间跳转链接（str）
    """

    logger.info(f"keywords: {keywords}")
    # logger.info(f"in_field: {in_field}")
    # logger.info(f"startat: {startat}")
    # logger.info(f"qid: {qid}")

    in_field = ""
    startat = None
    qid = None

    sess = _build_session()

    logger.info("build_session ok")

    url, html = _arxiv_fulltext_search(keywords.split('|'), in_field, startat, qid, session=sess)

    logger.debug(f'html: {html}')

    parsed = _parse_fulltext_results(html)

    logger.debug(f'parsed: {parsed}')

    out = {
        "request_url": url,
        "hits_text": parsed.get("hits_text", ""),
        "qid": parsed.get("qid"),
        "next_url": parsed.get("next_url"),
        "results": parsed.get("results", []),
    }

    logger.info(f'results: {out["results"]}')

    return out["results"]


if __name__ == '__main__':
    app.run(transport='sse')
