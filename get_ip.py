from playwright.sync_api import sync_playwright
import re
import os
import requests

# ================= 配置区 =================
# 映射配置：(目标行号, 环境变量里的域名Key, 环境变量里的ZoneID Key)
CONFIG = [
    (2, "CF_RECORD_NAME_1", "CF_ZONE_ID_1"), # 第2行 -> 域名1
    (3, "CF_RECORD_NAME_2", "CF_ZONE_ID_2")  # 第3行 -> 域名2
]
# ==========================================

def update_cloudflare_dns(new_ip, record_name, zone_id):
    """通用的 DNS 更新函数，支持不同的 Zone ID"""
    token = os.environ.get("CF_API_TOKEN")

    if not record_name or not zone_id:
        print(f"\n[!] 跳过更新：未配置域名或 Zone ID。")
        return

    print(f"\n开始检查并更新 Cloudflare DNS: {record_name} (Zone: {zone_id})")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        # 1. 查找现有记录
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={record_name}&type=A"
        resp = requests.get(url, headers=headers).json()
        
        payload = {
            "type": "A", "name": record_name, "content": new_ip, "ttl": 60, "proxied": False
        }

        # 2. 如果不存在则创建
        if not resp.get("result"):
            print(f"[*] 未找到记录，正在自动创建...")
            create_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
            create_resp = requests.post(create_url, headers=headers, json=payload).json()
            if create_resp.get("success"):
                print(f"[√] {record_name} 创建成功: {new_ip}")
            return

        # 3. 如果存在则更新
        record = resp["result"][0]
        record_id = record["id"]
        old_ip = record["content"]

        if old_ip == new_ip:
            print(f"[#] {record_name} 已指向 {new_ip}，无需更改。")
            return

        print(f"[*] 发现新 IP！将 {record_name} 从 {old_ip} 更改为 {new_ip}...")
        update_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
        update_resp = requests.put(update_url, headers=headers, json=payload).json()
        
        if update_resp.get("success"):
            print(f"[√] {record_name} 更新成功！")
        else:
            print(f"[x] {record_name} 更新失败: {update_resp.get('errors')}")

    except Exception as e:
        print(f"[!] API 调用异常: {e}")

def fetch_ip_and_save():
    with sync_playwright() as p:
        print("启动无头 Chromium 浏览器...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = "https://api.uouin.com/cloudflare.html"
        
        try:
            page.goto(url, wait_until="domcontentloaded")
            print("等待 5 秒加载数据...")
            page.wait_for_timeout(5000) 
            
            final_html = page.content()
            ips = re.findall(r'<td>\s*(\d{1,3}(?:\.\d{1,3}){3})\s*</td>', final_html)
            
            if ips:
                # 过滤旧占位 IP
                fresh_ips = [ip for ip in ips if ip not in["172.64.82.114", "198.41.194.162"]]
                results = []

                # 根据配置循环处理
                for row_num, name_key, zone_key in CONFIG:
                    record_name = os.environ.get(name_key)
                    zone_id = os.environ.get(zone_key)

                    if len(fresh_ips) >= row_num:
                        target_ip = fresh_ips[row_num - 1]
                        # 先执行 Cloudflare 更新操作
                        update_cloudflare_dns(target_ip, record_name, zone_id)
                        # 【修改点】仅将 IP 加入结果列表，不包含域名信息
                        results.append(target_ip)
                    else:
                        print(f"数据不足，无法提取第 {row_num} 行。")

                # 将两个 IP 写入文件，每个 IP 占一行
                if results:
                    with open("IP.txt", "w", encoding="utf-8") as f:
                        f.write("\n".join(results))
                    print(f"\n[√] 两个优选 IP 已保存至 IP.txt")
            else:
                print("未匹配到 IP 数据。")

        except Exception as e:
            print(f"浏览器运行出错: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    fetch_ip_and_save()
