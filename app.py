from flask import Flask, request, abort, send_file
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import yt_dlp
import os

app = Flask(__name__)

# 填入你在 Line Developers 取得的 Channel Access Token 和 Secret
LINE_CHANNEL_ACCESS_TOKEN = '你的 Channel Access Token'
LINE_CHANNEL_SECRET = '你的 Channel Secret'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
    url = event.message.text

    if not url.startswith("http"):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請提供有效的影片網址！"))
        return

    video_path = download_video(url)
    
    if video_path:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="影片下載完成，開始回傳檔案..."))
        send_file_to_user(event.source.user_id, video_path)
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

def send_file_to_user(user_id, video_path):
    try:
        with open(video_path, 'rb') as video_file:
            line_bot_api.push_message(user_id, TextSendMessage(text="正在傳送影片..."))
            line_bot_api.push_message(user_id, TextSendMessage(text="因影片過大，請至雲端查看！"))
        os.remove(video_path)  # 傳送完後刪除檔案
    except Exception as e:
        print(f"傳送影片失敗: {e}")

if __name__ == "__main__":
    app.run(debug=True)
