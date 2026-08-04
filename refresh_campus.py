#!/usr/bin/env python3
"""
27届校招信息自动刷新脚本（增强版）
数据来源：牛客网 / 华中科技大学 / 华北电力大学 / 国资央企招聘平台
"""
import os
import sys
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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
        log(f"  加载现有数据失败: {e}")
        return []


def fetch_nowcoder():
    log("  正在抓取: 牛客网校招日程")
    results = []
    try:
        url = "https://www.nowcoder.com/school/schedule"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("a", href=True)
        found = 0
        for a in cards:
            text = a.get_text(" ", strip=True)
            href = a["href"]
            if "27" not in text:
                continue
            if not href.startswith("http"):
                href = urljoin("https://www.nowcoder.com", href)
            name = ""
            city = ""
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if "地点" in line:
                    city = line.split("：")[-1].split(":")[-1].strip()
                elif len(line) < 40 and not name and "收藏" not in line and "http" not in line:
                    name = line
            if name and len(name) > 1:
                results.append({
                    "企业名称": name,
                    "企业性质": "待确认",
                    "招聘岗位": "27届校招",
                    "工作城市": city or "详见官网",
                    "招聘时间段": "2026年8月-招满即止",
                    "要求专业": "详见官网",
                    "要求学历": "本科及以上",
                    "招聘网址": href
                })
                found += 1
        log(f"    牛客网: 找到 {found} 条")
    except Exception as e:
        log(f"    牛客网抓取失败: {e}")
    return results


def fetch_hust():
    log("  正在抓取: 华中科技大学就业网")
    results = []
    try:
        url = "https://job.hust.edu.cn/zpxx123123/index.htm"
        resp = requests.get(url, headers=HEADERS, timeout=15)
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
                results.append({
                    "企业名称": company_name,
                    "企业性质": "待确认",
                    "招聘岗位": "详见官网",
                    "工作城市": "详见官网",
                    "招聘时间段": "2026年8月-招满即止",
                    "要求专业": "详见官网",
                    "要求学历": "本科及以上",
                    "招聘网址": href
                })
        log(f"    华科就业网: 找到 {len(results)} 条")
    except Exception as e:
        log(f"    华科就业网抓取失败: {e}")
    return results


def fetch_ncepu():
    log("  正在抓取: 华北电力大学就业网")
    results = []
    try:
        url = "https://job.ncepu.edu.cn/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not any(kw in text for kw in ["2027", "27届"]):
                continue
            if not href.startswith("http"):
                href = urljoin("https://job.ncepu.edu.cn", href)
            company_name = text
            for rm in ["2027届", "27届", "毕业生", "校企联合培养", "宣讲会", "招聘", "简章", "公告", "已举办"]:
                company_name = company_name.replace(rm, "")
            company_name = re.sub(r'\d{4}-\d{2}-\d{2}', '', company_name)
            company_name = re.sub(r'\d{2}:\d{2}-\d{2}:\d{2}', '', company_name)
            company_name = company_name.strip(" -—_(周一二三四五六日)")
            if company_name and len(company_name) > 2:
                results.append({
                    "企业名称": company_name,
                    "企业性质": "待确认",
                    "招聘岗位": "详见官网",
                    "工作城市": "详见官网",
                    "招聘时间段": "2026年8月-招满即止",
                    "要求专业": "详见官网",
                    "要求学历": "本科及以上",
                    "招聘网址": href
                })
        log(f"    华电就业网: 找到 {len(results)} 条")
    except Exception as e:
        log(f"    华电就业网抓取失败: {e}")
    return results


def fetch_iguopin():
    log("  正在抓取: 国资央企招聘平台")
    results = []
    try:
        url = "https://cujiuye.iguopin.com/notice"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not any(kw in text for kw in ["2027", "27届", "校招"]):
                continue
            if not href.startswith("http"):
                href = urljoin("https://cujiuye.iguopin.com", href)
            company_name = text.replace("2027届", "").replace("校园招聘", "").replace("校招", "").strip()
            if company_name and len(company_name) > 2 and "查看详情" not in company_name:
                results.append({
                    "企业名称": company_name,
                    "企业性质": "央国企",
                    "招聘岗位": "详见官网",
                    "工作城市": "详见官网",
                    "招聘时间段": "2026年8月-招满即止",
                    "要求专业": "详见官网",
                    "要求学历": "本科及以上",
                    "招聘网址": href
                })
        log(f"    国聘网: 找到 {len(results)} 条")
    except Exception as e:
        log(f"    国聘网抓取失败: {e}")
    return results

def merge_data(existing_data, new_data):
    existing_names = {d["企业名称"] for d in existing_data}
    added = []
    for item in new_data:
        name = item["企业名称"]
        if name not in existing_names:
            existing_data.append(item)
            existing_names.add(name)
            added.append(name)
    log(f"  本次新增 {len(added)} 家企业:")
    for name in added:
        log(f"    + {name}")
    return existing_data, added


def save_data_file(data):
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        '"""', "27届校园招聘数据源",
        "数据结构: {企业名称, 企业性质, 招聘岗位, 工作城市, 招聘时间段, 要求专业, 要求学历, 招聘网址}",
        '"""', "import datetime", "",
        "# 当前更新时间",
        'LAST_UPDATED = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")  # 实际更新: ' + today,
        "", "RECRUITMENT_DATA = ["
    ]
    for item in data:
        lines.append("    {")
        for key, val in item.items():
            lines.append(f'        "{key}": "{val}",')
        lines.append("    },")
    lines.append("]")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def regenerate_html():
    log("  重新生成HTML表格...")
    result = subprocess.run(
        ["python3", os.path.join(SCRIPT_DIR, "generate_table.py")],
        capture_output=True, text=True, cwd=SCRIPT_DIR
    )
    log(f"  {result.stdout.strip()}")
    if result.stderr:
        log(f"  {result.stderr.strip()}")
    import shutil
    src = os.path.join(SCRIPT_DIR, "27届校招信息汇总表.html")
    dst = os.path.join(SCRIPT_DIR, "index.html")
    if os.path.exists(src):
        shutil.copy2(src, dst)
        log(f"  已同步 index.html")


def run_once():
    log("=" * 60)
    log("🚀 开始自动刷新27届校招信息...")
    existing_data = load_existing_data()
    log(f"  现有数据: {len(existing_data)} 家企业")
    all_new = []
    all_new.extend(fetch_nowcoder())
    all_new.extend(fetch_hust())
    all_new.extend(fetch_ncepu())
    all_new.extend(fetch_iguopin())
    log(f"  共抓取到 {len(all_new)} 条潜在新信息")
    merged_data, added = merge_data(existing_data, all_new)
    log(f"  合并后总计: {len(merged_data)} 家企业")
    save_data_file(merged_data)
    regenerate_html()
    log("✅ 刷新完成！")


if __name__ == "__main__":
    run_once()
