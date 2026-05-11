---
name: novel-scraper
description: 小说章节爬取工具 - 从笔趣阁类网站爬取小说章节内容，支持逐章下载、全本下载，自动处理分页。使用requests+BeautifulSoup，兼容22biqu等笔趣阁站点。
---

# 小说章节爬取工具

通用小说章节爬虫，支持笔趣阁类站点。

## 功能

- 单章下载：爬取指定章节完整内容
- 全本下载：从章节列表页自动爬取所有章节
- 自动翻页：处理章节内部分页
- 输出格式：TXT文件，支持合并为单文件

## 使用方法

### 1. 安装依赖

```bash
pip install requests beautifulsoup4
```

### 2. 爬取单章

```bash
python3 scripts/novel_scraper.py single --url https://www.22biqu.com/biqu96978/45523663.html
```

### 3. 爬取全部章节

```bash
python3 scripts/novel_scraper.py all --index https://www.22biqu.com/biqu96978/
```

### 4. 爬取指定范围章节

```bash
python3 scripts/novel_scraper.py range \
  --index https://www.22biqu.com/biqu96978/ \
  --start 1 \
  --end 50
```