from playwright.sync_api import sync_playwright
import re
import os

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
            
            # 【核心操作】强制浏览器等待 5 秒钟，让网页上的 JS 执行完毕，刷出真正的最新数据
            print("页面初始加载完成，正在等待 5 秒钟让 JS 刷新实时数据...")
            page.wait_for_timeout(5000) 
            
            # 抓取等待 5 秒后，网页最终渲染出来的真实 HTML 源码
            final_html = page.content()
            
            # 提取 <td> 中的 IP
            ips = re.findall(r'<td>\s*(\d{1,3}(?:\.\d{1,3}){3})\s*</td>', final_html)
            
            if ips:
                # 过滤掉我们已知的、刷新前的“旧数据占位符”
                # 包括图片1的 172.64.82.114 和你后来提到的 198.41.194.162
                fresh_ips = [ip for ip in ips if ip not in["172.64.82.114", "198.41.194.162"]]
                
                if fresh_ips:
                    real_ip = fresh_ips[0]
                    print("\n" + "="*40)
                    print(f"【成功提取刷新后的最新IP】: {real_ip}")
                    
                    # 抓取页面上的时间戳供参考，验证是否是最新的时间
                    times = re.findall(r'202\d/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', final_html)
                    if times:
                        print(f"页面显示的数据时间是: {times[0]}")
                    print("="*40)
                    
                    # 写入到根目录的 IP.txt 文件中
                    with open("IP.txt", "w", encoding="utf-8") as f:
                        f.write(real_ip)
                    print("已成功将 IP 写入到 IP.txt 文件！")
                else:
                    print("抓取到了IP，但全是被过滤掉的旧数据占位符。")
            else:
                print("未能从最终页面中找到任何 IP。")

        except Exception as e:
            print(f"浏览器运行出错: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    fetch_ip_and_save()
