import os
import threading
from flask import Flask, request, abort, send_from_directory
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, VideoSendMessage
from linebot import LineBotApi, WebhookHandler
import yt_dlp

app = Flask(__name__)

# 從環境變數讀取 LINE 設定（Railway 環境變數需要設定）
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
LINE_SECRET = os.getenv('LINE_SECRET')

# 檢查環境變數是否設置
if not LINE_ACCESS_TOKEN or not LINE_SECRET:
    print("Error: LINE_ACCESS_TOKEN or LINE_SECRET not set!")
    exit(1)  # 如果沒有設置正確則退出程式

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# 設定 public 資料夾的路徑
public_folder = 'public'

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
        send_video_to_user(event.source.user_id, video_path)  # 傳送影片給使用者

        
        # 設置計時器，10秒後重設影片
        threading.Timer(5, reset_video, [video_path]).start()
        
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="影片下載失敗或無法處理該網址！"))

def download_video(url):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(public_folder, 'downloaded_video.mp4'),  # 儲存影片的路徑，保證它在 public 資料夾
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return 'downloaded_video.mp4'
    except Exception as e:
        print(f"下載錯誤: {e}")
        return None

@app.route('/public/<filename>')
def serve_file(filename):
    return send_from_directory(public_folder, filename)

def send_video_to_user(user_id, video_path):
    try:
        # 使用 Railway 提供的公開 URL 來發送影片
        video_url = f'https://lineapp-production.up.railway.app/public/{video_path}'
        preview_url = 'https://your-preview-image-url'  # 可自定義縮圖 URL

        # 發送影片給使用者
        line_bot_api.push_message(
            user_id,
            VideoSendMessage(
                original_content_url=video_url,  # 影片的公開 URL
                preview_image_url=preview_url  # 影片縮圖
            )
        )
    except Exception as e:
        print(f"發送影片錯誤: {e}")

@handler.add(MessageEvent, message=TextMessage)
def reset_video(video_path):
    # 10秒後重設影片
    try:
        # 刪除影片檔案
        if os.path.exists(os.path.join(public_folder, video_path)):
            os.remove(os.path.join(public_folder, video_path))
        print(f"影片 {video_path} 已重設")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="影片下載成功!!"))
    except Exception as e:
        print(f"重設影片錯誤: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
