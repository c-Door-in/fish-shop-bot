from enum import Enum, auto
from textwrap import dedent
from time import sleep
from pprint import pprint

from environs import Env
from redis import Redis
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

from moltin_api import get_products_info, add_product_to_cart, get_cart_summary, remove_cart_item

import logging

logger = logging.getLogger(__name__)

class States(Enum):
    HANDLE_MENU = auto()
    HANDLE_DESCRIPTION = auto()
    HANDLE_CART = auto()


def start(update, context):
    chat_id = update.effective_chat.id

    if update.callback_query:
        message_id = update.callback_query.message.message_id
    else:
        message_id = update.message.message_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    thinking = context.bot.send_message(chat_id=chat_id, text='Думаю...')
    
    products = get_products_info()
    context.chat_data['products'] = products
    keyboard = []
    for product_id, product in products.items():
        keyboard.append(
            [InlineKeyboardButton(product['name'],
                                  callback_data=product_id)]
        )
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='Корзина')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.delete_message(chat_id=chat_id, message_id=thinking.message_id)
    context.bot.send_message(
        chat_id=chat_id,
        text='Привет!',
        reply_markup=reply_markup,
    )

    return States.HANDLE_MENU


def main_menu(update, context):
    chat_id = update.effective_chat.id
    if update.callback_query:
        message_id = update.callback_query.message.message_id
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    products = context.chat_data['products']
    keyboard = []
    for product_id, product in products.items():
        keyboard.append(
            [InlineKeyboardButton(product['name'],
                                  callback_data=product_id)]
        )
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='Корзина')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=chat_id,
        text='Выбирай мудро!',
        reply_markup=reply_markup,
    )

    return States.HANDLE_MENU


def handle_menu(update, context):
    chat_id = update.effective_chat.id
    query = update.callback_query
    current_product_id = query.data
    context.chat_data['current_product_id'] = current_product_id
    current_product = context.chat_data['products'][current_product_id]

    main_image_link = current_product['main_image_link']
    name = current_product['name']
    prices = '\n'.join(current_product['prices'])
    description = current_product['description']
    on_stock = current_product['on_stock']
    
    text = dedent(f'''
        {name}

        {prices}
        {on_stock} на складе

        {description}'''
    )

    message_id = update.callback_query.message.message_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)

    keyboard = [
        [
            InlineKeyboardButton('1 шт', callback_data=1),
            InlineKeyboardButton('5 шт', callback_data=5),
            InlineKeyboardButton('20 шт', callback_data=20),
        ],
        [InlineKeyboardButton('Корзина', callback_data='Корзина')],
        [InlineKeyboardButton('Назад', callback_data='Назад')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_photo(
        chat_id=chat_id,
        photo=main_image_link,
        caption=text,
        reply_markup=reply_markup,
    )

    return States.HANDLE_DESCRIPTION


def add_to_cart(update, context):
    current_product_id = context.chat_data['current_product_id']
    chat_id = update.effective_chat.id
    prod_quantity = int(update.callback_query.data)

    adding_status = add_product_to_cart(
        prod_id=current_product_id,
        cart_id=chat_id,
        quantity=prod_quantity,
    )

    return States.HANDLE_DESCRIPTION


def handle_cart(update, context):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    thinking = context.bot.send_message(chat_id=chat_id, text='Думаю...')
    cart_summary = get_cart_summary(chat_id)
    summary_for_text = []
    keyboard = []
    for item_id, product in cart_summary['cart_items'].items():
        summary_for_text.append(
            dedent(f'''
                {product['name']}
                {product['description']}
                {product['unit_price']} за шт
                {product['quantity']} шт в корзине за {product['value']}'''
            )
        )
        keyboard.append(
            [InlineKeyboardButton(f'Убрать из корзины {product["name"]}',
                                  callback_data=item_id)]
        )
    summary_for_text.append(f'\nВсего: {cart_summary["total"]}')
    text = '\n'.join(summary_for_text)

    keyboard.append(
        [InlineKeyboardButton('В меню', callback_data='В меню')],
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.delete_message(chat_id=chat_id, message_id=thinking.message_id)
    context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

    return States.HANDLE_CART


def remove_from_cart(update, context):
    chat_id = update.effective_chat.id
    item_id = update.callback_query.data
    removing_status = remove_cart_item(item_id, chat_id)

    return handle_cart(update, context)


def echo(update, context):
    chat_id = update.effective_chat.id
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
                CallbackQueryHandler(handle_cart, pattern='^Корзина$'),
                CallbackQueryHandler(handle_menu),
            ],
            States.HANDLE_DESCRIPTION: [
                CallbackQueryHandler(main_menu, pattern='^Назад$'),
                CallbackQueryHandler(handle_cart, pattern='^Корзина$'),
                CallbackQueryHandler(add_to_cart, pattern='^\d+$'),
            ],
            States.HANDLE_CART: [
                CallbackQueryHandler(main_menu, pattern='^В меню$'),
                CallbackQueryHandler(remove_from_cart),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
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