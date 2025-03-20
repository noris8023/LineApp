import os
from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot import LineBotApi, WebhookHandler
import yt_dlp

app = Flask(__name__)

# 從環境變數讀取 LINE 設定（Railway 環境變數需要設定）
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
LINE_SECRET = os.getenv('LINE_SECRET')

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    url = event.message.text.strip()

    if not url.startswith("http"):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請提供有效的影片網址！"))
        return

    video_path = download_video(url)
    
    if video_path:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="影片下載完成，請稍後..."))
        cloud_link = upload_to_cloud(video_path)  # 上傳至雲端
        if cloud_link:
            line_bot_api.push_message(event.source.user_id, TextSendMessage(text=f"影片已上傳，請點擊連結下載：\n{cloud_link}"))
        else:
            line_bot_api.push_message(event.source.user_id, TextSendMessage(text="上傳失敗，請稍後再試！"))
        os.remove(video_path)  # 刪除本地影片
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="影片下載失敗或無法處理該網址！"))

def download_video(url):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloaded_video.mp4',  # 下載的影片檔名
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return 'downloaded_video.mp4'
    except Exception as e:
        print(f"下載錯誤: {e}")
        return None

def upload_to_cloud(video_path):
    """
    模擬上傳至雲端（可以改為 Google Drive, S3, Dropbox 等服務）
    """
    try:
        cloud_link = f"https://your-cloud-service.com/{video_path}"  # 替換為真正的雲端上傳邏輯
        return cloud_link
    except Exception as e:
        print(f"雲端上傳錯誤: {e}")
        return None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
