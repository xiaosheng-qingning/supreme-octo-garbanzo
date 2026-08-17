# -*- coding: utf-8 -*-
"""
SimpleLanDisk - 局域网双界面网盘（在原有功能上额外加入视频播放）
"""

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
import os
import shutil
import uuid
import random
from urllib.parse import quote, unquote

app = FastAPI(title="SimpleLanDisk - 局域网双界面网盘")

# ============ 用户配置区 ============
ACCOUNTS = {
    "admin": {"pwd": "123456", "root": "./data/videos", "skin": "new"},
    "admins": {"pwd": "123456", "root": "./data/study", "skin": "old"}
}
RECYCLE_NAME = "$RecycleBin"
SYSTEM_FOLDER = "$system"
PORT = 8001
# ===================================

# ---------- 1️⃣ 视频后缀 & MIME ----------
VIDEO_EXTS = {
    ".mp4", ".webm", ".ogg", ".mov", ".avi",
    ".mkv", ".flv", ".wmv", ".mpg", ".mpeg",
    ".ts"                     # 支持 MPEG‑TS
}
VIDEO_MIME = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".ogg": "video/ogg",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
    ".flv": "video/x-flv",
    ".wmv": "video/x-ms-wmv",
    ".mpg": "video/mpeg",
    ".mpeg": "video/mpeg",
    ".ts": "video/mp2t"
}
# -------------------------------------

first_user = list(ACCOUNTS.values())[0]
RECYCLE_DIR = os.path.join(first_user["root"], RECYCLE_NAME)

for acc in ACCOUNTS.values():
    os.makedirs(acc["root"], exist_ok=True)
os.makedirs(RECYCLE_DIR, exist_ok=True)

sessions = {}

QUOTES_LIST = [
    ("Alan Kay", "预测未来最好的方式就是创造它。"),
    ("Edsger W. Dijkstra", "简单是可靠的先决条件。"),
    ("Donald Knuth", "过早优化是万恶之源。"),
    ("Linus Torvalds", "好的程序员关心代码，伟大的程序员关心数据结构。"),
    ("Grace Hopper", "最危险的一句话是：我们一直都是这么做的。"),
    ("Brian Kernighan", "控制复杂度就是软件工程的全部。"),
    ("Yukihiro Matsumoto", "代码是写给人看的，顺便给机器执行。"),
    ("Richard Stallman", "自由软件关乎自由，而非价格。"),
    ("Edsger W. Dijkstra", "如果调试是移除bug的过程，那么编程就是植入bug的过程。"),
    ("Linus Torvalds", "Talk is cheap. Show me the code."),
    ("Donald Knuth", "程序就是人写给计算机看的文章。"),
    ("Ken Thompson", "不要追求完美，只要能用就行。"),
    ("Bjarne Stroustrup", "软件设计的目标就是降低复杂度。"),
    ("Guido van Rossum", "代码可读性最重要。"),
    ("Tim Berners-Lee", "互联网的力量在于它的开放性。"),
    ("Martin Fowler", "任何傻瓜都能写出计算机看得懂的代码。优秀程序员写人能读懂的代码。"),
    ("Robert C. Martin", "整洁的代码只做一件事。"),
    ("Ward Cunningham", "代码就是设计。"),
    ("Larry Wall", "优秀程序员有三大美德：懒惰、急躁、傲慢。"),
    ("Joshua Bloch", "编写程序时要为维护者着想。"),
    ("Edsger W. Dijkstra", "测试只能证明bug存在，不能证明bug不存在。"),
    ("Alan Perlis", "程序不必与人对话，但一定要让人读懂。"),
    ("Richard Feynman", "如果你不能简单解释一件事，说明你还没有真正弄懂它。"),
    ("James Gosling", "不要过早抽象。"),
    ("Douglas Crockford", "优秀架构来自不断重构。"),
    ("Michael O. Church", "写代码前先想好退出条件。"),
    ("Simon Peyton-Jones", "让复杂的事情变简单是我们的使命。"),
    ("Joe Armstrong", "面向对象最大问题是得到了太多隐形环境。"),
    ("Mark Zuckerberg", "快速迭代，打破常规。"),
    ("Bill Gates", "成功是糟糕的老师，它诱使聪明人认为自己不会失败。"),
    ("Steve Jobs", "简单比复杂更难。"),
    ("Jeff Atwood", "任何能用JavaScript写出来的应用，最终都会用JavaScript写出来。"),
    ("Dennis Ritchie", "C语言本质上就是一种方便的汇编。"),
    ("Kent Beck", "先让代码跑起来，再让代码变好。"),
    ("Herb Sutter", "不要重复自己。")
]

# ---------- 2️⃣ STYLE_NEW（新增 video‑wrapper 样式） ----------
STYLE_NEW = """
<style>
body{font-family:Arial,sans-serif;max-width:960px;margin:24px auto;padding:0 18px;background:#f0f2f5;color:#222;}
.wrap{background:#ffffff;padding:24px;border-radius:6px;}
.quote{text-align:center;color:#444;font-style:italic;padding:12px 0;margin:8px 0;border-bottom:1px solid #eee;}
.card{background:#f8fafc;border:1px solid #e2e8f0;padding:14px;margin:10px 0;border-radius:6px;}
a{color:#2563eb;text-decoration:none;margin:0 8px;}
a:hover{text-decoration:underline;}
input{padding:5px;}

/* ==== 视频播放器专用样式 ==== */
.video-wrapper{
    margin:12px 0;
    text-align:center;
}
.video-wrapper video{
    max-width:100%;
    height:auto;
    border:1px solid #d1d5db;
    border-radius:4px;
    background:#000;
}
</style>
"""
# ----------------------------------------------------------

STYLE_OLD = """
<style>
body{font-family:Arial;font-size:16px;margin:15px;}
h2{font-size:22px;}
.item{padding:6px 2px;}
a{color:#0000EE;text-decoration:underline;}
hr{border:1px solid #999;}
</style>
"""

PAGE_LOGIN = f"""
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>内网网盘-登录</title>
{STYLE_NEW}
</head>
<body>
<div class="wrap">
<h2>SimpleLanDisk 局域网网盘</h2>
<hr>
<form action="/login" method="post">
用户名：<br>
<input type="text" name="username" size="30"><br>
密码：<br>
<input type="password" name="password" size="30"><br><br>
<input type="submit" value="登录">
</form>
</div>
</body>
</html>
"""

PAGE_LOGIN_FAIL = f"""
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>登录失败</title>
{STYLE_NEW}
</head>
<body>
<div class="wrap">
<h2>账号或密码错误</h2>
<a href="/login">返回登录页</a>
</div>
</body>
</html>
"""

PAGE_SUCCESS = """
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>操作成功</title>
</head>
<body>
<h2>操作成功!</h2>
<a href="/">返回文件列表</a>
</body>
</html>
"""

PAGE_ERROR = """
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>错误</title>
</head>
<body>
<h2>操作失败</h2>
<a href="/">回到首页</a>
</body>
</html>
"""


def get_session_info(request: Request):
    sid = request.cookies.get("session_id")
    if sid not in sessions:
        return None
    return sessions[sid]


def safe_join(root: str, subpath: str) -> str:
    user_path = unquote(subpath)
    final = os.path.abspath(os.path.join(root, user_path))
    if not final.startswith(os.path.abspath(root)):
        raise ValueError("越权访问禁止")
    return final


@app.api_route("/login", methods=["GET", "POST"])
async def login(request: Request, username: str = Form(None), password: str = Form(None)):
    if request.method == "GET":
        info = get_session_info(request)
        if info is not None:
            return RedirectResponse(url="/", status_code=302)
        return HTMLResponse(PAGE_LOGIN)

    if username in ACCOUNTS and ACCOUNTS[username]["pwd"] == password:
        new_sid = str(uuid.uuid4())
        sessions[new_sid] = {
            "user": username,
            "root": ACCOUNTS[username]["root"],
            "skin": ACCOUNTS[username]["skin"]
        }
        resp = RedirectResponse(url="/", status_code=302)
        resp.set_cookie("session_id", new_sid, max_age=86400 * 7)
        return resp
    else:
        return HTMLResponse(PAGE_LOGIN_FAIL)


@app.get("/logout")
async def logout(request: Request):
    sid = request.cookies.get("session_id")
    if sid and sid in sessions:
        del sessions[sid]
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("session_id")
    return resp


@app.get("/browse/{subpath:path}")
async def browse(request: Request, subpath: str = "", search: str = ""):
    info = get_session_info(request)
    if info is None:
        return RedirectResponse(url="/login", status_code=302)
    user_root = info["root"]
    skin = info["skin"]

    try:
        current_dir = safe_join(user_root, subpath)
    except ValueError:
        return RedirectResponse(url="/", status_code=302)

    if not os.path.isdir(current_dir):
        return RedirectResponse(url="/", status_code=302)

    author, words = random.choice(QUOTES_LIST)

    filelist_html = ""
    parent_path = os.path.dirname(subpath)
    if subpath != "":
        filelist_html += f'<div class="item"><a href="/browse/{quote(parent_path)}">.. 返回上一级</a></div>\n'

    for name in sorted(os.listdir(current_dir)):
        if name in [RECYCLE_NAME, SYSTEM_FOLDER]:
            continue
        if search != "" and search.lower() not in name.lower():
            continue
        full = os.path.join(current_dir, name)
        encoded_name = quote(os.path.join(subpath, name))
        if os.path.isdir(full):
            filelist_html += f'<div class="item">📂 <a href="/browse/{encoded_name}">{name}</a> <a href="/trash/move/{encoded_name}">[移入回收站]</a></div>\n'
        else:
            # ----------------- 视频文件检测 -----------------
            _, ext = os.path.splitext(name)
            if ext.lower() in VIDEO_EXTS:
                # 视频文件额外添加 “播放” 链接
                filelist_html += (
                    f'<div class="item">📽 '
                    f'<a href="/download/{encoded_name}">{name}</a> '
                    f'<a href="/watch/{encoded_name}">[播放]</a> '
                    f'<a href="/openlink/{encoded_name}">[直链]</a> '
                    f'<a href="/trash/move/{encoded_name}">[移入回收站]</a></div>\n'
                )
            else:
                # 普通文件
                filelist_html += f'<div class="item">📄 <a href="/download/{encoded_name}">{name}</a> <a href="/openlink/{encoded_name}">[直链]</a> <a href="/trash/move/{encoded_name}">[移入回收站]</a></div>\n'

    # ----------------- 页面渲染 -----------------
    if skin == "new":
        page_html = f"""
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>SimpleLanDisk-新版</title>
{STYLE_NEW}
</head>
<body>
<div class="wrap">
<div class="quote">「{words}」——{author}</div>
<hr>
<p><a href="/logout">退出登录</a> | <a href="/trash">回收站</a></p>
<p>当前路径: {subpath if subpath else '根目录'}</p>
<form action="/browse/{subpath}" method="get">
搜索：<input type="text" name="search" size="70">
<input type="submit" value="搜索">
</form>
<h3>上传文件</h3>
<form action="/upload" method="post" enctype="multipart/form-data">
<input type="hidden" name="target_folder" value="{subpath}">
<input type="file" name="file">
<input type="submit" value="上传">
</form>
<hr>
{filelist_html}
<br>
<a href="/">回到根目录</a>
</div>
</body>
</html>
"""
    else:
        page_html = f"""
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>SimpleLanDisk v0.1</title>
{STYLE_OLD}
</head>
<body>
<h2>SimpleLanDisk v0.1</h2>
<div>「{words}」——{author}</div>
<hr>
<p><a href="/logout">退出登录</a> | <a href="/trash">回收站</a></p>
<p>当前路径: {subpath if subpath else '根目录'}</p>
<form action="/browse/{subpath}" method="get">
搜索：<input type="text" name="search" size="30">
<input type="submit" value="搜索">
</form>
<h3>上传文件</h3>
<form action="/upload" method="post" enctype="multipart/form-data">
<input type="hidden" name="target_folder" value="{subpath}">
<input type="file" name="file">
<input type="submit" value="上传">
</form>
<hr>
{filelist_html}
<br>
<a href="/">回到根目录</a>
</body>
</html>
"""
    return HTMLResponse(page_html)


@app.get("/openlink/{subpath:path}")
async def open_link_page(request: Request, subpath: str):
    info = get_session_info(request)
    if info is None:
        return RedirectResponse(url="/login", status_code=302)
    user_root = info["root"]
    skin = info["skin"]
    try:
        file_path = safe_join(user_root, subpath)
    except ValueError:
        return HTMLResponse(PAGE_ERROR)
    if not os.path.isfile(file_path):
        return HTMLResponse(PAGE_ERROR)
    video_url = f"http://{request.client.host}:{PORT}/stream/{quote(subpath)}"
    filename = os.path.basename(unquote(subpath))
    style = STYLE_NEW if skin == "new" else STYLE_OLD
    html = f"""
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>直链-{filename}</title>
{style}
</head>
<body>
<h2>文件直链</h2>
<input type="text" value="{video_url}" size="75" readonly>
<br><br>
<a href="/">返回网盘</a>
</body>
</html>
"""
    return HTMLResponse(html)


# ====================== 5️⃣ 新增视频播放页面 ======================
@app.get("/watch/{subpath:path}")
async def watch_video(request: Request, subpath: str):
    """
    纯 HTML + CSS 的视频播放页（不依赖 JavaScript）。
    利用已经实现的 /stream 接口进行流式输出。
    """
    info = get_session_info(request)
    if info is None:
        return RedirectResponse(url="/login", status_code=302)

    user_root = info["root"]
    skin = info["skin"]

    try:
        video_path = safe_join(user_root, subpath)
    except ValueError:
        return HTMLResponse(PAGE_ERROR)

    if not os.path.isfile(video_path):
        return HTMLResponse(PAGE_ERROR)

    # 文件名 & MIME
    filename = os.path.basename(unquote(subpath))
    video_url = f"/stream/{quote(subpath)}"
    _, ext = os.path.splitext(filename)
    mime_type = VIDEO_MIME.get(ext.lower(), "video/mp4")   # 默认 fallback 为 mp4

    style = STYLE_NEW if skin == "new" else STYLE_OLD

    html = f"""
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>▶ 播放 - {filename}</title>
{style}
</head>
<body>
<div class="wrap">
<h2>▶ 正在播放：{filename}</h2>

<div class="video-wrapper">
    <video controls preload="metadata">
        <source src="{video_url}" type="{mime_type}">
        您的浏览器不支持 HTML5 视频播放。
    </video>
</div>

<p>
    <a href="/browse/{quote(os.path.dirname(subpath))}">← 返回目录</a> |
    <a href="/">← 回到根目录</a>
</p>
</div>
</body>
</html>
"""
    return HTMLResponse(html)


# ====================== 6️⃣ stream 端返回合适 MIME ======================
@app.get("/stream/{subpath:path}")
async def stream_video(request: Request, subpath: str):
    info = get_session_info(request)
    if info is None:
        return RedirectResponse(url="/login", status_code=302)

    user_root = info["root"]
    try:
        file_path = safe_join(user_root, subpath)
    except ValueError:
        return HTMLResponse(PAGE_ERROR)

    if not os.path.isfile(file_path):
        return HTMLResponse(PAGE_ERROR)

    # 依据后缀返回正确的 Content‑Type，浏览器即可流式播放
    _, ext = os.path.splitext(file_path)
    mime = VIDEO_MIME.get(ext.lower(), "application/octet-stream")
    return FileResponse(file_path, media_type=mime)


@app.get("/trash")
async def trash_page(request: Request):
    info = get_session_info(request)
    if info is None:
        return RedirectResponse(url="/login", status_code=302)
    skin = info["skin"]
    items_html = ""
    for name in sorted(os.listdir(RECYCLE_DIR)):
        enc = quote(name)
        items_html += f'<div class="item">📄 {name} <a href="/trash/restore/{enc}">[还原]</a> <a href="/trash/delete/{enc}">[永久删除]</a></div>\n'
    style = STYLE_NEW if skin == "new" else STYLE_OLD
    wrap_open = '<div class="wrap">' if skin == "new" else ''
    wrap_close = '</div>' if skin == "new" else ''
    html = f"""
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>回收站</title>
{style}
</head>
<body>
{wrap_open}
<h2>回收站</h2>
<a href="/">返回网盘</a>
<hr>
{items_html}
{wrap_close}
</body>
</html>
"""
    return HTMLResponse(html)


@app.get("/trash/move/{subpath:path}")
async def move_to_trash(request: Request, subpath: str):
    info = get_session_info(request)
    if info is None:
        return RedirectResponse(url="/login", status_code=302)
    user_root = info["root"]
    try:
        src = safe_join(user_root, subpath)
    except ValueError:
        return HTMLResponse(PAGE_ERROR)
    if not os.path.exists(src):
        return HTMLResponse(PAGE_ERROR)
    basename = os.path.basename(src)
    dst = os.path.join(RECYCLE_DIR, basename)
    shutil.move(src, dst)
    return RedirectResponse(url="/", status_code=302)


@app.get("/trash/restore/{filename}")
async def restore_item(request: Request, filename: str):
    info = get_session_info(request)
    if info is None:
        return RedirectResponse(url="/login", status_code=302)
    user_root = info["root"]
    try:
        trash_file = safe_join(RECYCLE_DIR, filename)
        dest = safe_join(user_root, filename)
    except ValueError:
        return HTMLResponse(PAGE_ERROR)
    if not os.path.exists(trash_file):
        return HTMLResponse(PAGE_ERROR)
    shutil.move(trash_file, dest)
    return RedirectResponse(url="/trash", status_code=302)


@app.get("/trash/delete/{filename}")
async def permanently_delete(request: Request, filename: str):
    info = get_session_info(request)
    if info is None:
        return RedirectResponse(url="/login", status_code=302)
    try:
        target = safe_join(RECYCLE_DIR, filename)
    except ValueError:
        return HTMLResponse(PAGE_ERROR)
    if os.path.isfile(target):
        os.remove(target)
    elif os.path.isdir(target):
        shutil.rmtree(target)
    else:
        return HTMLResponse(PAGE_ERROR)
    return RedirectResponse(url="/trash", status_code=302)


@app.get("/")
async def root():
    return RedirectResponse(url="/browse/", status_code=302)


@app.post("/upload")
async def upload(request: Request, file: UploadFile | None = File(None), target_folder: str = Form("")):
    info = get_session_info(request)
    if info is None:
        return RedirectResponse(url="/login", status_code=302)
    user_root = info["root"]
    if not file or not file.filename:
        return HTMLResponse(PAGE_ERROR)

    try:
        save_dir = safe_join(user_root, target_folder)
    except ValueError:
        return HTMLResponse(PAGE_ERROR)

    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, file.filename)
    with open(save_path, "wb") as f:
        f.write(await file.read())
    return HTMLResponse(PAGE_SUCCESS)


@app.get("/download/{subpath:path}")
async def download(request: Request, subpath: str):
    info = get_session_info(request)
    if info is None:
        return RedirectResponse(url="/login", status_code=302)
    user_root = info["root"]
    try:
        file_path = safe_join(user_root, subpath)
    except ValueError:
        return RedirectResponse(url="/", status_code=302)

    if not os.path.isfile(file_path):
        return RedirectResponse(url="/", status_code=302)
    return FileResponse(file_path, media_type="application/octet-stream", filename=os.path.basename(file_path))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
