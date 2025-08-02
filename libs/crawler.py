# 标准库
import re
import asyncio
from pathlib import Path

# 第三方库
import aiohttp
from bs4 import BeautifulSoup

# 自定义模块
from libs.log import logger
from libs.toml import read

BASE_URL = 'https://springsunday.net'
TORRENTS_URL = f'{BASE_URL}/torrents.php'

config = read("config/config.toml")
language = config["BASIC"].get("LANGUAGE", "zh-CN,zh")
cookie = config["BASIC"].get("COOKIE", "")
sec_ch_ua = config["BASIC"].get(
    "SEC_CH_UA", '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"'
)
sec_fetch_dest = config["BASIC"].get("SEC_FETCH_DEST", "document")
sec_fetch_mode = config["BASIC"].get("SEC_FETCH_MODE", "cors")
user_agent = config["BASIC"].get(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
)

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": language,
    "Cookie": cookie,
    "Priority": "u=0, i",
    "Sec-Ch-Ua": sec_ch_ua,
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": sec_fetch_dest,
    "Sec-Fetch-Mode": sec_fetch_mode,
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": user_agent,
}


def parse_size_to_gb(size_str: str) -> float:
    """将如 '12.3 GB', '900 MB', '1.2 TB' 的字符串转换为 GB 浮点数"""
    match = re.match(r'([\d.]+)\s*(GB|MB|TB)', size_str, re.IGNORECASE)
    if not match:
        return 0.0
    size, unit = float(match.group(1)), match.group(2).upper()
    if unit == 'GB':
        return size
    elif unit == 'MB':
        return size / 1024
    elif unit == 'TB':
        return size * 1024
    return 0.0


async def fetch_torrents():
    matched = []
    size_gb = 0.0
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(TORRENTS_URL, headers=headers) as resp:
                if resp.status != 200:
                    logger.warning(f"请求失败，状态码：{resp.status}")
                    return []

                html = await resp.text()
                soup = BeautifulSoup(html, "lxml")
                torrents = soup.find_all('tr', class_='sticky_bg')

                for row in torrents:
                    # 类型过滤
                    type_td = row.find('td')
                    img = type_td.find('img') if type_td else None
                    if not img or img.get('alt') not in {'Movies(电影)', 'TV Series(剧集)'}:
                        continue

                    # 标签过滤
                    if  img.get('alt') == 'Movies(电影)':
                        tag_div = row.find('div', class_='torrent-smalldescr')
                        if not tag_div:
                            continue
                        tag_text = tag_div.get_text()
                        if '官方' not in tag_text or '原生' not in tag_text:
                            continue
                    
                    elif img.get('alt') == 'TV Series(剧集)':
                        tag_div = row.find('div', class_='torrent-smalldescr')
                        if not tag_div:
                            continue
                        tag_text = tag_div.get_text()
                        if '官方' not in tag_text:
                            continue
                        tds = row.find_all('td')

                        for td in tds:
                            if 'MB' in td.text or 'GB' in td.text or 'TB' in td.text:
                                size_gb = parse_size_to_gb(td.text.strip())
                                break
                        if not (120 < size_gb < 150):
                            continue

                    
                    # 图标过滤
                    icon_spans = row.find_all('span', class_='torrent-icon')
                    skip_titles = {'放弃认领', '认领人数已满'}
                    if any(span.get('title') in skip_titles for span in icon_spans):
                        continue
                    
                    # 详情链接
                    link_tag = row.find('a', href=True, title=True)
                    if not link_tag:
                        continue
                    title = link_tag['title'].strip()
                    detail_url = BASE_URL + '/' + link_tag['href'].lstrip('/')
                    match = re.search(r'id=(\d+)', link_tag['href'])
                    if not match:
                        continue
                    torrent_id = match.group(1)

                    matched.append((torrent_id, title, detail_url))

    except Exception as e:
        logger.exception(f"抓取种子列表出错: {e}")
        return []

    return matched
