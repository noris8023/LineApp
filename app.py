import os
from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, VideoSendMessage
from linebot import LineBotApi, WebhookHandler
import yt_dlp

app = Flask(__name__, static_url_path='/public', static_folder='public')

# 從環境變數讀取 LINE 設定（Railway 環境變數需要設定）
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
LINE_SECRET = os.getenv('LINE_SECRET')

# 檢查環境變數是否設置
if not LINE_ACCESS_TOKEN or not LINE_SECRET:
    print("Error: LINE_ACCESS_TOKEN or LINE_SECRET not set!")
    exit(1)  # 如果沒有設置正確則退出程式

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
        send_video_to_user(event.source.user_id, video_path)  # 傳送影片給使用者
        os.remove(f'public/{video_path}')  # 刪除本地影片
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="影片下載失敗或無法處理該網址！"))

def download_video(url):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'public/downloaded_video.mp4',  # 下載的影片檔案儲存在 public 資料夾中
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return 'downloaded_video.mp4'
    except Exception as e:
        print(f"下載錯誤: {e}")
        return None

def send_video_to_user(user_id, video_path):
    try:
        # 使用 Railway 公共 URL 發送影片
        public_video_url = f'https://lineapp-production.up.railway.app/public/{video_path}'  # 使用 public 資料夾中的影片
        public_preview_url = f'https://lineapp-production.up.railway.app/public/preview.jpg'  # 影片縮圖，這裡也需要存放於 public 資料夾
        
        # 發送影片給使用者
        line_bot_api.push_message(
            user_id,
            VideoSendMessage(
                original_content_url=public_video_url,  # 公共影片的 URL
                preview_image_url=public_preview_url  # 影片縮圖的 URL
            )
        )
    except Exception as e:
        print(f"發送影片錯誤: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
