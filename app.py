from flask import Flask, request, render_template, jsonify
import requests
import re

app = Flask(__name__)

# -----------------配置区域------------------
QQ_MUSIC_API = "http://10.0.0.254:3300"
BACKEND_API = "http://localhost:7000"
GOTIFY_URL = "http://localhost:48080/message"  # Gotify URL配置
GOTIFY_TOKEN = "A0aCk_0TG0MS0W0"               # 这里填你的token
# ----------------------------------------------------

def extract_segment(text, key):
    """ 通用正则提取函数 """
    pattern = rf'"{key}"\s*:\s*"([^"]+)"'
    match = re.search(pattern, text)
    return match.group(1) if match else None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        song_name = request.form.get("song")
        audio_type = request.form.get("quality")
        bot_id = request.form.get("botid")  # 获取用户选择的 BOT ID
        print(f"\n[前端] 收到请求：歌曲={song_name}, 音质={audio_type}, BOT ID={bot_id}")

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

            # ============= Gotify推送 =============
            try:
                requests.post(
                    GOTIFY_URL,
                    params={"token": GOTIFY_TOKEN},
                    data={
                        "title": "QQ音乐点歌",
                        "message": f"用户点了歌曲：{target_songname}",
                        "priority": "8"
                    },
                    timeout=3  
                )
                print("[推送] Gotify通知已发送")
            except Exception as e:
                print(f"[推送] 通知失败: {str(e)}")

            # 发送到后端
            payload = {
                "complete_url": play_url,
                "song_name": target_songname,
                "album_cover_url": cover_url,
                "botid": bot_id  # 将 BOT ID 添加到 payload 中
            }
            print(f"[前端] 发送到后端的数据：{payload}")
            requests.post(f"{BACKEND_API}/api/send-url", json=payload)

            return render_template("index.html", play_url=play_url, song_name=song_name, cover_url=cover_url)

        except requests.exceptions.RequestException as e:
            print(f"[前端] 网络请求异常：{str(e)}")
            return jsonify({"error": f"网络请求失败: {str(e)}"}), 500
        except Exception as e:
            print(f"[前端] 处理异常：{str(e)}")
            return jsonify({"error": f"数据处理失败: {str(e)}"}), 500

    return render_template("index.html")

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
    app.run(host="0.0.0.0", port=29111, debug=True)