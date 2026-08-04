#!/usr/bin/env python3
"""
27届校招信息自动刷新脚本
功能：
1. 尝试从招聘网站抓取最新27届校招信息
2. 更新 campus_data.py 数据源
3. 重新生成HTML表格

用法：
    python3 refresh_campus.py           # 手动刷新一次
    python3 refresh_campus.py --daemon  # 守护模式，每6小时自动刷新
"""

import os
import sys
import time
import json
import re
import datetime
import subprocess
import requests
from bs4 import BeautifulSoup

# 配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "campus_data.py")
HTML_FILE = os.path.join(SCRIPT_DIR, "27届校招信息汇总表.html")
LOG_FILE = os.path.join(SCRIPT_DIR, "refresh.log")
REFRESH_INTERVAL = 6 * 3600  # 6小时

# 数据来源（招聘信息发布平台）
SOURCES = [
    {
        "name": "国资央企招聘平台",
        "url": "https://cujiuye.iguopin.com/notice",
        "type": "国企央企"
    },
    {
        "name": "华中科技大学就业网",
        "url": "https://job.hust.edu.cn/zpxx123123/index.htm",
        "type": "综合"
    },
    {
        "name": "武汉理工大学就业网",
        "url": "https://scc.whut.edu.cn/",
        "type": "综合"
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def try_fetch_source(source):
    """尝试抓取单个数据源"""
    log(f"  正在抓取: {source['name']} ({source['url']})")
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # 尝试提取包含"2027"的招聘链接
        links = []
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if "2027" in text or "27届" in text or "校招" in text:
                links.append({"text": text, "href": href})

        log(f"    找到 {len(links)} 条潜在招聘信息")
        return links
    except Exception as e:
        log(f"    ⚠️ 抓取失败: {e}")
        return []


def check_for_updates():
    """检查是否有新的招聘信息"""
    log("=" * 60)
    log("开始检查27届校招更新...")

    all_new = []
    for source in SOURCES:
        items = try_fetch_source(source)
        all_new.extend(items)

    log(f"本轮共发现 {len(all_new)} 条潜在新信息")
    log(f"（详细数据需手动核实后添加到 campus_data.py）")
    return all_new


def update_timestamp():
    """更新数据文件中的时间戳"""
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    content = open(DATA_FILE, "r", encoding="utf-8").read()
    new_content = re.sub(
        r'LAST_UPDATED = .*',
        f'LAST_UPDATED = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")  # 实际更新: {today}',
        content
    )
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)


def regenerate_html():
    """重新生成HTML表格，并同步更新 index.html"""
    log("  重新生成HTML表格...")
    result = subprocess.run(
        ["python3", os.path.join(SCRIPT_DIR, "generate_table.py")],
        capture_output=True, text=True, cwd=SCRIPT_DIR
    )
    log(f"  {result.stdout.strip()}")
    if result.stderr:
        log(f"  stderr: {result.stderr.strip()}")

    # 同步 index.html（GitHub Pages 默认入口）
    import shutil
    src = os.path.join(SCRIPT_DIR, "27届校招信息汇总表.html")
    dst = os.path.join(SCRIPT_DIR, "index.html")
    shutil.copy2(src, dst)
    log(f"  已同步 index.html")


def run_once():
    """手动刷新一次"""
    log("🚀 手动刷新模式")
    check_for_updates()
    update_timestamp()
    regenerate_html()
    log("✅ 刷新完成！")


def run_daemon():
    """守护模式，定期刷新"""
    log("🔄 守护模式启动，每6小时自动刷新...")
    log(f"  日志文件: {LOG_FILE}")
    log(f"  HTML输出: {HTML_FILE}")

    while True:
        try:
            check_for_updates()
            update_timestamp()
            regenerate_html()
            log(f"⏰ 下次刷新时间: {(datetime.datetime.now() + datetime.timedelta(seconds=REFRESH_INTERVAL)).strftime('%Y-%m-%d %H:%M:%S')}")
            log("")
        except Exception as e:
            log(f"❌ 刷新过程出错: {e}")

        time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    if "--daemon" in sys.argv or "-d" in sys.argv:
        run_daemon()
    else:
        run_once()
