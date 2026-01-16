#!/usr/bin/env python3
"""
生成包含新闻数据的完整 HTML 页面
解决浏览器 CORS 限制问题，将 JSON 数据直接嵌入 HTML
"""

import json
import os
import sys

# HTML 模板
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>国际财经新闻 | Finance News Watcher</title>
    <meta name="description" content="实时监控全球财经新闻，涵盖Reuters、Bloomberg、WSJ等国际媒体及新浪财经、东方财富等中文财经资讯">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a25;
            --bg-card-hover: #22222f;
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --text-muted: #606070;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --accent-pink: #ec4899;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-orange: #f97316;
            --gradient-primary: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%);
            --gradient-card: linear-gradient(145deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0) 100%);
            --shadow-glow: 0 0 60px rgba(59, 130, 246, 0.15);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 24px;
        }

        /* Header */
        header {
            background: linear-gradient(180deg, var(--bg-secondary) 0%, transparent 100%);
            padding: 32px 0;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(20px);
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            width: 48px;
            height: 48px;
            background: var(--gradient-primary);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: var(--shadow-glow);
        }

        .logo-text h1 {
            font-size: 24px;
            font-weight: 700;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .logo-text p {
            font-size: 12px;
            color: var(--text-muted);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .update-time {
            font-size: 13px;
            color: var(--text-muted);
            padding: 8px 16px;
            background: var(--bg-card);
            border-radius: 20px;
            border: 1px solid var(--border-color);
        }

        .refresh-btn {
            padding: 10px 20px;
            background: var(--gradient-primary);
            border: none;
            border-radius: 20px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow);
        }

        /* Stats Section */
        .stats-section {
            padding: 24px 0;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }

        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            background: var(--bg-card-hover);
            transform: translateY(-2px);
        }

        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }

        .stat-icon.blue { background: rgba(59, 130, 246, 0.15); }
        .stat-icon.purple { background: rgba(139, 92, 246, 0.15); }
        .stat-icon.pink { background: rgba(236, 72, 153, 0.15); }
        .stat-icon.cyan { background: rgba(6, 182, 212, 0.15); }

        .stat-info h3 {
            font-size: 28px;
            font-weight: 700;
        }

        .stat-info p {
            font-size: 13px;
            color: var(--text-muted);
        }

        /* Tabs */
        .tabs-section {
            padding: 16px 0;
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
        }

        .region-tabs {
            display: flex;
            gap: 8px;
            background: var(--bg-card);
            padding: 4px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }

        .region-tab {
            padding: 10px 20px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .region-tab.active {
            background: var(--gradient-primary);
            color: white;
        }

        .region-tab:hover:not(.active) {
            background: rgba(255, 255, 255, 0.05);
        }

        .source-tabs {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            flex: 1;
        }

        .source-tab {
            padding: 8px 16px;
            border: 1px solid var(--border-color);
            background: var(--bg-card);
            color: var(--text-secondary);
            border-radius: 20px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .source-tab.active {
            border-color: var(--accent-blue);
            color: var(--accent-blue);
            background: rgba(59, 130, 246, 0.1);
        }

        .source-tab:hover:not(.active) {
            border-color: var(--text-muted);
        }

        /* News Grid */
        .news-section {
            padding: 24px 0 48px;
        }

        .news-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 20px;
        }

        .news-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            gap: 16px;
            position: relative;
            overflow: hidden;
        }

        .news-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-primary);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .news-card:hover {
            background: var(--bg-card-hover);
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }

        .news-card:hover::before {
            opacity: 1;
        }

        .news-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
        }

        .news-source {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            background: rgba(59, 130, 246, 0.15);
            color: var(--accent-blue);
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .news-time {
            font-size: 12px;
            color: var(--text-muted);
            white-space: nowrap;
        }

        .news-title {
            font-size: 17px;
            font-weight: 600;
            line-height: 1.5;
            color: var(--text-primary);
        }

        .news-title a {
            color: inherit;
            text-decoration: none;
            transition: color 0.3s ease;
        }

        .news-title a:hover {
            color: var(--accent-blue);
        }

        .news-description {
            font-size: 14px;
            color: var(--text-secondary);
            line-height: 1.7;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .news-footer {
            margin-top: auto;
            display: flex;
            justify-content: flex-end;
        }

        .read-more {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            background: rgba(59, 130, 246, 0.1);
            color: var(--accent-blue);
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.3s ease;
        }

        .read-more:hover {
            background: var(--accent-blue);
            color: white;
        }

        /* Loading */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: var(--bg-primary);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            transition: opacity 0.5s ease;
        }

        .loading-overlay.hidden {
            opacity: 0;
            pointer-events: none;
        }

        .loading-spinner {
            width: 60px;
            height: 60px;
            border: 3px solid var(--border-color);
            border-top-color: var(--accent-blue);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .loading-text {
            margin-top: 20px;
            color: var(--text-secondary);
            font-size: 14px;
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-muted);
        }

        .empty-state-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                text-align: center;
            }

            .news-grid {
                grid-template-columns: 1fr;
            }

            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="loading-overlay" id="loading">
        <div class="loading-spinner"></div>
        <p class="loading-text">正在加载新闻数据...</p>
    </div>

    <header>
        <div class="container">
            <div class="header-content">
                <div class="logo">
                    <div class="logo-icon">📊</div>
                    <div class="logo-text">
                        <h1>Finance News Watcher</h1>
                        <p>国际 & 中文财经新闻实时监控</p>
                    </div>
                </div>
                <div class="header-actions">
                    <span class="update-time" id="update-time">更新于 --</span>
                    <button class="refresh-btn" onclick="location.reload()">
                        🔄 刷新
                    </button>
                </div>
            </div>
        </div>
    </header>

    <main class="container">
        <section class="stats-section">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon blue">📰</div>
                    <div class="stat-info">
                        <h3 id="total-news">0</h3>
                        <p>总新闻数</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon purple">🌍</div>
                    <div class="stat-info">
                        <h3 id="int-sources">0</h3>
                        <p>国际来源</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon pink">🇨🇳</div>
                    <div class="stat-info">
                        <h3 id="cn-sources">0</h3>
                        <p>中文来源</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon cyan">⏰</div>
                    <div class="stat-info">
                        <h3 id="next-update">09:00</h3>
                        <p>下次自动更新</p>
                    </div>
                </div>
            </div>
        </section>

        <section class="tabs-section">
            <div class="region-tabs">
                <button class="region-tab active" data-region="all" onclick="switchRegion('all')">
                    🌐 全部 <span id="count-all">0</span>
                </button>
                <button class="region-tab" data-region="international" onclick="switchRegion('international')">
                    🌍 国际 <span id="count-international">0</span>
                </button>
                <button class="region-tab" data-region="chinese" onclick="switchRegion('chinese')">
                    🇨🇳 中文 <span id="count-chinese">0</span>
                </button>
            </div>
            <div class="source-tabs" id="source-tabs"></div>
        </section>

        <section class="news-section">
            <div class="news-grid" id="news-grid"></div>
        </section>
    </main>

    <script>
        let newsData = null;
        let currentRegion = 'all';
        let currentSource = 'all';

        async function loadNewsData() {
            // 优先使用内嵌数据
            if (window.embeddedNewsData) {
                newsData = window.embeddedNewsData;
                updateUI();
                return;
            }
            // 尝试从外部 JSON 文件加载
            try {
                const response = await fetch('news_data.json');
                if (response.ok) {
                    newsData = await response.json();
                    updateUI();
                    return;
                }
            } catch (e) {
                console.log('Local data not found, loading demo data...');
            }
            loadDemoData();
        }

        function loadDemoData() {
            newsData = {
                fetchTime: new Date().toISOString(),
                sources: [
                    {
                        name: 'Reuters Business', category: 'Business', region: 'international',
                        itemCount: 3,
                        items: [
                            { title: 'Global Markets Rally as Tech Stocks Lead Recovery', description: 'Major indices across Asia, Europe and the US posted gains as investors bet on continued economic growth.', link: 'https://reuters.com/business', pubDate: new Date(Date.now() - 3600000).toISOString() },
                            { title: 'Oil Prices Surge on Middle East Supply Concerns', description: 'Brent crude jumps 3% as geopolitical tensions raise concerns about potential supply disruptions.', link: 'https://reuters.com/business', pubDate: new Date(Date.now() - 7200000).toISOString() },
                            { title: 'Federal Reserve Signals Patience on Rate Cuts', description: 'Fed officials suggest they need more evidence of cooling inflation before beginning to lower interest rates.', link: 'https://reuters.com/business', pubDate: new Date(Date.now() - 10800000).toISOString() }
                        ]
                    },
                    {
                        name: 'Bloomberg Markets', category: 'Markets', region: 'international',
                        itemCount: 2,
                        items: [
                            { title: 'Asian Stocks Mixed as Investors Weigh China Data', description: 'Hong Kong and mainland China markets diverge as new economic indicators send mixed signals.', link: 'https://bloomberg.com/markets', pubDate: new Date(Date.now() - 5400000).toISOString() },
                            { title: 'Dollar Weakens Against Major Currencies', description: 'The greenback falls to a one-week low as traders reassess Federal Reserve policy moves.', link: 'https://bloomberg.com/markets', pubDate: new Date(Date.now() - 9000000).toISOString() }
                        ]
                    },
                    {
                        name: '新浪财经', category: '综合', region: 'chinese',
                        itemCount: 3,
                        items: [
                            { title: '人民币汇率稳中有升 央行释放积极信号', description: '中国人民银行表示将保持人民币汇率在合理均衡水平上的基本稳定，增强市场信心。', link: 'https://finance.sina.com.cn', pubDate: new Date(Date.now() - 3600000).toISOString() },
                            { title: 'A股三大指数集体收涨 科技股领涨', description: '上证指数收涨0.8%，深证成指涨1.2%，创业板指涨1.5%，科技板块表现活跃。', link: 'https://finance.sina.com.cn', pubDate: new Date(Date.now() - 7200000).toISOString() },
                            { title: '多家银行下调存款利率 理财市场或迎调整', description: '国有大行纷纷下调存款利率，分析师预计将对银行理财产品收益率产生影响。', link: 'https://finance.sina.com.cn', pubDate: new Date(Date.now() - 10800000).toISOString() }
                        ]
                    },
                    {
                        name: '东方财富', category: '快讯', region: 'chinese',
                        itemCount: 2,
                        items: [
                            { title: '北向资金今日净买入超50亿元 连续三日流入', description: '外资持续看好中国市场，北向资金大幅流入A股市场，偏好金融和消费板块。', link: 'https://www.eastmoney.com', pubDate: new Date(Date.now() - 5400000).toISOString() },
                            { title: '新能源汽车销量再创新高 产业链迎来机遇', description: '最新数据显示国内新能源汽车渗透率突破40%，相关产业链公司股价上涨。', link: 'https://www.eastmoney.com', pubDate: new Date(Date.now() - 9000000).toISOString() }
                        ]
                    }
                ]
            };
            updateUI();
        }

        function switchRegion(region) {
            currentRegion = region;
            currentSource = 'all';
            
            document.querySelectorAll('.region-tab').forEach(tab => {
                const isActive = tab.dataset.region === region;
                tab.classList.toggle('active', isActive);
            });

            updateSourceTabs();
            renderNews();
        }

        function updateUI() {
            if (!newsData) return;

            // 统计数据
            let totalNews = 0;
            let intSources = 0, cnSources = 0;
            let intNews = 0, cnNews = 0;
            
            newsData.sources.forEach(source => {
                const count = source.items ? source.items.length : 0;
                totalNews += count;
                if (source.region === 'chinese') { cnSources++; cnNews += count; }
                else { intSources++; intNews += count; }
            });

            document.getElementById('total-news').textContent = totalNews;
            document.getElementById('int-sources').textContent = intSources;
            document.getElementById('cn-sources').textContent = cnSources;
            document.getElementById('count-all').textContent = totalNews;
            document.getElementById('count-international').textContent = intNews;
            document.getElementById('count-chinese').textContent = cnNews;

            // 更新时间
            if (newsData.fetchTime) {
                const date = new Date(newsData.fetchTime);
                document.getElementById('update-time').textContent = 
                    `更新于 ${date.toLocaleDateString('zh-CN')} ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`;
            }

            updateSourceTabs();
            renderNews();

            // 隐藏加载动画
            document.getElementById('loading').classList.add('hidden');
        }

        function updateSourceTabs() {
            const container = document.getElementById('source-tabs');
            container.innerHTML = '';

            const sources = newsData.sources.filter(s => 
                currentRegion === 'all' || s.region === currentRegion
            );

            const allTab = document.createElement('button');
            allTab.className = 'source-tab' + (currentSource === 'all' ? ' active' : '');
            allTab.textContent = '全部来源';
            allTab.onclick = () => {
                currentSource = 'all';
                updateSourceTabs();
                renderNews();
            };
            container.appendChild(allTab);

            sources.forEach(source => {
                const tab = document.createElement('button');
                tab.className = 'source-tab' + (currentSource === source.name ? ' active' : '');
                tab.textContent = source.name;
                tab.onclick = () => {
                    currentSource = source.name;
                    updateSourceTabs();
                    renderNews();
                };
                container.appendChild(tab);
            });
        }

        function renderNews() {
            const grid = document.getElementById('news-grid');
            grid.innerHTML = '';

            let allItems = [];

            newsData.sources.forEach(source => {
                if (currentRegion !== 'all' && source.region !== currentRegion) return;
                if (currentSource !== 'all' && source.name !== currentSource) return;

                if (source.items) {
                    source.items.forEach(item => {
                        allItems.push({ ...item, sourceName: source.name, sourceRegion: source.region });
                    });
                }
            });

            // 按时间排序
            allItems.sort((a, b) => new Date(b.pubDate || 0) - new Date(a.pubDate || 0));

            if (allItems.length === 0) {
                grid.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📭</div>
                        <p>暂无新闻数据</p>
                    </div>
                `;
                return;
            }

            allItems.forEach(item => {
                const card = document.createElement('div');
                card.className = 'news-card';

                const timeStr = item.pubDate ? formatTime(item.pubDate) : '';

                card.innerHTML = `
                    <div class="news-header">
                        <span class="news-source">${item.sourceName}</span>
                        <span class="news-time">${timeStr}</span>
                    </div>
                    <h3 class="news-title">
                        <a href="${item.link}" target="_blank" rel="noopener">${item.title}</a>
                    </h3>
                    ${item.description ? `<p class="news-description">${item.description}</p>` : ''}
                    <div class="news-footer">
                        <a href="${item.link}" target="_blank" rel="noopener" class="read-more">
                            阅读全文 →
                        </a>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function formatTime(dateStr) {
            try {
                const date = new Date(dateStr);
                const now = new Date();
                const diff = now - date;

                if (diff < 3600000) {
                    return `${Math.floor(diff / 60000)}分钟前`;
                } else if (diff < 86400000) {
                    return `${Math.floor(diff / 3600000)}小时前`;
                } else {
                    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
                }
            } catch {
                return dateStr;
            }
        }

        // 初始化
        document.addEventListener('DOMContentLoaded', loadNewsData);
    </script>
</body>
</html>'''


def generate_html_with_data(data_file, output_file):
    """生成包含内嵌数据的 HTML"""
    
    # 读取新闻数据
    with open(data_file, 'r', encoding='utf-8') as f:
        news_data = f.read()
    
    # 创建内嵌数据的脚本
    embedded_script = f'''
    <script>
        // 内嵌的新闻数据（自动生成，解决 CORS 限制）
        window.embeddedNewsData = {news_data};
    </script>
    '''
    
    # 在 </head> 前插入数据脚本
    html_content = HTML_TEMPLATE.replace('</head>', embedded_script + '\n</head>')
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Generated: {output_file}")
    
    # 统计信息
    data = json.loads(news_data)
    total = sum(s.get('itemCount', 0) for s in data.get('sources', []))
    print(f"   📰 {total} articles embedded")

def main():
    # 脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    
    data_file = os.path.join(repo_dir, 'news_data.json')
    output_file = os.path.join(repo_dir, 'index.html')
    
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        print("   Please run fetch_news.py first")
        sys.exit(1)
    
    generate_html_with_data(data_file, output_file)

if __name__ == '__main__':
    main()
