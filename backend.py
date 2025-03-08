from flask import Flask, request, jsonify
import requests
import urllib.parse

app = Flask(__name__)

# -----------------配置区域------------------
BASE_API = "http://10.0.0.254:58913"
# ------------------------------------------------------------

@app.route('/api/send-url', methods=['POST'])
def send_url():
    try:
        print("\n[后端] 收到新请求，开始处理...")
        data = request.get_json()
        if not data:
            print("[后端] 错误：请求体不是有效的JSON")
            return jsonify({"error": "请求必须为JSON格式"}), 400

        bot_id = data.get("botid")  # 获取选择的 BOT ID
        if bot_id is None:
            bot_id = "0"  # 默认值为 0
        print(f"[后端] 选中的 BOT_ID 为：{bot_id}")

        print(f"[后端] 收到完整数据：{data}")
        responses = []
        
        # 生成 API 路径
        api_paths = {
            "play": f"/api/bot/use/{bot_id}/(/play",
            "stop": f"/api/bot/use/{bot_id}/(/pause", 
            "desc": f"/api/bot/use/{bot_id}/(/bot/description/set",
            "pm_channel": f"/api/bot/use/{bot_id}/(/pm/channel/当前正在播放：",
            "avatar": f"/api/bot/use/{bot_id}/(/bot/avatar/set"
        }

        # 处理播放请求
        if complete_url := data.get("complete_url"):
            print(f"\n[后端] 处理播放请求：{complete_url}")
            encoded_url = urllib.parse.quote(complete_url, safe='')
            play_api = f"{BASE_API}{api_paths['play']}/{encoded_url})"
            print(f"[后端] 构造播放 API：{play_api}")
            
            try:
                resp = requests.get(play_api, timeout=5)
                print(f"[后端] 播放请求响应状态码：{resp.status_code}")
                responses.append("播放请求已发送")
            except Exception as e:
                print(f"[后端] 播放请求失败：{str(e)}")
                responses.append(f"播放请求失败: {str(e)}")

        # 处理歌曲信息
        if song_name := data.get("song_name"):
            print(f"\n[后端] 处理歌曲信息：{song_name}")
            
            # 描述设置
            encoded_name = urllib.parse.quote(song_name, safe='')
            desc_api = f"{BASE_API}{api_paths['desc']}/{encoded_name})"
            print(f"[后端] 构造描述 API：{desc_api}")
            try:
                resp = requests.get(desc_api, timeout=3)
                print(f"[后端] 描述设置响应状态码：{resp.status_code}")
                responses.append("描述更新成功")
            except Exception as e:
                print(f"[后端] 描述设置失败：{str(e)}")
                responses.append(f"描述更新失败: {str(e)}")

            # 频道通知
            pm_api = f"{BASE_API}{api_paths['pm_channel']}{song_name})"
            print(f"[后端] 构造频道通知 API：{pm_api}")
            try:
                resp = requests.get(pm_api, timeout=3)
                print(f"[后端] 频道通知响应状态码：{resp.status_code}")
                responses.append("频道通知已发送")
            except Exception as e:
                print(f"[后端] 频道通知失败：{str(e)}")
                responses.append(f"频道通知失败: {str(e)}")

        # 处理专辑封面
        if cover_url := data.get("album_cover_url"):
            print(f"\n[后端] 处理专辑封面：{cover_url}")
            if cover_url:
                encoded_cover = urllib.parse.quote(cover_url, safe='')
                avatar_api = f"{BASE_API}{api_paths['avatar']}/{encoded_cover})"
                print(f"[后端] 构造头像 API：{avatar_api}")
                try:
                    resp = requests.get(avatar_api, timeout=5)
                    print(f"[后端] 头像设置响应状态码：{resp.status_code}")
                    responses.append("专辑头像设置成功")
                except Exception as e:
                    print(f"[后端] 头像设置失败：{str(e)}")
                    responses.append(f"头像设置失败: {str(e)}")

        print(f"\n[后端] 最终响应列表：{responses}")
        return jsonify({"status": "success", "details": responses}), 200

    except Exception as e:
        print(f"\n[后端] 全局异常：{str(e)}")
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500
    
@app.route('/api/send-stop', methods=['POST'])
def handle_stop():
    """ 处理停止请求 """
    print("\n[后端] 收到停止请求")
    try:
        data = request.get_json()
        bot_id = data.get("botid") if data else None  # 获取用户选择的 BOT ID
        if bot_id is None:
            bot_id = "0"  # 默认值为 0
        print(f"[后端] 选中的 BOT_ID 为：{bot_id}")

        # 停止 API 路径
        stop_api = f"{BASE_API}/api/bot/use/{bot_id}/(/stop"
        print(f"[后端] 构造机器人停止 API：{stop_api}")

        # 发送请求到机器人API
        resp = requests.get(stop_api, timeout=3)
        return jsonify({
            "status": "success",
            "api_status": resp.status_code,
            "message": "停止命令已送达"
        }), 200
    except requests.exceptions.RequestException as e:
        print(f"[后端] 请求失败：{str(e)}")
        return jsonify({"error": "机器人服务不可达"}), 502
    except Exception as e:
        print(f"[后端] 处理异常：{str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=False)