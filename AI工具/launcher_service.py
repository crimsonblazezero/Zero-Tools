"""
KovaScape Launcher Service
监听本地 8766 端口，接收 Hub 启动页的 HTTP 请求，执行对应的本地工具。

路径约定（相对于本文件所在目录）：
  launcher_service.py 与各工具文件夹同级，例如：
    AI工具/
    ├── launcher_service.py
    ├── kovascape-hub.html
    ├── 启动Hub.bat
    ├── Amazon_Image_Tool_V5.0.py
    ├── Batch Files Transfer_V1.0.py
    ├── create_picture_folders.py
    ├── FNSKU Label Rename.py
    └── Amazon Image Extractor/
        ├── run.bat
        ├── asin_list.xlsx
        └── amazon_images_result.xlsx
"""
import http.server
import subprocess
import json
import os
import sys
import tempfile

PORT = 8766
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 用 launcher 自身的 Python，避免多版本混用
PYTHON = sys.executable

TOOLS = {
    "batch-transfer": {
        "type": "py",
        "path": "Batch Files Transfer_V1.0.py",
        "label": "Batch Files Transfer",
    },
    "create-folders": {
        "type": "py",
        "path": "create_picture_folders.py",
        "label": "Create Picture Folders",
    },
    "image-tool": {
        "type": "py",
        "path": "Amazon_Image_Tool_V5.0.py",
        "label": "Amazon Image Tool V5.0",
    },
    "fnsku-rename": {
        "type": "py",
        "path": "FNSKU Label Rename.py",
        "label": "FNSKU Label Rename",
    },
    "amazon-image-extractor-mode1": {
        "type": "bat_arg",
        "path": os.path.join("Amazon Image Extractor", "run.bat"),
        "arg":  "1",
        "label": "Amazon Image Extractor Mode1",
    },
    "amazon-image-extractor-mode2": {
        "type": "bat_arg",
        "path": os.path.join("Amazon Image Extractor", "run.bat"),
        "arg":  "2",
        "label": "Amazon Image Extractor Mode2",
    },
}


class LauncherHandler(http.server.BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/ping":
            self._json(200, {"status": "ok", "port": PORT})

        elif self.path.startswith("/open-file"):
            from urllib.parse import urlparse, parse_qs, unquote
            qs = parse_qs(urlparse(self.path).query)
            rel = unquote(qs.get("path", [""])[0]).replace("/", os.sep)
            full = os.path.normpath(os.path.join(BASE_DIR, rel))
            if not full.startswith(BASE_DIR):
                self._json(403, {"error": "路径不合法"})
                return
            if not os.path.exists(full):
                self._json(404, {"error": f"文件不存在: {rel}"})
                return
            if sys.platform == "win32":
                os.startfile(full)
            else:
                subprocess.Popen(["open", full])
            self._json(200, {"status": "opened", "file": rel})

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/launch":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
            tool_id = data.get("tool", "")
            tool = TOOLS.get(tool_id)

            if not tool:
                self._json(400, {"error": f"未知工具: {tool_id}"})
                return

            full_path = os.path.normpath(os.path.join(BASE_DIR, tool["path"]))
            work_dir  = os.path.dirname(full_path)

            if not os.path.exists(full_path):
                self._json(404, {"error": f"文件不存在: {tool['path']}"})
                return

            if tool["type"] == "py":
                # 列表方式，完全避开 cmd 引号嵌套
                subprocess.Popen(
                    ["cmd", "/c", "start", tool["label"], PYTHON, full_path],
                    cwd=work_dir
                )

            elif tool["type"] == "bat_arg":
                arg = tool.get("arg", "1")
                # 关键：不用 pipe，而是写一个临时 bat
                # 在临时 bat 里直接 set CHOICE=2，跳过 set /p 交互
                # 这样 run.bat 的完整流程（拉Chrome → timeout → 运行Python）都能正常执行
                tmp_bat = os.path.join(work_dir, "_hub_launch.bat")
                with open(tmp_bat, "w", encoding="gbk") as f:
                    f.write("@echo off\n")
                    f.write('cd /d "{}"\n'.format(work_dir))
                    # 预设 CHOICE 环境变量，run.bat 里的 set /p 读到后直接用
                    f.write("set CHOICE={}\n".format(arg))
                    # 调用原始 run.bat，它会读取已设置的 CHOICE 变量
                    f.write('call "{}"\n'.format(full_path))
                subprocess.Popen(
                    ["cmd", "/c", "start", tool["label"], tmp_bat],
                    cwd=work_dir
                )

            elif tool["type"] == "bat":
                subprocess.Popen(
                    ["cmd", "/c", "start", tool["label"], full_path],
                    cwd=work_dir
                )

            self._json(200, {"status": "launched", "tool": tool["label"]})

        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):
        print(f"  [Launcher] {fmt % args}")


if __name__ == "__main__":
    server = http.server.HTTPServer(("127.0.0.1", PORT), LauncherHandler)
    print(f"\n  KovaScape Launcher Service")
    print(f"  Python   : {PYTHON}")
    print(f"  监听端口 : {PORT}")
    print(f"  工作目录 : {BASE_DIR}")
    print(f"  已注册工具: {', '.join(TOOLS.keys())}")
    print(f"\n  关闭此窗口 = 停止服务\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  服务已停止")
