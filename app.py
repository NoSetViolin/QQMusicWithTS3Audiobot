from flask import Flask, request, render_template, jsonify
import requests
import re
from packaging import version
import threading
import time
import schedule
import json
import os

app = Flask(__name__)

# -----------------配置区域------------------
QQ_MUSIC_API = "http://10.0.0.254:3300"
BACKEND_API = "http://10.0.0.70:7000"
# ----------------------------------------------------

# -----------------下面不要动----------------
__version__ = "3.2.4"
HISTORY_FILE = "song_history.json"
# ------------------------------------------

def load_history():
    """ 从文件加载历史记录 """
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:  # 检查文件内容是否为空
                    return json.loads(content)
                else:
                    print(f"[警告] {HISTORY_FILE} 文件为空，返回空列表")
                    return []
        else:
            print(f"[信息] {HISTORY_FILE} 文件不存在，创建新文件")
            save_history([])  # 创建空文件
            return []
    except json.JSONDecodeError as e:
        print(f"[错误] 解析 {HISTORY_FILE} 失败: {e}，返回空列表")
        return []
    except Exception as e:
        print(f"[错误] 加载历史记录时发生未知错误: {e}，返回空列表")
        return []

def save_history(history):
    """ 保存历史记录到文件 """
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[错误] 保存历史记录到 {HISTORY_FILE} 失败: {e}")

def extract_segment(text, key):
    """ 通用正则提取函数 """
    pattern = rf'"{key}"\s*:\s*"([^"]+)"'
    match = re.search(pattern, text)
    return match.group(1) if match else None

def check_for_updates():
    """ 检查更新 """
    try:
        print("[更新检查] 正在检查更新...")
        response = requests.get("http://kennyz.cn:27721/chfs/shared/cdn/latestjson/TS3AudioBotQQMusicAPI/latestVer.json")
        response.raise_for_status()
        latest_info = response.json()
        latest_version = latest_info.get("version")
        download_url = latest_info.get("url")
        release_notes = latest_info.get("release_notes", "")

        if latest_version and version.parse(latest_version) > version.parse(__version__):
            print(f"\n[更新检查] 发现新版本: {latest_version}")
            print(f"[更新检查] 更新内容: {release_notes}")
            print(f"[更新检查] 下载链接: {download_url}")
        else:
            print("[更新检查] 当前已是最新版本。")
    except requests.RequestException as e:
        print(f"[更新检查] 检查更新失败: {e}")
    except Exception as e:
        print(f"[更新检查] 更新检查异常: {e}")

def run_scheduler():
    """ 运行定时任务 """
    schedule.every(1).hours.do(check_for_updates)
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次待执行任务

@app.route("/", methods=["GET", "POST"])
def index():
    song_history = load_history()
    if request.method == "POST":
        song_name = request.form.get("song")
        audio_type = request.form.get("quality")
        bot_id = request.form.get("botid")  # 获取用户选择的 BOT ID
        print(f"\n[前端] 收到请求：歌曲={song_name}, 音质={audio_type}, BOT ID={bot_id}")

        # 更新历史记录
        new_entry = {"song": song_name, "botid": bot_id, "count": 1}
        found = False
        for item in song_history:
            if item["song"] == song_name and item["botid"] == bot_id:
                item["count"] += 1
                found = True
                break
        if not found:
            song_history.insert(0, new_entry)  # 新歌曲插到顶部
        if len(song_history) > 10:  # 限制历史记录长度
            song_history.pop()
        save_history(song_history)

        search_url = f"{QQ_MUSIC_API}/search?key={song_name}"
        print(f"[前端] 正在发送搜索请求：{search_url}")
        
        try:
            response = requests.get(search_url)
            response.raise_for_status()
            print(f"[前端] 收到API响应，状态码：{response.status_code}")
            print(f"[前端] 响应内容预览：{response.text[:200]}...")  # 打印前200字符

            # 提取歌曲信息
            try:
                song_data = response.json()
                print("[前端] JSON解析成功")
                target_songname = song_data["data"]["list"][0]["songname"]
                albummid = song_data["data"]["list"][0].get("albummid")
                print(f"[前端] 从JSON获取：songname={target_songname}, albummid={albummid}")
            except Exception as e:
                print(f"[前端] JSON解析失败，使用正则备用方案。错误：{str(e)}")
                target_songname = extract_segment(response.text, "songname") or "未知歌曲"
                albummid = extract_segment(response.text, "albummid")
                print(f"[前端] 正则提取结果：songname={target_songname}, albummid={albummid}")

            # songmid,strmeidamid检查
            songmid = extract_segment(response.text, "songmid")
            strmediamid = extract_segment(response.text, "strMediaMid")
            print(f"[前端] 关键参数：songmid={songmid}, strmediamid={strmediamid}")
            if not songmid or not strmediamid:
                print("[前端] 错误：缺少必要参数！")
                return jsonify({"error": "未找到必要参数！"}), 400

            # 构造封面图URL
            play_url = f"{QQ_MUSIC_API}/song/url?id={songmid}&type={audio_type}&mediaId={strmediamid}&isRedirect=1"
            cover_url = f"http://y.qq.com/music/photo_new/T002R300x300M000{albummid}.jpg" if albummid else None
            print(f"[前端] 生成播放URL：{play_url}")
            print(f"[前端] 生成封面URL：{cover_url}")

            # 发送到后端
            payload = {
                "complete_url": play_url,
                "song_name": target_songname,
                "album_cover_url": cover_url,
                "botid": bot_id  # 将 BOT ID 添加到 payload 中
            }
            print(f"[前端] 发送到后端的数据：{payload}")
            requests.post(f"{BACKEND_API}/api/send-url", json=payload)

            return render_template("index.html", play_url=play_url, song_name=song_name, cover_url=cover_url, song_history=song_history)

        except requests.exceptions.RequestException as e:
            print(f"[前端] 网络请求异常：{str(e)}")
            return jsonify({"error": f"网络请求失败: {str(e)}"}), 500
        except Exception as e:
            print(f"[前端] 处理异常：{str(e)}")
            return jsonify({"error": f"数据处理失败: {str(e)}"}), 500

    return render_template("index.html", song_history=song_history)

@app.route("/stop", methods=["POST"])
def stop_proxy():
    """ 停止请求转发路由 """
    try:
        print("\n[主程序] 收到停止请求，正在转发到后端...")
        bot_id = request.form.get("botid")  # 获取选择的 BOT ID
        if bot_id is None:
            bot_id = "0"  # 默认值为 0
        payload = {"botid": bot_id}  # 将 BOT ID 添加到 payload 中

        # 转发到后端服务
        resp = requests.post(f"{BACKEND_API}/api/send-stop", json=payload)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "后端服务不可用"}), 502
    except Exception as e:
        print(f"[主程序] 转发异常：{str(e)}")
        return jsonify({"error": "服务暂时不可用"}), 500

if __name__ == "__main__":
    # 仅在非调试模式或主进程中启动调度器
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # 启动时立即检查一次更新
        check_for_updates()
        # 启动定时任务线程
        threading.Thread(target=run_scheduler, daemon=True).start()
    
    app.run(host="0.0.0.0", port=29111, debug=True)