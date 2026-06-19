import time
import requests
from pathlib import Path
from typing import Optional

BASE_URL = "https://cloud-api.yandex.net/v1/disk"

class YandexDiskClient:
    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"OAuth {token}"})

    def _folder_exists(self, path: str) -> bool:
        r = self.session.get(f"{BASE_URL}/resources", params={"path": path, "limit": 1})
        if r.status_code == 200:
            return r.json().get("type") == "dir"
        return False

    def _get_upload_url(self, disk_path: str, overwrite: bool = True) -> str:
        r = self.session.get(
            f"{BASE_URL}/resources/upload",
            params={"path": disk_path, "overwrite": str(overwrite).lower()},
        )
        r.raise_for_status()
        return r.json()["href"]
  
    def _list_resources(self, folder_path: str) -> list[dict]:
        r = self.session.get(
            f"{BASE_URL}/resources",
            params={"path": folder_path, "limit": 1000},
        )
        r.raise_for_status()
        return r.json().get("_embedded", {}).get("items", [])

    def SetFiles(
        self,
        local_paths: list[str] | str,
        disk_folder: str,
        overwrite: bool = True,
    ) -> list[str]:

        if isinstance(local_paths, str):
            local_paths = [local_paths]

        self.SetFolder(disk_folder)

        uploaded = []

        for local_path in local_paths:
            local_path = Path(local_path)

            if not local_path.is_file():
                raise FileNotFoundError(local_path)

            disk_path = f"{disk_folder.rstrip('/')}/{local_path.name}"
            upload_url = self._get_upload_url(disk_path, overwrite)

            data = open(local_path, "rb").read()
            r = self.session.put(upload_url, data=data)
            r.raise_for_status()

            print(f"[SetFiles] ✓ {local_path.name} → {disk_path}")
            uploaded.append(disk_path)

        return uploaded

    def GetFiles(
        self,
        disk_folder: str,
        names: str | list[str],
        local_dir: str = ".",
    ) -> list[str]:

        local_dir = Path(local_dir)
        local_dir.mkdir(parents=True, exist_ok=True)

        if names == "*":
            items = self._list_resources(disk_folder)
            target_names = [i["name"] for i in items if i["type"] == "file"]
        elif isinstance(names, str):
            target_names = [n.strip() for n in names.split(",") if n.strip()]
        else:
            target_names = list(names)

        downloaded = []

        for name in target_names:
            disk_path = f"{disk_folder.rstrip('/')}/{name}"

            try:
                url = self._get_download_url(disk_path)
            except requests.HTTPError as e:
                print(f"[GetFiles] ✗ {name}: {e}")
                continue

            data = self.session.get(url).content
            local_path = local_dir / name

            local_path.write_bytes(data)

            print(f"[GetFiles] ✓ {disk_path} → {local_path}")
            downloaded.append(str(local_path))

        return downloaded

    def GetFolders(self, path: Optional[str] = None) -> list[str]:
        target = path or "/"
        items = self._list_resources(target)
        folders = [i["name"] for i in items if i["type"] == "dir"]

        print(f"[GetFolders] {target}: {folders}")
        return folders

    def SetFolder(self, path: str) -> str:
        path = path.replace("\\", "/")
        segments = [s for s in path.split("/") if s]

        current = ""
        for s in segments:
            current = f"{current}/{s}"
            r = self.session.put(f"{BASE_URL}/resources", params={"path": current})

            if r.status_code == 202:
                time.sleep(1)
            elif r.status_code not in (201, 409):
                r.raise_for_status()

        return path

if __name__ == "__main__":
    TOKEN = "y0__wgBEOitvKoHGJXRQSD9v6i0F0ycrFsAPa5bkh0DaajOqxeSEP-e"

    client = YandexDiskClient(TOKEN)

    client.SetFolder("/my_uploads/docs")

    client.SetFiles(
        local_paths=["report.pdf", "data.csv"],
        disk_folder="/my_uploads/docs",
    )

    client.GetFiles(
        disk_folder="/my_uploads/docs",
        names="report.pdf, data.csv",
        local_dir="./downloads",
    )


    root_folders = client.GetFolders()

    sub_folders = client.GetFolders("/my_uploads")