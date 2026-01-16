// Vercel Serverless Function - 实时抓取财经新闻
// 路径: /api/news.js
// 完整版本：支持所有中文新闻源，每个源只返回最新 10 条

export default async function handler(req, res) {
  // CORS 头
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=120');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  // 所有新闻源配置
  const SOURCES = [
    // 国际源 (RSS)
    { name: 'BBC Business', url: 'https://feeds.bbci.co.uk/news/business/rss.xml', region: 'international', type: 'rss' },
    { name: 'CNBC Top News', url: 'https://www.cnbc.com/id/100003114/device/rss/rss.html', region: 'international', type: 'rss' },
    { name: 'WSJ Markets', url: 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml', region: 'international', type: 'rss' },
    { name: 'Financial Times', url: 'https://www.ft.com/rss/home', region: 'international', type: 'rss' },
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/news/rssindex', region: 'international', type: 'rss' },
    { name: 'Reuters Business', url: 'https://feeds.reuters.com/reuters/businessNews', region: 'international', type: 'rss' },
    
    // 中文源 (RSS)
    { name: '36氪财经', url: 'https://36kr.com/feed', region: 'chinese', type: 'rss' },
    { name: '虎嗅网', url: 'https://www.huxiu.com/rss/0.xml', region: 'chinese', type: 'rss' },
    
    // 中文源 (JSON API)
    { name: '新浪财经', url: 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=10&page=1', region: 'chinese', type: 'sina' },
    { name: '华尔街见闻', url: 'https://api.wallstreetcn.com/apiv1/content/articles?channel=global-channel&limit=10', region: 'chinese', type: 'wallstreet' }
  ];

  const results = {
    fetchTime: new Date().toISOString(),
    sources: []
  };

  // 并行获取所有新闻源
  const fetchPromises = SOURCES.map(async (source) => {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(source.url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
          'Accept': '*/*'
        },
        signal: controller.signal
      });
      clearTimeout(timeout);
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const content = await response.text();
      let items = [];
      
      // 根据类型选择解析方式
      switch (source.type) {
        case 'sina':
          items = parseSinaJSON(content);
          break;
        case 'wallstreet':
          items = parseWallstreetJSON(content);
          break;
        default:
          items = parseRSS(content, 10);
      }
      
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

  const settledResults = await Promise.allSettled(fetchPromises);
  results.sources = settledResults.map(r => r.status === 'fulfilled' ? r.value : r.reason);
  
  const totalItems = results.sources.reduce((sum, s) => sum + (s.itemCount || 0), 0);
  console.log(`Fetched ${totalItems} articles from ${results.sources.length} sources`);

  return res.status(200).json(results);
}

// 解析新浪财经 JSON
function parseSinaJSON(content) {
  try {
    const data = JSON.parse(content);
    if (data?.result?.data) {
      return data.result.data.slice(0, 10).map(item => ({
        title: item.title || '',
        link: item.url || '',
        description: item.intro || '',
        pubDate: item.ctime || ''
      }));
    }
  } catch (e) {
    console.error('Sina parse error:', e.message);
  }
  return [];
}

// 解析华尔街见闻 JSON
function parseWallstreetJSON(content) {
  try {
    const data = JSON.parse(content);
    if (data?.data?.items) {
      return data.data.items.slice(0, 10).map(item => ({
        title: item.title || '',
        link: `https://wallstreetcn.com/articles/${item.id}`,
        description: item.summary || '',
        pubDate: item.display_time ? new Date(item.display_time * 1000).toISOString() : ''
      }));
    }
  } catch (e) {
    console.error('Wallstreet parse error:', e.message);
  }
  return [];
}

// 解析 RSS
function parseRSS(content, maxItems = 10) {
  const items = [];
  const itemRegex = /<item[^>]*>([\s\S]*?)<\/item>|<entry[^>]*>([\s\S]*?)<\/entry>/gi;
  let match;
  
  while ((match = itemRegex.exec(content)) !== null && items.length < maxItems) {
    const itemContent = match[1] || match[2];
    
    const titleMatch = /<title[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/i.exec(itemContent);
    const title = titleMatch ? titleMatch[1].trim().replace(/<[^>]+>/g, '') : '';
    
    let link = '';
    const linkMatch = /<link[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/link>|<link[^>]*href=["']([^"']+)["']/i.exec(itemContent);
    if (linkMatch) {
      link = (linkMatch[1] || linkMatch[2] || '').trim().replace(/&amp;/g, '&');
    }
    
    const descMatch = /<description[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/description>|<summary[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/summary>/i.exec(itemContent);
    let description = descMatch ? (descMatch[1] || descMatch[2] || '').replace(/<[^>]+>/g, '').trim().slice(0, 300) : '';
    
    const dateMatch = /<pubDate[^>]*>([\s\S]*?)<\/pubDate>|<published[^>]*>([\s\S]*?)<\/published>|<updated[^>]*>([\s\S]*?)<\/updated>/i.exec(itemContent);
    const pubDate = dateMatch ? (dateMatch[1] || dateMatch[2] || dateMatch[3] || '').trim() : '';
    
    if (title && link) {
      items.push({ title, link, description, pubDate });
    }
  }
  
  return items;
}
