import http from 'http';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Import the TanStack Start server handler
const serverEntryPath = join(__dirname, 'dist/server/server.js');
const { default: serverHandler } = await import(serverEntryPath);

const staticDir = join(__dirname, 'dist/client');
const port = process.env.PORT || 8080;

// Serve static assets
function serveStatic(pathname, res) {
  const filePath = join(staticDir, pathname);

  // Prevent directory traversal
  if (!filePath.startsWith(staticDir)) {
    res.writeHead(404);
    res.end('Not found');
    return true;
  }

  // Check if file exists
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    return false;
  }

  const ext = filePath.split('.').pop();
  const mimeTypes = {
    js: 'application/javascript',
    css: 'text/css',
    html: 'text/html',
    json: 'application/json',
    png: 'image/png',
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    gif: 'image/gif',
    svg: 'image/svg+xml',
    woff: 'font/woff',
    woff2: 'font/woff2',
  };

  const contentType = mimeTypes[ext] || 'application/octet-stream';
  const data = fs.readFileSync(filePath);

  res.writeHead(200, {
    'Content-Type': contentType,
    'Content-Length': data.length,
  });
  res.end(data);
  return true;
}

// Create HTTP server
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = url.pathname;

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // Try to serve static files
  if (pathname.startsWith('/assets/') || pathname === '/favicon.ico') {
    if (serveStatic(pathname, res)) {
      return;
    }
  }

  // For everything else (API + SSR), use the TanStack handler
  try {
    const response = await serverHandler.fetch(
      new Request(url, {
        method: req.method,
        headers: Object.fromEntries(
          Object.entries(req.headers).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v])
        ),
        body: req.method !== 'GET' && req.method !== 'HEAD' ? req : undefined,
      })
    );

    res.writeHead(response.status, Object.fromEntries(response.headers));
    res.end(await response.text());
  } catch (error) {
    console.error('Server error:', error);
    res.writeHead(500);
    res.end('Internal server error');
  }
});

server.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
