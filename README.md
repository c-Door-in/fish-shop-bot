# Бот магазина, сделанного на Elasticpath.com
 Бот выводит список товаров, формирует корзину и собирает контактные данные для последующей оплаты. 
 
 Здесь можно посмотреть [пример бота в Telegram](https://t.me/yoga_shop_bot)  
  
  <img src="https://github.com/c-Door-in/fish-shop-bot/blob/3ca81646757d104a59ef6054b293f90aa63c3552/yoga_shop_bot.gif?raw=true" width="300" />
  
 
 ## Установка
 У вас уже должен быть установлен Python3.  
 Подключите зависимости:
 ```
 pip install -r requirements.txt
 ```
 ### Создайте бота у [Bot Father](https://t.me/BotFather)

 *Внимание! Бот работает с уже созданным магазином на [https://www.elasticpath.com/](https://https://www.elasticpath.com/)*  
 Для работы бота потребуются ключи для доступа по API.  
 Также должны быть оформлены и опубликованы товары посредством `PRODUCT EXPERIENCE MANAGER`.
 
 ### Установка переменных среды
 Создайте в корне файл .env  
 Запишите в него следующие переменные:
 ```
 TGBOT_TOKEN=<Токен вашего телеграм бота>

 ELASTICPATH_CLIENT_ID=<Одноименный ключ из elasticpath>

 ELASTICPATH_CLIENT_SECRET=<Одноименный ключ из elasticpath>
 ```
 
 ## Запуск
 Для запуска используйте команду:
 ```
 python tg_bot.py
 ```
 Все метода API доступа собраны в модуле `moltin_api.py`
 
 ## Цели проекта
 Проект создан в учебных целях на портале [Devman](https://dvmn.org/).
 
