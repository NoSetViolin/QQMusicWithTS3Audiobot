import requests

# 用户输入地址和内容
address = input("请输入API地址（ IP/域名 和 端口 ）: ")
content = input("请粘贴cookie: ")

# 构造 URL 和数据
url = f"http://{address}/user/setCookie"
headers = {"Content-Type": "application/json"}
data = {"data": content}

# 发送 POST 请求
try:
    response = requests.post(url, json=data, headers=headers)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
except requests.RequestException as e:
    print(f"请求失败: {e}")
