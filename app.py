import os
from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import TextMessage

app = Flask(__name__)

# 使用 Railway 變數名稱
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET')

if not LINE_ACCESS_TOKEN or not LINE_SECRET:
    raise ValueError("❌ LINE_CHANNEL_ACCESS_TOKEN 或 LINE_CHANNEL_SECRET 未設定！請檢查 Railway 變數設定。")

messaging_api = MessagingApi(LINE_ACCESS_TOKEN)
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
        reply_text = "請提供有效的影片網址！"
    else:
        video_path = download_video(url)
        if video_path:
            reply_text = "影片下載完成，請稍後..."
            cloud_link = upload_to_cloud(video_path)
            if cloud_link:
                reply_text = f"影片已上傳，請點擊下載：\n{cloud_link}"
            else:
                reply_text = "上傳失敗，請稍後再試！"
            os.remove(video_path)
        else:
            reply_text = "影片下載失敗或無法處理該網址！"

    reply_message = ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[TextMessage(text=reply_text)]
    )
    messaging_api.reply_message(reply_message)

def download_video(url):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloaded_video.mp4',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return 'downloaded_video.mp4'
    except Exception as e:
        print(f"下載錯誤: {e}")
        return None

def upload_to_cloud(video_path):
    return f"https://your-cloud-service.com/{video_path}"  # 這裡改成你的雲端上傳邏輯

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
