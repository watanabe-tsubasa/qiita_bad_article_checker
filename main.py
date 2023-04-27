from distutils.log import error
from fastapi import FastAPI, Request
import logging
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv; load_dotenv()
import uvicorn
import os
import requests
from src.handle_markdown import HandleParagraph, HandleTagEvent, HandleCodeBlock, HandleTagEvent

CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET') or 'CHANNEL_SECRET'
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN') or 'CHANNEL_ACCESS_TOKEN'

app = FastAPI()

line_bot_api = LineBotApi(channel_access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(channel_secret=CHANNEL_SECRET)

logger = logging.getLogger(__name__)

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers['X-Line-Signature']
    
    body = await request.body()
    logger.info("Request body:" + body.decode())
    
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        logger.warning("Invalid signature")
        return "Invalid signature"
    
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text.startswith("https://qiita.com"):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='記事を判定します。少々お待ちください。')
        )
        try:
            res = requests.get(event.message.text + '.md')
            article_text = res.content.decode(res.encoding)
            
            # タグについて
            tag_handler = HandleTagEvent(article_text)
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text=tag_handler.count_tag())
            )
            tag_list = tag_handler.get_tag_list()
            for tag in tag_list:
                message = tag_handler.validate_tag_info(tag)
                if message != 'is_collect':
                    line_bot_api.push_message(
                        event.source.user_id,
                        TextSendMessage(text=message)
                    )
            
            # コードブロックの部分について
            code_handler = HandleCodeBlock(article_text)
            code_block_list = code_handler.get_code_block()
            if code_block_list != 'no_code':
                for i, match in enumerate(code_block_list):
                    message = code_handler.validate_code_lang(i, match)
                    line_bot_api.push_message(
                        event.source.user_id,
                        TextSendMessage(text=message)
                    )
            
            # 段落構成の部分について
            paragraph_handler = HandleParagraph(article_text)
            if paragraph_handler.is_contain_h_one() != 'is_collect':
                message = paragraph_handler.is_contain_h_one()
                line_bot_api.push_message(
                        event.source.user_id,
                        TextSendMessage(text=message)
                    )
            if paragraph_handler.is_corrupted_paragraph() != 'is_collect':
                message = paragraph_handler.is_corrupted_paragraph()
                line_bot_api.push_message(
                        event.source.user_id,
                        TextSendMessage(text=message)
                    )
            
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text='簡易フィードバックが完了しました', )
            )
            
        except error:
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text=f'エラーが発生しました。事務局まで連絡してください。\n{error}', )
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='Qiita記事のURLを送信してください')
        )
    
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, log_level='info')