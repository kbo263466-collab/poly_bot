import requests
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

def get_poly_data():
    """获取 Polymarket 赔率并进行双语逻辑处理"""
    url = "https://gamma-api.polymarket.com/events?limit=10&active=true&closed=false"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        report = "【💰 Polymarket 全球热门事件赔率 (Bilingual)】\n"
        report += "=" * 50 + "\n\n"
        
        # 汉化映射词典
        translations = {
            "Presidential": "总统大选",
            "Winner": "获胜者",
            "Election": "选举",
            "US": "美国",
            "Federal": "联邦"
        }
        
        for event in data:
            title_en = event.get('title', 'N/A')
            title_cn = title_en
            for eng, chn in translations.items():
                title_cn = title_cn.replace(eng, chn)
            
            markets = event.get('markets', [{}])[0]
            group = markets.get('groupNames', ['Yes', 'No'])
            prices = markets.get('outcomePrices', ['0', '0'])
            
            # 概率计算与容错处理
            try:
                c1 = f"{float(prices[0])*100:.1f}%" if prices else "N/A"
                c2 = f"{float(prices[1])*100:.1f}%" if len(prices) > 1 else "N/A"
            except:
                c1, c2 = "N/A", "N/A"
            
            report += f"📍 {title_cn}\n"
            report += f"   (EN: {title_en})\n"
            report += f"   📊 胜率预期: {group[0]}({c1}) | {group[1]}({c2})\n\n"
        return report
    except Exception as e:
        return f"❌ 赔率数据抓取失败: {str(e)}\n"

def get_news_data():
    """获取全球前沿新闻"""
    # 使用 NewsAPI 公共接口
    url = "https://newsapi.org/v2/top-headlines?sources=google-news&pageSize=10&apiKey=02392437e56847849e7550f28e67f08b"
    try:
        response = requests.get(url, timeout=15)
        articles = response.json().get('articles', [])
        report = "【🌍 全球前沿热门新闻汇总 (Bilingual)】\n"
        report += "=" * 50 + "\n"
        report += "(注：以下为全球热点新闻摘要)\n\n"
        
        for i, art in enumerate(articles, 1):
            title = art.get('title', 'No Title')
            source = art.get('source', {}).get('name', 'Unknown')
            report += f"{i}. {title} [{source}]\n\n"
        return report
    except Exception as e:
        return "❌ 新闻数据抓取失败\n"

def send_email(content):
    """发送邮件（全加密变量保护版）"""
    mail_host = "smtp.qq.com"
    
    # 从 GitHub Secrets 读取环境变量
    mail_user = os.getenv("MAIL_USER")
    mail_pass = os.getenv("MAIL_PASS")
    mail_receiver = os.getenv("MAIL_RECEIVER")

    # 安全检查
    if not all([mail_user, mail_pass, mail_receiver]):
        print("❌ 错误：环境变量 (USER/PASS/RECEIVER) 配置不全，请检查 GitHub Secrets。")
        return False

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = f"M4_Bot_Reporter <{mail_user}>"
    message['To'] = mail_receiver
    message['Subject'] = Header(f"🌍 全球资讯双语日报 ({now_str})", 'utf-8')

    # 重试机制
    for attempt in range(3):
        try:
            smtp = smtplib.SMTP_SSL(mail_host, 465, timeout=15)
            smtp.login(mail_user, mail_pass)
            smtp.sendmail(mail_user, [mail_receiver], message.as_string())
            smtp.quit()
            print(f"✅ {now_str} 邮件已成功送达！")
            return True
        except Exception as e:
            print(f"⚠️ 第 {attempt + 1} 次尝试失败: {e}")
            time.sleep(5)
    return False

if __name__ == "__main__":
    print("🚀 正在通过 M4 Mac 指令启动云端抓取任务...")
    
    # 数据汇总
    news_part = get_news_data()
    poly_part = get_poly_data()
    
    final_report = "您好！这是为您精心准备的全球双语日报：\n\n"
    final_report += news_part + "\n" + "="*60 + "\n\n" + poly_part
    final_report += "\n---\n本报告由 GitHub Actions 自动化生成。报告时间：" + datetime.now().strftime("%Y-%m-%d %H:%M")
    
    send_email(final_report)