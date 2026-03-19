from playwright.sync_api import sync_playwright
import re
import os

# ================= 配置区 =================
# 你想要获取表格中第几行的 IP？ (填 1 就是第一行，填 2 就是第二行)
TARGET_ROW = 2
# ==========================================

def fetch_ip_and_save():
    with sync_playwright() as p:
        print("启动无头 Chromium 浏览器...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = "https://api.uouin.com/cloudflare.html"
        print(f"正在访问页面: {url}")
        
        try:
            # 访问网页并等待基础 DOM 加载
            page.goto(url, wait_until="domcontentloaded")
            
            # 强制等待 5 秒钟，让网页上的 JS 执行完毕，刷出真正的最新数据
            print("页面初始加载完成，正在等待 5 秒钟让 JS 刷新实时数据...")
            page.wait_for_timeout(5000) 
            
            # 抓取等待 5 秒后，网页最终渲染出来的真实 HTML 源码
            final_html = page.content()
            
            # 提取 <td> 中的 IP
            ips = re.findall(r'<td>\s*(\d{1,3}(?:\.\d{1,3}){3})\s*</td>', final_html)
            
            if ips:
                # 过滤掉已知的“旧数据占位符”
                fresh_ips = [ip for ip in ips if ip not in["172.64.82.114", "198.41.194.162"]]
                
                # 检查抓取到的有效 IP 数量是否满足我们要提取的行数
                if len(fresh_ips) >= TARGET_ROW:
                    # 列表的索引是从 0 开始的，所以第 2 行对应索引 1
                    target_index = TARGET_ROW - 1
                    real_ip = fresh_ips[target_index]
                    
                    print("\n" + "="*40)
                    print(f"【成功提取刷新后的 第 {TARGET_ROW} 行 最新IP】: {real_ip}")
                    
                    # 抓取页面上的时间戳供参考
                    times = re.findall(r'202\d/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', final_html)
                    if len(times) >= TARGET_ROW:
                        print(f"该 IP 对应的数据时间是: {times[target_index]}")
                    print("="*40)
                    
                    # 写入到 IP.txt 文件中
                    with open("IP.txt", "w", encoding="utf-8") as f:
                        f.write(real_ip)
                    print("已成功将 IP 写入到 IP.txt 文件！")
                else:
                    print(f"抓取到了有效IP，但总数只有 {len(fresh_ips)} 个，无法获取第 {TARGET_ROW} 行的数据。")
            else:
                print("未能从最终页面中找到任何 IP。")

        except Exception as e:
            print(f"浏览器运行出错: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    fetch_ip_and_save()
