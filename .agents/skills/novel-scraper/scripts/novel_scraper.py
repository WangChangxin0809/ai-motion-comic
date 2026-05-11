#!/usr/bin/env python3
"""
小说章节爬取工具 - 支持笔趣阁类站点
用法:
  python3 novel_scraper.py single --url https://www.22biqu.com/biqu96978/45523663.html
  python3 novel_scraper.py all --index https://www.22biqu.com/biqu96978/
  python3 novel_scraper.py range --index https://www.22biqu.com/biqu96978/ --start 1 --end 50
"""

import os
import sys
import re
import json
import time
import argparse
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.22biqu.com/",
}
DELAY = 1.5  # 请求间隔，避免被封


def fetch_page(url: str, encoding: str = "utf-8") -> str:
    """获取页面HTML"""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = encoding
    return resp.text


def parse_chapter(html: str) -> dict:
    """
    解析章节页面，返回 {title, content, next_url, prev_url, index_url}
    """
    soup = BeautifulSoup(html, "html.parser")

    # 标题: h1.title
    title_tag = soup.select_one("h1.title") or soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "未知标题"

    # 正文: div#content
    content_div = soup.select_one("div#content")
    paragraphs = []
    if content_div:
        for p in content_div.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

    content = "\n".join(paragraphs)

    # 导航链接
    next_url = None
    prev_url = None
    index_url = None

    for a in soup.find_all("a"):
        a_id = a.get("id", "")
        txt = a.get_text(strip=True)
        href = a.get("href", "")
        if a_id == "next_url" and href and "没有了" not in txt:
            next_url = urljoin("https://www.22biqu.com", href)
        elif a_id == "prev_url" and href and "没有了" not in txt:
            prev_url = urljoin("https://www.22biqu.com", href)
        elif a_id == "info_url" and href:
            index_url = urljoin("https://www.22biqu.com", href)

    return {
        "title": title,
        "content": content,
        "next_url": next_url,
        "prev_url": prev_url,
        "index_url": index_url,
    }


def fetch_full_chapter(url: str) -> dict:
    """
    获取完整章节（自动翻页）
    某些章节被拆成多页（_2.html, _3.html...）
    """
    all_content = []
    title = None
    current_url = url
    page_count = 0

    while current_url and page_count < 20:  # 最多20页
        page_count += 1
        print(f"    读取分页 {page_count}: {current_url.split('/')[-1]}", end="\r")

        html = fetch_page(current_url)
        result = parse_chapter(html)

        if title is None:
            title = result["title"]

        all_content.append(result["content"])

        # 检查是否有下一页
        if result.get("next_url"):
            # 判断下一页是否是同一章节的分页（URL末尾的 _2, _3 后缀）
            next_path = urlparse(result["next_url"]).path
            current_path = urlparse(current_url).path
            if next_path != current_path and result["next_url"] != current_url:
                current_url = result["next_url"]
                time.sleep(DELAY)
            else:
                break
        else:
            break

    print(" " * 60, end="\r")  # 清除状态行
    return {
        "title": title or "未知标题",
        "content": "\n\n".join(all_content),
        "pages": page_count,
    }


def parse_chapter_list(html: str, index_url: str) -> list:
    """
    从目录页解析章节列表
    """
    soup = BeautifulSoup(html, "html.parser")
    chapters = []

    # 通常章节链接在 dl > dd > a 中
    for a in soup.select("dl dd a"):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if href and title and href.endswith(".html"):
            full_url = urljoin(index_url, href)
            chapters.append({"title": title, "url": full_url})

    # 备选: 查找所有指向章节的链接
    if not chapters:
        for a in soup.select("#list a"):
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if href and title and href.endswith(".html"):
                full_url = urljoin(index_url, href)
                chapters.append({"title": title, "url": full_url})

    return chapters


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def scrape_single(url: str, output_dir: str = "./novels"):
    """爬取单个章节"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"📖 开始爬取: {url}")
    result = fetch_full_chapter(url)

    print(f"📝 标题: {result['title']}")
    print(f"📄 页数: {result['pages']}")
    print(f"📊 字数: {len(result['content'])}")

    filename = sanitize_filename(result["title"]) + ".txt"
    filepath = Path(output_dir) / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result["title"] + "\n\n")
        f.write(result["content"])

    print(f"✅ 已保存: {filepath}")
    return filepath


def scrape_all(index_url: str, output_dir: str = "./novels"):
    """爬取全部章节"""
    print(f"📚 获取章节目录: {index_url}")
    html = fetch_page(index_url)
    chapters = parse_chapter_list(html, index_url)

    if not chapters:
        print("❌ 未找到章节列表，请检查URL")
        return

    print(f"📋 共找到 {len(chapters)} 章")
    novel_name = sanitize_filename(
        chapters[0]["title"].split("第")[0].strip() if chapters else "novel"
    )
    novel_dir = Path(output_dir) / novel_name
    novel_dir.mkdir(parents=True, exist_ok=True)

    all_text = []
    total = len(chapters)

    for i, ch in enumerate(chapters, 1):
        print(f"\n[{i}/{total}] {ch['title']}")
        try:
            result = fetch_full_chapter(ch["url"])
            all_text.append(f"\n\n{'='*40}")
            all_text.append(result["title"])
            all_text.append(f"{'='*40}\n\n")
            all_text.append(result["content"])

            # 保存单章
            filename = sanitize_filename(ch["title"]) + ".txt"
            filepath = novel_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(result["title"] + "\n\n")
                f.write(result["content"])
        except Exception as e:
            print(f"  ❌ 失败: {e}")

        time.sleep(DELAY)

    # 合并所有章节
    combined_path = novel_dir / f"{novel_name}_全本.txt"
    with open(combined_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_text))

    print(f"\n✅ 完成! 共 {len(all_text)//3} 章")
    print(f"📁 目录: {novel_dir}")
    print(f"📄 合并: {combined_path}")


def scrape_range(index_url: str, start: int, end: int, output_dir: str = "./novels"):
    """爬取指定范围的章节"""
    print(f"📚 获取章节目录: {index_url}")
    html = fetch_page(index_url)
    chapters = parse_chapter_list(html, index_url)

    if not chapters:
        print("❌ 未找到章节列表")
        return

    # 截取范围
    chapters = chapters[max(0, start - 1) : min(end, len(chapters))]
    print(f"📋 爬取范围: 第{start}章 ~ 第{end}章 ({len(chapters)}章)")

    novel_name = sanitize_filename(
        chapters[0]["title"].split("第")[0].strip() if chapters else "novel"
    )
    novel_dir = Path(output_dir) / novel_name
    novel_dir.mkdir(parents=True, exist_ok=True)

    all_text = []
    total = len(chapters)

    for i, ch in enumerate(chapters, 1):
        print(f"\n[{start + i - 1}/{start + total - 1}] {ch['title']}")
        try:
            result = fetch_full_chapter(ch["url"])
            all_text.append(f"\n\n{'='*40}")
            all_text.append(result["title"])
            all_text.append(f"{'='*40}\n\n")
            all_text.append(result["content"])
        except Exception as e:
            print(f"  ❌ 失败: {e}")

        time.sleep(DELAY)

    combined_path = novel_dir / f"{novel_name}_{start}-{end}.txt"
    with open(combined_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_text))

    print(f"\n✅ 完成!")
    print(f"📄 已保存: {combined_path}")


def main():
    parser = argparse.ArgumentParser(description="小说章节爬取工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    p_single = subparsers.add_parser("single", help="爬取单章")
    p_single.add_argument("--url", "-u", required=True, help="章节URL")
    p_single.add_argument("--output", "-o", default="./novels", help="输出目录")

    p_all = subparsers.add_parser("all", help="爬取全部章节")
    p_all.add_argument("--index", "-i", required=True, help="目录页URL")
    p_all.add_argument("--output", "-o", default="./novels", help="输出目录")

    p_range = subparsers.add_parser("range", help="爬取指定范围章节")
    p_range.add_argument("--index", "-i", required=True, help="目录页URL")
    p_range.add_argument("--start", "-s", type=int, required=True, help="起始章节号")
    p_range.add_argument("--end", "-e", type=int, required=True, help="结束章节号")
    p_range.add_argument("--output", "-o", default="./novels", help="输出目录")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "single":
            scrape_single(args.url, args.output)
        elif args.command == "all":
            scrape_all(args.index, args.output)
        elif args.command == "range":
            scrape_range(args.index, args.start, args.end, args.output)
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()