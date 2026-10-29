// Minimal MCP-compatible stub server
// Replace with real MCP implementation when ready
const http = require('http');

const server = http.createServer((req, res) => {
  res.writeHead(200, {'Content-Type': 'application/json'});
  res.end(JSON.stringify({status: 'ok', message: 'MCP stub server running'}));
});

server.listen(8765, () => {
  console.log('MCP stub server listening on port 8765');
});

process.stdin.resume();
process.stdin.on('data', () => {});
