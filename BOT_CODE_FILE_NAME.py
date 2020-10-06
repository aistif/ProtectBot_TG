# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 15:44:40 2020

@author: aistif
GitHub: https://github.com/aistif/
Twitter: @aishtif

"""

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatPermissions
import pandas as pd
import numpy as np
import os
import re

PORT = int(os.environ.get('PORT', 5000))

## Create logging file if needed
logging.basicConfig(filename='Logs.log',
                    level=logging.INFO,
                    filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
TOKEN = 'YOUR_BOT_TOKEN'


## A function returns bool value deciding whether received text is a spam or not
def is_spam(text):
    # Create DataFrame of spam words (custom list) from CSV file named spam_words.csv
    spam_words = pd.read_csv('spam_words.csv',
                             header=None,
                             names=['spam_words'],
                             engine="python",
                             encoding='utf-8'
                            )

    if any(word in text for word in spam_words['spam_words']): #or text.count('#') > 2 or text.count('@') > 1:
        return True
    else:
        return False 


## A function that receives text and clean it for eaier filtering
# of spam words (handles Arabic text currently)
def cleanText(text):
    text = re.sub(r'[,.;?؟،:؛!&$-]+\ *', ' ', text)
    text = re.sub(r'[إأٱآا]', 'ا', text)
    text = re.sub(r'[ىي]', 'ي', text)
    text = re.sub(r'[ئؤ]', 'ء', text)
    text = re.sub(r'ة', 'ه', text)

    ## Remove diacritics (Tashkeel)
    diacritics = re.compile(""" ّ    | # Tashdid
                                َ    | # Fatha
                                ً    | # Tanwin Fath
                                ُ    | # Damma
                                ٌ    | # Tanwin Damm
                                ِ    | # Kasra
                                ٍ    | # Tanwin Kasr
                                ْ    | # Sukun
                                ـ     # Tatwil/Kashida
                            """, re.VERBOSE)
    text = re.sub(diacritics, '', text)

    # Clean text from non-Arabic letters
    text = re.sub(r'[^ء-ي ]', '', text)

    return text


## The function (filterMedia) aims to filter out media that has improper captions
# and then kicks out the sender if the sender ID is not the AdminID
def filterMedia(update, context):
    """Filter media messages."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_id = update.message.message_id
    caption = update.message.caption
    caption = cleanText(caption)

    if chat_id != ADMIN_ID_HERE and is_spam(caption):
        context.bot.deleteMessage(chat_id=chat_id, message_id=message_id)
        context.bot.kickChatMember(chat_id=chat_id, user_id=user_id)

    ## Forward the media to the admin privately for monitoring purposes of uncaptured
    # offensive media to leave it for human decision
    elif chat_id != ADMIN_ID_HERE:
        msg = "وسائط جديدة وصلت للمجموعة:"
        logging.info(chat_id)
        
        context.bot.send_message(chat_id=ADMIN_ID_HERE, text=msg)
        context.bot.forward_message(chat_id=ADMIN_ID_HERE, from_chat_id=chat_id, message_id=message_id)
    else:
        pass                  


## The function (filterTexts) aims to filter out spam/improper messages
# and then kicks out the sender if the sender ID is not the AdminID
def filterTexts(update, context):
    """Filter media messages."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_id = update.message.message_id
    msg_body = update.message.text
    msg_body = cleanText(msg_body)

    is_spamw = is_spam(msg_body)

    if chat_id != ADMIN_ID_HERE and is_spamw:
        context.bot.deleteMessage(chat_id=chat_id, message_id=message_id)
        context.bot.kickChatMember(chat_id=chat_id, user_id=user_id)
        
    else:
        pass


def main():
    """Start the bot."""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Send media to filterMedia function
    msg_fltr = MessageHandler((Filters.video | Filters.audio | Filters.photo) & (~Filters.command) , filterMedia)
    dp.add_handler(msg_fltr)

    # Send text to filterTexts function
    txt_fltr = MessageHandler((Filters.text | Filters.caption) & (~Filters.command) , filterTexts)
    dp.add_handler(txt_fltr)

    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('YOUR_HEROKU_PROJECT_URL' + TOKEN)

    updater.idle()


if __name__ == '__main__':
    main()