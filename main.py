import requests
import os
import smtplib
import time
import json
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime
import logging

# 配置日志
log_dir = "/Volumes/chao/poly_bot/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_poly_data():
    """获取 Polymarket 赔率（修复版）- 筛选10%-95%概率的事件"""
    url = "https://gamma-api.polymarket.com/events?limit=10&active=true&closed=false"
    try:
        logger.info(f"Fetching Polymarket data from {url}")
        response = requests.get(url, timeout=15)
        data = response.json()
        logger.info(f"Polymarket API returned {len(data) if isinstance(data, list) else 'N/A'} events")

        report = "📊 POLYMARKET REAL-TIME ODDS (Filtered 10%-95%)\n"
        report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        if not isinstance(data, list):
            error_msg = f"❌ Polymarket API 返回格式异常: {type(data)}\n"
            logger.error(error_msg)
            return error_msg

        valid_events = []  # 存储符合条件的事件
        filtered_count = 0  # 记录被过滤的事件数

        for event in data[:10]:  # 最多显示10条
            title = event.get('title', 'N/A')
            markets = event.get('markets', [])

            if not markets or not isinstance(markets, list):
                continue

            market = markets[0]
            if not isinstance(market, dict):
                continue

            # groupNames 可能是 None
            group = market.get('groupNames') or ['Yes', 'No']

            # outcomePrices 可能是 JSON 字符串，如 '["0.65", "0.35"]'
            prices_raw = market.get('outcomePrices', '["0", "0"]')
            if isinstance(prices_raw, str):
                try:
                    prices = json.loads(prices_raw)
                except json.JSONDecodeError:
                    prices = ['0', '0']
            else:
                prices = prices_raw

            # 确保 prices 是列表且有两个元素
            if not isinstance(prices, list) or len(prices) < 2:
                prices = ['0', '0']

            try:
                p1 = float(prices[0]) * 100
                p2 = float(prices[1]) * 100

                # 筛选条件：概率在10%-95%之间
                if 10 <= p1 <= 95 and 10 <= p2 <= 95:
                    g1 = group[0] if len(group) > 0 else 'Yes'
                    g2 = group[1] if len(group) > 1 else 'No'
                    valid_events.append({
                        'title': title,
                        'g1': g1,
                        'g2': g2,
                        'p1': p1,
                        'p2': p2
                    })
                    logger.debug(f"Event accepted: {title} ({p1:.1f}% vs {p2:.1f}%)")
                else:
                    filtered_count += 1
                    logger.debug(f"Event filtered: {title} ({p1:.1f}% vs {p2:.1f}%) - out of range")
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse prices for {title}: {e}")
                continue

        # 生成报告
        if valid_events:
            for event in valid_events:
                report += f"🔹 {event['title']}\n"
                report += f"   PROBABILITY: {event['g1']} ({event['p1']:.1f}%) vs {event['g2']} ({event['p2']:.1f}%)\n\n"
        else:
            report += "⚠️ 当前没有符合筛选条件的事件 (10%-95% 概率)\n\n"

        if filtered_count > 0:
            report += f"📌 已过滤 {filtered_count} 个几乎确定的事件 (<10% 或 >95%)\n"

        logger.info(f"Polymarket: {len(valid_events)} events accepted, {filtered_count} filtered")
        return report if len(report) > 50 else "❌ 未获取到有效 Polymarket 数据\n"
    except Exception as e:
        error_msg = f"❌ Polymarket Data Error: {e}\n"
        logger.error(error_msg)
        return error_msg

def get_news_data():
    """获取全球前沿新闻（使用 mediastack）"""
    url = "http://api.mediastack.com/v1/news?access_key=9f80de54e9e55a04763b7c4d2961869c&languages=en&limit=10"
    try:
        logger.info(f"Fetching news from mediastack...")
        response = requests.get(url, timeout=15)
        result = response.json()

        # 检查 API 返回状态
        if result.get('error'):
            error_msg = f"❌ Mediastack Error: {result.get('error', {}).get('message', 'Unknown error')}\n"
            logger.error(error_msg)
            return error_msg

        articles = result.get('data', [])
        if not articles:
            logger.warning("No articles returned from mediastack")
            return "❌ 未获取到新闻数据\n"

        logger.info(f"Retrieved {len(articles)} articles from mediastack")

        report = "🌍 GLOBAL FRONTIER NEWS SUMMARY\n"
        report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        for i, art in enumerate(articles[:10], 1):
            title = art.get('title') or 'No Title'
            source = art.get('source') or 'Unknown'
            desc = art.get('description') or 'No summary available.'

            # 安全截断描述
            if desc and len(desc) > 120:
                desc = desc[:120] + '...'

            report += f"{i}. {title}\n"
            report += f"   Source: {source}\n"
            report += f"   Brief: {desc}\n\n"

        return report
    except Exception as e:
        error_msg = f"❌ News Data Error: {e}\n"
        logger.error(error_msg)
        return error_msg

def send_email(content):
    mail_host = "smtp.qq.com"
    mail_user = os.getenv("MAIL_USER")
    mail_pass = os.getenv("MAIL_PASS")
    mail_receiver = os.getenv("MAIL_RECEIVER")

    if not all([mail_user, mail_pass, mail_receiver]):
        logger.error("邮件配置不完整，请检查环境变量")
        return False

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = f"M4_Intelligence_Bot <{mail_user}>"
    message['To'] = mail_receiver
    message['Subject'] = Header(f"Daily Intelligence Report | {now_str}", 'utf-8')

    try:
        smtp = smtplib.SMTP_SSL(mail_host, 465, timeout=15)
        smtp.login(mail_user, mail_pass)
        smtp.sendmail(mail_user, [mail_receiver], message.as_string())
        smtp.quit()
        logger.info(f"✅ Report Sent: {now_str}")
        return True
    except Exception as e:
        logger.error(f"❌ Send Failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Starting bot...")

    logger.info("Fetching news...")
    news_part = get_news_data()
    logger.info(f"News length: {len(news_part)} chars")

    logger.info("Fetching polymarket...")
    poly_part = get_poly_data()
    logger.info(f"Polymarket length: {len(poly_part)} chars")

    final_report = "PREMIUM DAILY INTELLIGENCE SUMMARY\n"
    final_report += "Generated by M4 Mac mini | " + datetime.now().strftime("%Y-%m-%d") + "\n"
    final_report += "━" * 40 + "\n\n"
    final_report += news_part + "\n"
    final_report += poly_part
    final_report += "\n[End of Report]"

    logger.info(f"Final report length: {len(final_report)} chars")
    logger.info("Sending email...")

    success = send_email(final_report)
    if success:
        logger.info("Bot finished successfully")
    else:
        logger.error("Bot finished with errors")
    logger.info("=" * 50)