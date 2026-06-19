const BASE = "https://cloud-api.yandex.net/v1/disk";

// Восстанавление предыдущих настроек
chrome.storage.local.get(["token", "folder", "filename"], (data) => {
  if (data.token)    document.getElementById("token").value    = data.token;
  if (data.folder)   document.getElementById("folder").value   = data.folder;
  if (data.filename) document.getElementById("filename").value = data.filename;
});

// JS однопоточный, но неблокирующий
// Берет выделенный текст со страницы
document.getElementById("btn-grab").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => window.getSelection().toString(),
  });

  // ?. - оператор опциональной последовательности 
  const text = results?.[0]?.result?.trim(); 
  if (text) {
    document.getElementById("text").value = text;
    setStatus("Текст получен", false);
  } else {
    setStatus("Нет выделенного текста", true);
  }
});

// Загрузить в Яндекс Диск 
document.getElementById("btn-send").addEventListener("click", async () => {
  const token    = document.getElementById("token").value.trim();
  const folder   = document.getElementById("folder").value.trim() || "/uploads";
  const filename = document.getElementById("filename").value.trim() || "selection.txt";
  const text     = document.getElementById("text").value;

  if (!token) return setStatus("Введите OAuth токен", true);
  if (!text)  return setStatus("Текст пустой", true);

  chrome.storage.local.set({ token, folder, filename });

  setStatus("Создаю папку...", false);

  try {
    await ensureFolder(token, folder);
    setStatus("Загружаю файл...", false);
    await uploadText(token, folder, filename, text);
    setStatus(`Загружено: ${folder}/${filename}`, false);
  } catch (e) {
    setStatus("Ошибка: " + e.message, true);
  }
});


function setStatus(msg, isError) {
  const el = document.getElementById("status");
  el.textContent = msg;
  el.className = isError ? "error" : "";
}

function apiHeaders(token) {
  return { Authorization: "OAuth " + token };
}

// Создает папку
async function ensureFolder(token, path) {
  const segments = path.replace(/^\//, "").split("/").filter(Boolean); 
  let current = "";
  for (const seg of segments) {
    current += "/" + seg;
    const r = await fetch(
      `${BASE}/resources?path=${encodeURIComponent(current)}`,
      { method: "PUT", headers: apiHeaders(token) }
    );
    // 201 - папка создана; 409 - уже существует
    if (r.status !== 201 && r.status !== 409) {
      const body = await r.json().catch(() => ({}));
      throw new Error(body.description || `PUT folder ${r.status}`);
    }
  }
}

// Запрашивает URL для загрузки и загружает файл с текстом
async function uploadText(token, folder, filename, text) {
  const diskPath = folder.replace(/\/$/, "") + "/" + filename;

  // Шаг 1: получить URL
  const r1 = await fetch(
    `${BASE}/resources/upload?path=${encodeURIComponent(diskPath)}&overwrite=true`,
    { headers: apiHeaders(token) }
  );
  if (!r1.ok) {
    const body = await r1.json().catch(() => ({}));
    throw new Error(body.description || `Получение URL: ${r1.status}`);
  }
  const { href } = await r1.json();

  // Шаг 2: загрузить содержимое
  const r2 = await fetch(href, {
    method: "PUT",
    body: new Blob([text], { type: "text/plain" }),
  });
  if (!r2.ok) throw new Error(`Загрузка файла: ${r2.status}`);
}
