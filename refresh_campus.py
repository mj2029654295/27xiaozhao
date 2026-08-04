#!/usr/bin/env python3
"""
27届校招信息自动刷新脚本（增强版）
数据来源：
1. 牛客网校招日程 (nowcoder.com)
2. 华中科技大学就业网 (job.hust.edu.cn)
3. 华北电力大学就业网 (job.ncepu.edu.cn)
4. 国资央企招聘平台 (iguopin.com)

功能：
- 自动抓取新企业信息
- 与现有数据比对，只添加新企业
- 重新生成HTML表格
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
from urllib.parse import urljoin

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "campus_data.py")
HTML_FILE = os.path.join(SCRIPT_DIR, "27届校招信息汇总表.html")
LOG_FILE = os.path.join(SCRIPT_DIR, "refresh.log")
REFRESH_INTERVAL = 6 * 3600

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_existing_data():
    try:
        sys.path.insert(0, SCRIPT_DIR)
        if 'campus_data' in sys.modules:
            del sys.modules['campus_data']
        import campus_data
        return campus_data.RECRUITMENT_DATA
    except Exception as e:
        log(f"  ⚠️ 加载现有数据失败: {e}")
        return []


def fetch_nowcoder():
    log("  正在抓取: 牛客网校招日程")
    results = []
    try:
        url = "https://www.nowcoder.com/school/schedule?type=2"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if len(text) < 3:
                continue
            if not any(kw in text for kw in ["27届", "27秋招", "2027"]):
                continue
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            company_name = ""
            city = ""
            recruit_type = "27届校招"
            for line in lines:
                if "地点：" in line or "地点:" in line:
                    city = re.sub(r"地点[：:]", "", line).strip()
                elif "27届" in line or "27秋招" in line or "2027" in line:
                    recruit_type = line.split("丨")[0].strip() if "丨" in line else line
                elif line and not company_name and "收录" not in line and "收藏" not in line:
                    if 2 < len(line) < 30:
                        company_name = line
            parent = a.parent
            if parent:
                parent_text = parent.get_text(separator="\n", strip=True)
                parent_lines = [l.strip() for l in parent_text.split("\n") if l.strip()]
                for line in parent_lines:
                    if "地点：" in line or "地点:" in line:
                        city = re.sub(r"地点[：:]", "", line).strip()
                    elif not company_name and 2 < len(line) < 30 and "收录" not in line and "收藏" not in line and "27" not in line and "2027" not in line:
                        if not any(skip in line for skip in ["立即投递", "官网投递", "收藏", "http"]):
                            company_name = line
            if not href.startswith("http"):
                href = urljoin("https://www.nowcoder.com", href)
            if company_name and len(company_name) > 1:
                results.append({
                    "企业名称": company_name,
                    "企业性质": "待确认",
                    "招聘岗位": recruit_type,
                    "工作城市": city if city else "详见官网",
                    "招聘时间段": "2026年8月-招满即止",
                    "要求专业": "详见官网",
                    "要求学历": "本科及以上",
                    "招聘网址": href
                })
        log(f"    牛客网: 找到 {len(results)} 条27届校招信息")
    except Exception as e:
        log(f"    ⚠️ 牛客网抓取失败: {e}")
    return results


def fetch_hust():
    log("  正在抓取: 华中科技大学就业网")
    results = []
    try:
        url = "https://job.hust.edu.cn/zpxx123123/index.htm"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not any(kw in text for kw in ["2027", "27届"]):
                continue
            if not href.startswith("http"):
                href = urljoin("https://job.hust.edu.cn", href)
            company_name = text
            for rm in ["2027届校园招聘", "2027届", "27届", "招聘简章", "校园招聘", "招聘信息", "招聘公告", "2027年校招提前批", "2027年", "校招", "提前批"]:
                company_name = company_name.replace(rm, "")
            company_name = company_name.strip(" -—_")
            if company_name and len(company_name) > 2 and "毕业生生源" not in company_name:
        
