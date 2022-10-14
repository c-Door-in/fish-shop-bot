import json
from pprint import pprint
from urllib.parse import urljoin

import requests
from environs import Env


def get_access_token():
    env = Env()
    env.read_env()

    client_id = env.str('ELASTICPATH_CLIENT_ID')
    client_secret = env.str('ELASTICPATH_CLIENT_SECRET')
    auth_api_url = 'https://api.moltin.com/oauth/access_token/'

    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }

    response = requests.post(auth_api_url, data=payload)
    return response.json()['access_token']


def get_products():
    access_token = get_access_token()
    url = 'https://api.moltin.com/pcm/products/'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    return response.json()


def get_pricebooks():
    access_token = get_access_token()
    url = 'https://api.moltin.com/pcm/pricebooks/'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    return response.json()


def get_book_prices(book_id):
    access_token = get_access_token()
    url = f'https://api.moltin.com/pcm/pricebooks/{book_id}/prices'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    return response.json()


def get_product(prod_id):
    access_token = get_access_token()
    url = f'https://api.moltin.com/pcm/products/{prod_id}'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    return response.json()['data']


def get_inventories():
    access_token = get_access_token()
    url = 'https://api.moltin.com/v2/inventories/'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    return response.json()['data']


def get_inventory(prod_id):
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/inventories/{prod_id}'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    return response.json()['data']


def get_cart(cart_id):
    access_token = get_access_token()
    url = urljoin('https://api.moltin.com/v2/carts/', cart_id)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(url, headers=headers)
    return response.json()['data']


def get_cart_items(cart_id):
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(url, headers=headers)
    return response.json()


def add_product(prod_id, cart_id, quantity=1):
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'data': {
            'id': prod_id,
            'type': 'cart_item',
            'quantity': quantity,
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def get_currencies():
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/currencies/'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(url, headers=headers)
    return response.json()


def display_price(price_currencies):
    # TODO includes_tax
    prices = []
    currencies = get_currencies()
    pprint(currencies)
    for price_currency_code, price_value in price_currencies.items():
        for currency in currencies['data']:
            if currency['code'] == price_currency_code:
                amount = str(price_value['amount'])
                decimal = currency['decimal_places']
                decimal_point = currency['decimal_point']
                price = f'{amount[:-decimal]}{decimal_point}{amount[-decimal:]}'
                prices.append(currency['format'].format(price=price))
    return prices


def get_all_prices():
    prices = {}
    pricebooks = get_pricebooks()
    for pricebook in pricebooks['data']:
        book_prices = get_book_prices(pricebook['id'])
        for product_price_unit in book_prices['data']:
            product_sku = product_price_unit['attributes']['sku']
            product_prices = display_price(product_price_unit['attributes']['currencies'])
            prices[product_sku] = product_prices
    return prices


def get_available_amount(prod_id, inventories):
    for inventory in inventories:
        if inventory['id'] == prod_id:
            return inventory['available']
    return None


def get_file_link(file_id):
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/files/{file_id}'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    return response.json()['data']['link']['href']


def get_products_info():
    products = get_products()
    all_prices = get_all_prices()
    inventories = get_inventories()
    products_summury = {}
    for product in products['data']:
        id = product['id']
        sku = product['attributes']['sku']
        name = product['attributes']['name']
        description = product['attributes']['description']
        main_image_link = get_file_link(product['relationships']['main_image']['data']['id'])
        prices = all_prices[sku]
        in_stock = str(get_available_amount(id, inventories))

        products_summury[id] = {
            'sku': sku,
            'name': name,
            'description': description,
            'main_image_link': main_image_link,
            'prices': prices,
            'in_stock': in_stock,
        }
    return products_summury


def main():
    products_summury = get_products_info()
    pprint(products_summury)

    # cart = get_cart('123')
    # pprint(cart)

    # adding_prod_id = products[0]['id']
    # adding_status = add_product(adding_prod_id, cart['id'])
    # print(adding_status)

    # cart_items = get_cart_items(cart['id'])
    # pprint(cart_items)
    

if __name__ == "__main__":
    main()