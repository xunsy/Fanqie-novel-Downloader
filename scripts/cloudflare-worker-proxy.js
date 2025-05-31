/**
 * Cloudflare Workers 反向代理脚本
 * 用于代理番茄小说API请求，避免直接访问被封锁
 * 
 * 部署说明：
 * 1. 登录 Cloudflare Dashboard
 * 2. 进入 Workers & Pages
 * 3. 创建新的 Worker
 * 4. 将此脚本复制到 Worker 编辑器中
 * 5. 部署并获取 Worker 域名
 * 6. 在下载器中配置该域名
 */

// 允许代理的目标域名列表（安全考虑）
const ALLOWED_HOSTS = [
  'fqphp.gxom.cn',
  'api.cenguigui.cn', 
  'lsjk.zyii.xyz',
  'nu1.jingluo.love',
  'nu2.jingluo.love',
  'fanqienovel.com'
];

// CORS 头部配置
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
  'Access-Control-Max-Age': '86400',
};

/**
 * 处理请求的主函数
 */
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

/**
 * 处理HTTP请求
 * @param {Request} request - 传入的请求
 * @returns {Response} - 代理后的响应
 */
async function handleRequest(request) {
  const url = new URL(request.url);
  
  // 处理 OPTIONS 预检请求
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: CORS_HEADERS
    });
  }
  
  // 健康检查端点
  if (url.pathname === '/test' || url.pathname === '/health') {
    return new Response(JSON.stringify({
      status: 'ok',
      message: 'Cloudflare Workers proxy is running',
      timestamp: new Date().toISOString()
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...CORS_HEADERS
      }
    });
  }
  
  // 解析目标URL
  const targetUrl = parseTargetUrl(url);
  if (!targetUrl) {
    return new Response(JSON.stringify({
      error: 'Invalid request path',
      message: 'Please provide a valid API endpoint path'
    }), {
      status: 400,
      headers: {
        'Content-Type': 'application/json',
        ...CORS_HEADERS
      }
    });
  }
  
  // 检查目标域名是否被允许
  const targetHost = new URL(targetUrl).hostname;
  if (!ALLOWED_HOSTS.includes(targetHost)) {
    return new Response(JSON.stringify({
      error: 'Host not allowed',
      message: `Target host ${targetHost} is not in the allowed list`
    }), {
      status: 403,
      headers: {
        'Content-Type': 'application/json',
        ...CORS_HEADERS
      }
    });
  }
  
  try {
    // 构建代理请求
    const proxyRequest = new Request(targetUrl, {
      method: request.method,
      headers: cleanHeaders(request.headers),
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : null
    });
    
    // 发送代理请求
    const response = await fetch(proxyRequest);
    
    // 构建响应头
    const responseHeaders = new Headers(response.headers);
    
    // 添加CORS头部
    Object.entries(CORS_HEADERS).forEach(([key, value]) => {
      responseHeaders.set(key, value);
    });
    
    // 添加代理信息头部
    responseHeaders.set('X-Proxy-By', 'Cloudflare-Workers');
    responseHeaders.set('X-Target-Host', targetHost);
    
    // 返回代理响应
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders
    });
    
  } catch (error) {
    console.error('Proxy request failed:', error);
    
    return new Response(JSON.stringify({
      error: 'Proxy request failed',
      message: error.message,
      target: targetUrl
    }), {
      status: 502,
      headers: {
        'Content-Type': 'application/json',
        ...CORS_HEADERS
      }
    });
  }
}

/**
 * 解析目标URL
 * @param {URL} url - Worker请求的URL
 * @returns {string|null} - 目标URL或null
 */
function parseTargetUrl(url) {
  const pathname = url.pathname;
  const search = url.search;
  
  // 支持多种URL格式：
  // 1. /content?item_id=123 -> https://fqphp.gxom.cn/content?item_id=123
  // 2. /api/tomato/content.php?item_id=123 -> https://api.cenguigui.cn/api/tomato/content.php?item_id=123
  // 3. /fqphp.gxom.cn/content?item_id=123 -> https://fqphp.gxom.cn/content?item_id=123
  
  // 如果路径以域名开头，直接使用
  const domainMatch = pathname.match(/^\/([^\/]+\.[^\/]+)(\/.*)?$/);
  if (domainMatch) {
    const domain = domainMatch[1];
    const path = domainMatch[2] || '';
    return `https://${domain}${path}${search}`;
  }
  
  // 根据路径模式推断目标域名
  if (pathname.startsWith('/content')) {
    return `https://fqphp.gxom.cn${pathname}${search}`;
  } else if (pathname.startsWith('/api/tomato/')) {
    return `https://api.cenguigui.cn${pathname}${search}`;
  } else if (pathname.match(/^\/\d+$/)) {
    // 纯数字路径，可能是章节ID
    return `https://lsjk.zyii.xyz:3666/content?item_id=${pathname.slice(1)}${search ? '&' + search.slice(1) : ''}`;
  }
  
  return null;
}

/**
 * 清理请求头，移除可能导致问题的头部
 * @param {Headers} headers - 原始请求头
 * @returns {Headers} - 清理后的请求头
 */
function cleanHeaders(headers) {
  const cleanedHeaders = new Headers();
  
  // 需要移除的头部
  const skipHeaders = [
    'cf-ray',
    'cf-connecting-ip',
    'cf-visitor',
    'cf-worker',
    'x-forwarded-proto',
    'x-forwarded-for',
    'x-real-ip'
  ];
  
  for (const [key, value] of headers.entries()) {
    const lowerKey = key.toLowerCase();
    if (!skipHeaders.includes(lowerKey)) {
      cleanedHeaders.set(key, value);
    }
  }
  
  // 设置必要的头部
  cleanedHeaders.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36');
  
  return cleanedHeaders;
}

/**
 * 使用示例：
 * 
 * 1. 部署此脚本到 Cloudflare Workers
 * 2. 获取 Worker 域名，例如：https://your-worker.your-subdomain.workers.dev
 * 3. 在下载器中配置反代域名
 * 4. 原始请求：https://fqphp.gxom.cn/content?item_id=123
 *    代理请求：https://your-worker.your-subdomain.workers.dev/content?item_id=123
 * 
 * 支持的API端点：
 * - /content?item_id={id} -> fqphp.gxom.cn
 * - /api/tomato/content.php?item_id={id} -> api.cenguigui.cn  
 * - /{id} -> lsjk.zyii.xyz:3666/content?item_id={id}
 * - /fqphp.gxom.cn/content?item_id={id} -> 直接代理到指定域名
 */
