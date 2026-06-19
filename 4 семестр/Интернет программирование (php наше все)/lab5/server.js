const http = require('http');
const fs = require('fs');  // модуль file system

// JSON.parse(...) преобразует JSON строку в JavaScript объект
const data = JSON.parse(fs.readFileSync('data.json'));

// (req, res) => { ... } - функция, вызываемая при каждом HTTP запросе
const server = http.createServer((req, res) => {
  if (req.url.startsWith('/cities')) {
    const url = new URL(req.url, 'http://localhost:3000');
    const country = url.searchParams.get('country');

    const cities = data.countries[country];

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(cities));
  } else {

    fs.readFile('index.html', (err, content) => {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(content);
    });
  }
});

server.listen(3000, () => {
  console.log('Server running at http://localhost:3000');
});