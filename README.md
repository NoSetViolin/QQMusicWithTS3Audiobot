# QQMusicWithTS3Audiobot

这是一个网页点歌程序，原理是获取用户输入歌名，qqmusicAPI返回数据中提取第一位的songmid和mediamid进行传递，API目前只支持手动更新cookie，而且QQ音乐的cookie有效期较短（只有4天这样）

## 用法:

### 先执行 pip install -r requirements.txt安装依赖模块
### · app.py

   这是网页的主程序，用编辑器打开后请自行按照我里面提示修改保存，网页html在templates/index.html需要可以修改

   具体修改内容为：
   ```python
   QQ_MUSIC_API = "http://localhost:3300"        
   BACKEND_API = "http://localhost:7000"   
   ```     

   运行 python app.py

### · backend.py

   这个是用来给TS3Audiobot API提交播放的，用编辑器打开以后按照我的提示修改保存

   具体修改内容为
   ```python
   BASE_API = "http://localhost:58913"  # BOT后台地址（示例：http://tsbot.cn:58913）
   ```
   运行 python server.py


### · cookie.py

   比如说你的API是 `http://123.cn:3300/` 在输入地址时就输入 123.cn:3300

   记住不要有`/`


   运行 python cookie.py

### · templates/index.html

   网页模板，可改
   需要注意220-226行可以改
   ```html
   <!-- 选择 BOT ID的部分 -->
      <label for="botid">选择 BOT ID：</label>
         <select id="botid" name="botid" required>
            <option value="0">BOT 0</option>
            <option value="1">BOT 1</option>
            <option value="2">BOT 2</option>
         </select>
   ```
   按需增加bot数量


## cookie如何获取？

打开y.qq.com并登录，登录成功后按F12启用开发者面板，在开发者面板顶栏众多选项中选择 网络/Network。

此时刷新网页，会刷很多文件，拉到最顶上，有一个叫y.qq.com的文件。

单击他  在右边的展开面板中往下滑找到 Cookie：，将后面的内容复制粘贴即可

## 关于



更新日志：3.2.1 [R]  2025/02/21 05:27

-- 修复了在某些机器上BOT头像不加载问题

-- 多BOT点歌，暂停 支持

-- 性能优化（玄学） 点歌更快

没了