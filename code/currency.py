import requests

API_URL = "https://v6.exchangerate-api.com/v6"
API_KEY = "6b3e6f09c28d0a24ba44ac29"

def get_supported_currencies():
    """
    Fetches all the supported currencies from ExchangeRate-API.

    :return: A list of supported currency codes or None if the API call fails.
    """
    try:
        response = requests.get(f"{API_URL}/{API_KEY}/codes")
        if response.status_code == 200:
            data = response.json()
            if data['result'] == 'success':
                return [code[0] for code in data['supported_codes']]
            else:
                print("API error: ", data.get('error-type', 'Unknown error'))
        else:
            print(f"HTTP error: Status code {response.status_code}")
    except Exception as e:
        print(f"Error fetching supported currencies: {e}")
    return None

def get_conversion_rate(base_currency, target_currency):
    """
    Fetches the conversion rate from base_currency to target_currency.

    :param base_currency: The currency code you want to convert from (e.g., 'USD')
    :param target_currency: The currency code you want to convert to (e.g., 'EUR')
    :return: The conversion rate or None if the API call fails
    """
    try:
        response = requests.get(f"{API_URL}/{API_KEY}/latest/{base_currency}")
        if response.status_code == 200:
            data = response.json()
            if data['result'] == 'success':
                return data['conversion_rates'].get(target_currency)
            else:
                print("API error: ", data.get('error-type', 'Unknown error'))
        else:
            print(f"HTTP error: Status code {response.status_code}")
    except Exception as e:
        print(f"Error fetching conversion rate: {e}")
    return None
