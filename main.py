import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置信息 - 优先从环境变量读取
CONFIG = {
    'api_url': 'https://gamma-api.polymarket.com/events',
    'api_params': {'limit': 10, 'active': True, 'sort': 'volume:desc'},
    'mail_host': 'smtp.qq.com',
    'mail_user': os.getenv('MAIL_USER', '42301759@qq.com'), 
    'mail_pass': os.getenv('MAIL_PASS'), # 必须在 GitHub Secrets 中配置
    'receivers': [os.getenv('MAIL_RECEIVER', '118094457@qq.com')], # 修改后的接收邮箱
    'email_subject': '🌍 全球热门事件赔率日报'
}

def get_polymarket_data():
    try:
        logger.info('开始获取 Polymarket 数据...')
        # GitHub Actions 运行环境在海外，请求这个 API 会非常快
        response = requests.get(CONFIG['api_url'], params=CONFIG['api_params'], timeout=15)
        response.raise_for_status()
        events = response.json()
        
        if not isinstance(events, list):
            return '❌ 获取数据失败: API 返回数据格式错误'
            
        report_lines = [f"📈 Polymarket 热门趋势 ({time.strftime('%Y-%m-%d %H:%M')})\n", "="*40]
        
        for event in events:
            title = event.get('title', '未知事件')
            report_lines.append(f"【事件】: {title}")
            
            markets = event.get('markets', [])
            odds_str = ""
            if markets:
                outcomes = markets[0].get('outcomes', [])
                prices = markets[0].get('outcomePrices', [])
                if outcomes and prices:
                    for o, p in zip(outcomes, prices):
                        try:
                            # p 是字符串格式的赔率，如 "0.55"
                            prob = round(float(p) * 100, 1)
                            odds_str += f"   - {o}: {prob}%\n"
                        except: continue
            
            if odds_str:
                report_lines.append(odds_str.strip())
            else:
                desc = event.get('description', '暂无详细描述')[:60]
                report_lines.append(f"   详情: {desc}...")
            
            report_lines.append("-" * 30)
            
        logger.info('成功解析数据')
        return "\n".join(report_lines)
    except Exception as e:
        logger.error(f"抓取失败: {e}")
        return f"❌ 数据抓取异常: {e}"

def send_email(content):
    # 检查授权码是否存在
    if not CONFIG['mail_pass']:
        logger.error("未检测到 MAIL_PASS 环境变量！请在 GitHub Secrets 中配置。")
        return False

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f'邮件尝试发送... ({attempt+1}/{max_retries})')
            message = MIMEText(content, 'plain', 'utf-8')
            message['From'] = f"PolymarketBot <{CONFIG['mail_user']}>"
            message['To'] = CONFIG['receivers'][0]
            message['Subject'] = Header(CONFIG['email_subject'], 'utf-8')

            # 连接 QQ 邮箱的 SSL 端口
            server = smtplib.SMTP_SSL(CONFIG['mail_host'], 465, timeout=15)
            server.login(CONFIG['mail_user'], CONFIG['mail_pass'])
            server.sendmail(CONFIG['mail_user'], CONFIG['receivers'], message.as_string())
            server.quit()
            logger.info('✅ 邮件已发送至 118094457@qq.com')
            return True
        except Exception as e:
            logger.warning(f"发送失败: {e}")
            if attempt < max_retries - 1: 
                logger.info("等待 10 秒后重试...")
                time.sleep(10)
    return False

if __name__ == "__main__":
    content = get_polymarket_data()
    send_email(content)