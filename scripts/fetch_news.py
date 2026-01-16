#!/usr/bin/env python3
"""
Finance News Fetcher
抓取国际财经新闻并保存为 JSON 格式
"""

import json
import os
import re
import sys
import html
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser
import ssl

# 禁用 SSL 验证（某些网站可能需要）
ssl._create_default_https_context = ssl._create_unverified_context

class NewsHTMLParser(HTMLParser):
    """简单的 HTML 解析器，用于提取文本内容"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {'script', 'style', 'nav', 'footer', 'header'}
        self.current_tag = None
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        
    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                self.text.append(text)
                
    def get_text(self):
        return ' '.join(self.text)

def fetch_url(url, timeout=10):
    """获取 URL 内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8', errors='ignore')
    except (URLError, HTTPError) as e:
        print(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_rss_simple(content):
    """简单解析 RSS/XML 内容"""
    items = []
    # 匹配 <item> 或 <entry> 标签
    item_pattern = r'<item[^>]*>(.*?)</item>|<entry[^>]*>(.*?)</entry>'
    matches = re.findall(item_pattern, content, re.DOTALL | re.IGNORECASE)
    
    for match in matches[:20]:  # 限制 20 条新闻
        item_content = match[0] or match[1]
        
        # 提取标题
        title_match = re.search(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item_content, re.DOTALL | re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ''
        
        # 提取链接
        link_match = re.search(r'<link[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>|<link[^>]*href=["\']([^"\']+)["\']', item_content, re.DOTALL | re.IGNORECASE)
        link = ''
        if link_match:
            link = link_match.group(1) or link_match.group(2) or ''
            link = html.unescape(link.strip())  # 解码 HTML 实体如 &amp; -> &
        
        # 提取描述
        desc_match = re.search(r'<description[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>|<summary[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</summary>', item_content, re.DOTALL | re.IGNORECASE)
        description = ''
        if desc_match:
            description = desc_match.group(1) or desc_match.group(2) or ''
            # 清理 HTML 标签
            description = re.sub(r'<[^>]+>', '', description).strip()
        
        # 提取发布时间
        date_match = re.search(r'<pubDate[^>]*>(.*?)</pubDate>|<published[^>]*>(.*?)</published>|<updated[^>]*>(.*?)</updated>', item_content, re.DOTALL | re.IGNORECASE)
        pub_date = ''
        if date_match:
            pub_date = date_match.group(1) or date_match.group(2) or date_match.group(3) or ''
            pub_date = pub_date.strip()
        
        if title:
            items.append({
                'title': title,
                'link': link,
                'description': description[:500] if description else '',
                'pubDate': pub_date
            })
    
    return items

# 国际财经新闻 RSS 源
INTERNATIONAL_SOURCES = [
    {
        'name': 'Reuters Business',
        'url': 'https://feeds.reuters.com/reuters/businessNews',
        'category': 'Business',
        'region': 'international'
    },
    {
        'name': 'BBC Business',
        'url': 'https://feeds.bbci.co.uk/news/business/rss.xml',
        'category': 'Business',
        'region': 'international'
    },
    {
        'name': 'CNBC Top News',
        'url': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
        'category': 'Finance',
        'region': 'international'
    },
    {
        'name': 'Financial Times',
        'url': 'https://www.ft.com/rss/home',
        'category': 'Finance',
        'region': 'international'
    },
    {
        'name': 'Bloomberg Markets',
        'url': 'https://feeds.bloomberg.com/markets/news.rss',
        'category': 'Markets',
        'region': 'international'
    },
    {
        'name': 'Yahoo Finance',
        'url': 'https://finance.yahoo.com/news/rssindex',
        'category': 'Finance',
        'region': 'international'
    },
    {
        'name': 'MarketWatch',
        'url': 'http://feeds.marketwatch.com/marketwatch/topstories/',
        'category': 'Markets',
        'region': 'international'
    },
    {
        'name': 'WSJ Markets',
        'url': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
        'category': 'Markets',
        'region': 'international'
    }
]

# 中文财经新闻 RSS 源
CHINESE_SOURCES = [
    {
        'name': '新浪财经',
        'url': 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50&page=1&callback=&_=1',
        'category': '综合',
        'region': 'chinese',
        'type': 'json_sina'
    },
    {
        'name': '东方财富',
        'url': 'https://newsapi.eastmoney.com/kuaixun/v1/getlist_101_ajaxResult_50_1_.html',
        'category': '快讯',
        'region': 'chinese',
        'type': 'json_eastmoney'
    },
    {
        'name': '华尔街见闻',
        'url': 'https://api.wallstreetcn.com/apiv1/content/articles?channel=global-channel&limit=20',
        'category': '全球',
        'region': 'chinese',
        'type': 'json_wallstreet'
    },
    {
        'name': '36氪财经',
        'url': 'https://36kr.com/feed',
        'category': '科技财经',
        'region': 'chinese',
        'type': 'rss'
    },
    {
        'name': '界面新闻',
        'url': 'https://www.jiemian.com/rss/caijing.rss',
        'category': '财经',
        'region': 'chinese',
        'type': 'rss'
    },
    {
        'name': '虎嗅网',
        'url': 'https://www.huxiu.com/rss/0.xml',
        'category': '商业',
        'region': 'chinese',
        'type': 'rss'
    }
]

# 合并所有新闻源
NEWS_SOURCES = INTERNATIONAL_SOURCES + CHINESE_SOURCES

def parse_sina_json(content):
    """解析新浪财经 JSON"""
    items = []
    try:
        data = json.loads(content)
        if data.get('result') and data['result'].get('data'):
            for item in data['result']['data'][:20]:
                items.append({
                    'title': item.get('title', ''),
                    'link': item.get('url', ''),
                    'description': item.get('intro', ''),
                    'pubDate': item.get('ctime', '')
                })
    except:
        pass
    return items

def parse_eastmoney_json(content):
    """解析东方财富 JSON"""
    items = []
    try:
        # 移除 JSONP 包装
        content = re.sub(r'^[^(]*\(|\);?$', '', content)
        data = json.loads(content)
        if data.get('LivesList'):
            for item in data['LivesList'][:20]:
                items.append({
                    'title': item.get('Title', ''),
                    'link': item.get('Url', ''),
                    'description': item.get('Content', ''),
                    'pubDate': item.get('ShowTime', '')
                })
    except:
        pass
    return items

def parse_wallstreet_json(content):
    """解析华尔街见闻 JSON"""
    items = []
    try:
        data = json.loads(content)
        if data.get('data') and data['data'].get('items'):
            for item in data['data']['items'][:20]:
                items.append({
                    'title': item.get('title', ''),
                    'link': f"https://wallstreetcn.com/articles/{item.get('id', '')}",
                    'description': item.get('summary', ''),
                    'pubDate': datetime.fromtimestamp(item.get('display_time', 0)).isoformat() if item.get('display_time') else ''
                })
    except:
        pass
    return items

def fetch_all_news(output_dir=None):
    """获取所有新闻源的新闻"""
    all_news = {
        'fetchTime': datetime.now().isoformat(),
        'sources': [],
        'regions': {
            'international': [],
            'chinese': []
        }
    }
    
    for source in NEWS_SOURCES:
        print(f"Fetching from {source['name']}...")
        content = fetch_url(source['url'])
        
        source_data = {
            'name': source['name'],
            'category': source['category'],
            'region': source.get('region', 'international'),
            'url': source['url'],
            'itemCount': 0,
            'items': []
        }
        
        if content:
            # 根据类型选择解析方式
            source_type = source.get('type', 'rss')
            
            if source_type == 'json_sina':
                items = parse_sina_json(content)
            elif source_type == 'json_eastmoney':
                items = parse_eastmoney_json(content)
            elif source_type == 'json_wallstreet':
                items = parse_wallstreet_json(content)
            else:
                items = parse_rss_simple(content)
            
            source_data['itemCount'] = len(items)
            source_data['items'] = items
            print(f"  Found {len(items)} articles")
        else:
            print(f"  Failed to fetch")
            source_data['error'] = 'Failed to fetch'
        
        all_news['sources'].append(source_data)
        
        # 按区域分类
        region = source.get('region', 'international')
        if region in all_news['regions']:
            all_news['regions'][region].append(source_data['name'])
    
    # 保存到文件
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'news_data.json')
    else:
        output_file = 'news_data.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    
    # 统计
    int_count = sum(1 for s in all_news['sources'] if s.get('region') == 'international' and s['itemCount'] > 0)
    cn_count = sum(1 for s in all_news['sources'] if s.get('region') == 'chinese' and s['itemCount'] > 0)
    total_items = sum(s['itemCount'] for s in all_news['sources'])
    
    print(f"\n✅ News saved to {output_file}")
    print(f"   📰 Total: {total_items} articles")
    print(f"   🌍 International: {int_count} sources")
    print(f"   🇨🇳 Chinese: {cn_count} sources")
    return all_news

def main():
    """主函数"""
    # GitHub Actions 默认使用当前目录
    output_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    fetch_all_news(output_dir)

if __name__ == '__main__':
    main()
