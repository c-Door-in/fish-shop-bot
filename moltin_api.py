from pprint import pprint
from textwrap import dedent

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
    response.raise_for_status()
    return response.json()['access_token']


def get_products():
    access_token = get_access_token()
    url = 'https://api.moltin.com/pcm/products/'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_pricebooks():
    access_token = get_access_token()
    url = 'https://api.moltin.com/pcm/pricebooks/'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_book_prices(book_id):
    access_token = get_access_token()
    url = f'https://api.moltin.com/pcm/pricebooks/{book_id}/prices'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_product(prod_id):
    access_token = get_access_token()
    url = f'https://api.moltin.com/pcm/products/{prod_id}'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_inventories():
    access_token = get_access_token()
    url = 'https://api.moltin.com/v2/inventories/'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_inventory(prod_id):
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/inventories/{prod_id}'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_cart_summary(cart_id):
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    cart_items = response.json()

    cart_summary = {
        'cart_items': {},
        'total': cart_items['meta']['display_price']['with_tax']['formatted'],
    }
    for cart_item in cart_items['data']:
        item_id = cart_item['id']
        product_id = cart_item['product_id']
        name = cart_item['name']
        description = cart_item['description']
        unit_price = cart_item['meta']['display_price']['with_tax']['unit']['formatted']
        quantity = cart_item['quantity']
        value = cart_item['meta']['display_price']['with_tax']['value']['formatted']

        cart_summary['cart_items'][item_id] = {
            'product_id': product_id,
            'name': name,
            'description': description,
            'unit_price': unit_price,
            'quantity': quantity,
            'value': value,
        }
    return cart_summary


def add_product_to_cart(prod_id, cart_id, quantity=1):
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
    response.raise_for_status()
    return response.json()


def remove_cart_item(item_id, cart_id):
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{item_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_currencies():
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/currencies/'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def display_price(price_currencies):
    # TODO includes_tax
    prices = []
    currencies = get_currencies()
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
    response.raise_for_status()
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
        on_stock = str(get_available_amount(id, inventories))

        products_summury[id] = {
            'sku': sku,
            'name': name,
            'description': description,
            'main_image_link': main_image_link,
            'prices': prices,
            'on_stock': on_stock,
        }
    return products_summury


def get_customers():
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/customers'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_or_create_customer(name, email):
    customers = get_customers()
    for customer in customers['data']:
        if customer['email'] == email:
            return customer['id']
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/customers'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'data': {
            'type': 'customer',
            'name': name,
            'email': email,
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']['id']


def main():
    pass
    

if __name__ == "__main__":
    main()