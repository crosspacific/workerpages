from playwright.sync_api import sync_playwright
import re
import os
import requests  # 新增用于发送 API 请求的库

# ================= 配置区 =================
TARGET_ROW = 2  # 提取第 2 行的 IP
# ==========================================

def update_cloudflare_dns(new_ip):
    """调用 Cloudflare API 自动创建或更新 DNS 记录"""
    token = os.environ.get("CF_API_TOKEN")
    zone_id = os.environ.get("CF_ZONE_ID")
    record_name = os.environ.get("CF_RECORD_NAME")

    if not token or not zone_id or not record_name:
        print("\n[!] 未配置 Cloudflare 环境变量，跳过 DNS 绑定步骤。")
        return

    print(f"\n开始检查并更新 Cloudflare DNS: {record_name}")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        # 1. 查找域名现有的解析记录
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={record_name}&type=A"
        resp = requests.get(url, headers=headers).json()
        
        # 定义要写入的记录内容
        payload = {
            "type": "A",
            "name": record_name,
            "content": new_ip,
            "ttl": 60,
            "proxied": False  # 确保小黄云是关闭状态
        }

        # 2. 如果记录不存在，则【新建记录】
        if not resp.get("result"):
            print(f"[*] 未找到 {record_name} 的现有记录，正在自动创建新记录...")
            create_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
            create_resp = requests.post(create_url, headers=headers, json=payload).json()
            
            if create_resp.get("success"):
                print("[√] 记录创建成功！你的节点现在起飞了！")
            else:
                print(f"[x] 创建失败: {create_resp.get('errors')}")
            return

        # 3. 如果记录存在，则【更新记录】
        record = resp["result"][0]
        record_id = record["id"]
        old_ip = record["content"]

        if old_ip == new_ip:
            print(f"[#] 当前 DNS 记录已经是 {new_ip}，完全一致，无需重复更新。")
            return

        print(f"[*] 发现新 IP！正在将 {record_name} 从 {old_ip} 更改为 {new_ip}...")
        update_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
        
        update_resp = requests.put(update_url, headers=headers, json=payload).json()
        
        if update_resp.get("success"):
            print("[√] Cloudflare DNS 记录更新成功！")
        else:
            print(f"[x] Cloudflare 更新失败: {update_resp.get('errors')}")

    except Exception as e:
        print(f"[!] API 请求发生异常: {e}")


def fetch_ip_and_save():
    with sync_playwright() as p:
        print("启动无头 Chromium 浏览器...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = "https://api.uouin.com/cloudflare.html"
        print(f"正在访问页面: {url}")
        
        try:
            page.goto(url, wait_until="domcontentloaded")
            print("正在等待 5 秒钟让 JS 刷新实时数据...")
            page.wait_for_timeout(5000) 
            
            final_html = page.content()
            ips = re.findall(r'<td>\s*(\d{1,3}(?:\.\d{1,3}){3})\s*</td>', final_html)
            
            if ips:
                fresh_ips = [ip for ip in ips if ip not in["172.64.82.114", "198.41.194.162"]]
                if len(fresh_ips) >= TARGET_ROW:
                    target_index = TARGET_ROW - 1
                    real_ip = fresh_ips[target_index]
                    
                    print("\n" + "="*40)
                    print(f"【成功提取 第 {TARGET_ROW} 行 最新IP】: {real_ip}")
                    print("="*40)
                    
                    # 写入到 IP.txt 文件
                    with open("IP.txt", "w", encoding="utf-8") as f:
                        f.write(real_ip)
                    print("已将最新 IP 保存到 IP.txt。")
                    
                    # 触发 Cloudflare 更新
                    update_cloudflare_dns(real_ip)

                else:
                    print(f"抓取到了有效IP，但总数不足，无法获取第 {TARGET_ROW} 行。")
            else:
                print("未能从最终页面中找到任何 IP。")

        except Exception as e:
            print(f"浏览器运行出错: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    fetch_ip_and_save()
