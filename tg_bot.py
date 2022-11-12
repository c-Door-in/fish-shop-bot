from enum import Enum, auto
from textwrap import dedent
from time import sleep
from pprint import pprint

from environs import Env
from redis import Redis
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

from moltin_api import get_products_info, add_product_to_cart, get_cart_summary, remove_cart_item, get_or_create_customer

import logging

logger = logging.getLogger(__name__)

class States(Enum):
    HANDLE_MENU = auto()
    HANDLE_DESCRIPTION = auto()
    HANDLE_CART = auto()
    WAITING_EMAIL = auto()


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
        [InlineKeyboardButton('Оплатить', callback_data='Оплатить')],
    )
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


def waiting_email(update, context):
    chat_id = update.effective_chat.id

    message_id = update.callback_query.message.message_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    
    keyboard = [[InlineKeyboardButton('В меню', callback_data='В меню')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    last_message = context.bot.send_message(
        chat_id=chat_id,
        text='Введите почту',
        reply_markup=reply_markup,
    )
    context.chat_data['last_message_id'] = last_message.message_id

    return States.WAITING_EMAIL


def confirm_email(update, context):
    chat_id = update.effective_chat.id
    typed_email = update.message.text

    last_message_id = context.chat_data.get('last_message_id')
    if last_message_id:
        context.bot.delete_message(chat_id=chat_id, message_id=last_message_id)

    message_id = update.message.message_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)

    thinking = context.bot.send_message(chat_id=chat_id, text='Думаю...')

    user = update.message.from_user
    customer_id = get_or_create_customer(user['first_name'], typed_email)
    logger.debug(customer_id)

    text = f'Вы прислали мне эту почту: {typed_email}\nС вами свяжутся.'

    keyboard = [[InlineKeyboardButton('В меню', callback_data='В меню')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.delete_message(chat_id=chat_id, message_id=thinking.message_id)
    update.message.reply_text(text=text, reply_markup=reply_markup)

    return States.HANDLE_CART


def fail_email(update, context):
    chat_id = update.effective_chat.id

    last_message_id = context.chat_data.get('last_message_id')
    if last_message_id:
        context.bot.delete_message(chat_id=chat_id, message_id=last_message_id)

    message_id = update.message.message_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)

    text = f'Проверьте правильность написания.'

    keyboard = [[InlineKeyboardButton('В меню', callback_data='В меню')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    last_message = update.message.reply_text(text=text, reply_markup=reply_markup)
    context.chat_data['last_message_id'] = last_message.message_id

    return States.WAITING_EMAIL


def cancel(update, context):
    ConversationHandler.END


def error(update, error):
    """Log Errors caused by Updates."""
    logger.warning(f'Update "{update}" caused error "{error}"')


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
    env = Env()
    env.read_env()

    while True:
        try:
            updater = Updater(token=env.str('TG_BOT_TOKEN'))
            dp = updater.dispatcher
            dp.add_handler(ConversationHandler(
                entry_points=[CommandHandler('start', start)],
                states={
                    States.HANDLE_MENU: [
                        CallbackQueryHandler(handle_cart, pattern='^Корзина$'),
                        CallbackQueryHandler(handle_menu),
                    ],
                    States.HANDLE_DESCRIPTION: [
                        CallbackQueryHandler(main_menu, pattern='^Назад$'),
                        CallbackQueryHandler(handle_cart, pattern='^Корзина$'),
                        CallbackQueryHandler(add_to_cart, pattern=r'^\d+$'),
                    ],
                    States.HANDLE_CART: [
                        CallbackQueryHandler(waiting_email, pattern='^Оплатить$'),
                        CallbackQueryHandler(main_menu, pattern='^В меню$'),
                        CallbackQueryHandler(remove_from_cart),
                    ],
                    States.WAITING_EMAIL: [
                        CallbackQueryHandler(main_menu, pattern='^В меню$'),
                        MessageHandler(Filters.regex(r'^\w+@[a-z]+\.[a-z]+$'), confirm_email),
                        MessageHandler(Filters.text, fail_email),
                    ],
                },
                fallbacks=[CommandHandler('cancel', cancel)],
                allow_reentry=True,
            ))
            dp.add_error_handler(error)
            updater.start_polling()
            updater.idle()
        except Exception:
            logger.exception('Ошибка в devman-fishshop-tgbot. Перезапуск через 15 секунд.')
            sleep(15)


if __name__ == '__main__':
    main()