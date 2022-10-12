from enum import Enum, auto
from textwrap import dedent
from time import sleep

from environs import Env
from redis import Redis
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

from moltin_api import get_products, get_inventory

import logging

logger = logging.getLogger(__name__)

class States(Enum):
    HANDLE_MENU = auto()


def start(update, context):
    keyboard = []
    products = get_products()
    context.chat_data['products'] = products
    for product in products:
        keyboard.append(
            [InlineKeyboardButton(product['name'],
                                  callback_data=product['id'])]
        )
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Привет!',
        reply_markup=reply_markup,
    )

    return States.HANDLE_MENU


def handle_menu(update, context):
    query = update.callback_query
    inventory = get_inventory(query.data)
    on_stock = inventory['available']
    for product in context.chat_data['products']:
        if product['id'] == query.data:
            name = product['name']
            price = product['meta']['display_price']['with_tax']['formatted']
            description = product['description']
            text = dedent(f'''
                {name}

                {price}
                {on_stock} на складе

                {description}'''
            )
    update.callback_query.edit_message_text(text)

    return States.HANDLE_MENU


def echo(update, context):
    user_id = update.effective_user.id
    if update.message:
        text = update.message.text
    else:
        query = update.callback_query
        text = f'Вы задали {query.data}'
    keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счёт'],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.callback_query.edit_message_text(text)

    return States.REQUEST


def cancel(update, context):
    username = update.effective_user.first_name
    logger.info(f'User {username} canceled the conversation.')
    update.message.reply_text('До встречи!',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, error):
    """Log Errors caused by Updates."""
    logger.warning(f'Update "{update}" caused error "{error}"')


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
    env = Env()
    env.read_env()
    
    # db_connection = Redis(
    #     host=env.str('REDIS_HOST'),
    #     port=env.str('REDIS_PORT'),
    #     username=env.str('REDIS_USERNAME', default='default'),
    #     password=env.str('REDIS_PASSWORD'),
    #     decode_responses=True,
    # )
    # logger.info(f'db_connection_ping: {db_connection.ping()}')

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            States.HANDLE_MENU: [
                CallbackQueryHandler(handle_menu),
                MessageHandler(Filters.text, echo),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    while True:
        try:
            updater = Updater(token=env.str('TG_BOT_TOKEN'))
            dp = updater.dispatcher
            dp.add_handler(conv_handler)
            dp.add_error_handler(error)
            updater.start_polling()
            updater.idle()
        except Exception:
            logger.exception('Ошибка в devman-fishshop-tgbot. Перезапуск через 15 секунд.')
            sleep(15)


if __name__ == '__main__':
    main()