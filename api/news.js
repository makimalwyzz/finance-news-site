// Vercel Serverless Function - 实时抓取财经新闻
// 路径: /api/news.js

export default async function handler(req, res) {
  // CORS 头
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  // 国际财经新闻 RSS 源
  const SOURCES = [
    { name: 'Reuters Business', url: 'https://feeds.reuters.com/reuters/businessNews', region: 'international' },
    { name: 'BBC Business', url: 'https://feeds.bbci.co.uk/news/business/rss.xml', region: 'international' },
    { name: 'CNBC Top News', url: 'https://www.cnbc.com/id/100003114/device/rss/rss.html', region: 'international' },
    { name: 'Financial Times', url: 'https://www.ft.com/rss/home', region: 'international' },
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/news/rssindex', region: 'international' },
    { name: 'WSJ Markets', url: 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml', region: 'international' },
    { name: '36氪财经', url: 'https://36kr.com/feed', region: 'chinese' },
    { name: '虎嗅网', url: 'https://www.huxiu.com/rss/0.xml', region: 'chinese' }
  ];

  const results = {
    fetchTime: new Date().toISOString(),
    sources: []
  };

  // 并行获取所有新闻源
  const fetchPromises = SOURCES.map(async (source) => {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 8000);
      
      const response = await fetch(source.url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)',
          'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        },
        signal: controller.signal
      });
      clearTimeout(timeout);
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const content = await response.text();
      const items = parseRSS(content);
      
      return {
        name: source.name,
        region: source.region,
        itemCount: items.length,
        items: items
      };
    } catch (error) {
      console.error(`Error fetching ${source.name}:`, error.message);
      return {
        name: source.name,
        region: source.region,
        itemCount: 0,
        items: [],
        error: error.message
      };
    }
  });

  results.sources = await Promise.all(fetchPromises);
  
  // 统计
  const totalItems = results.sources.reduce((sum, s) => sum + s.itemCount, 0);
  console.log(`Fetched ${totalItems} articles from ${results.sources.length} sources`);

  return res.status(200).json(results);
}

// 解析 RSS
function parseRSS(content) {
  const items = [];
  const itemRegex = /<item[^>]*>([\s\S]*?)<\/item>|<entry[^>]*>([\s\S]*?)<\/entry>/gi;
  let match;
  
  while ((match = itemRegex.exec(content)) !== null && items.length < 15) {
    const itemContent = match[1] || match[2];
    
    // 提取标题
    const titleMatch = /<title[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/i.exec(itemContent);
    const title = titleMatch ? titleMatch[1].trim().replace(/<[^>]+>/g, '') : '';
    
    // 提取链接
    let link = '';
    const linkMatch = /<link[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/link>|<link[^>]*href=["']([^"']+)["']/i.exec(itemContent);
    if (linkMatch) {
      link = (linkMatch[1] || linkMatch[2] || '').trim();
      link = link.replace(/&amp;/g, '&');
    }
    
    // 提取描述
    const descMatch = /<description[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/description>|<summary[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/summary>/i.exec(itemContent);
    let description = '';
    if (descMatch) {
      description = (descMatch[1] || descMatch[2] || '').replace(/<[^>]+>/g, '').trim().slice(0, 300);
    }
    
    // 提取时间
    const dateMatch = /<pubDate[^>]*>([\s\S]*?)<\/pubDate>|<published[^>]*>([\s\S]*?)<\/published>|<updated[^>]*>([\s\S]*?)<\/updated>/i.exec(itemContent);
    const pubDate = dateMatch ? (dateMatch[1] || dateMatch[2] || dateMatch[3] || '').trim() : '';
    
    if (title && link) {
      items.push({ title, link, description, pubDate });
    }
  }
  
  return items;
}
