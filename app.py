from flask import Flask, request, abort, send_file
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.v3 import LineBotApi
from linebot.v3.webhook import WebhookHandler
import yt_dlp
import os

app = Flask(__name__)


line_bot_api = LineBotApi('NHC9uecjXr3bEcR9FuhfKBaCJ30XnGpazMVjqn7CCUk6uHdCTv5pc+VdIqY1jYz5ykxi6gMFk9VxlNImbujsAa28wyiz+IW7GVh6UGG7qLVBMZe+8yX5S6Nz60Yt5hyPhmfl4PoPTq50i4J1YGnBzAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('c5e8feb93963ce63f594d7a5841347d1')

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
