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
    url = 'https://api.moltin.com/v2/products/'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    return response.json()['data']


def get_product(prod_id):
    access_token = get_access_token()
    url = f'https://api.moltin.com/v2/products/{prod_id}'
    
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
    print(response.url)
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


def main():
    products = get_products()
    product = get_product(products[0]['id'])
    pprint(product)

    # cart = get_cart('123')
    # pprint(cart)

    # adding_prod_id = products[0]['id']
    # adding_status = add_product(adding_prod_id, cart['id'])
    # print(adding_status)

    # cart_items = get_cart_items(cart['id'])
    # pprint(cart_items)
    

if __name__ == "__main__":
    main()