"""Usage: cli.py [POST_CODE] [ALERT_SMS_NUMBER]

Arguments:
  POST_CODE           pick-up close to this post code
  ALERT_SMS_NUMBER    number to text alert when available

Options:
  -h --help
"""
import os

import requests
from twilio.rest import Client
from docopt import docopt

ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
SMS_ENABLED = ACCOUNT_SID and AUTH_TOKEN
PART_ID = 'MQCN2LL/A'  # IPhone X Space Grey 256GB


def _get_stores_availability(post_code, part_id):
    url = (
        'https://www.apple.com/shop/retail/pickup-message?pl=true'
        '&cppart=VERIZON/US&parts.0={part_id}&location={post_code}'
    ).format(part_id=part_id, post_code=post_code)
    resp = requests.get(url)
    resp.raise_for_status()
    resp_json = resp.json()
    if 'stores' not in resp_json['body']:
        raise ValueError('Could not gather available stores')
    return resp_json['body']['stores']


def can_i_order_iphone_x(post_code, part_id=PART_ID):
    stores_info = _get_stores_availability(
        post_code=post_code, part_id=part_id
    )
    stores_with_stock = [
        store for store in stores_info
        if store['partsAvailability'][PART_ID]['storeSelectionEnabled'] is True
    ]

    if not stores_with_stock:
        return False, 'Checked {} stores near you. Not available yet'.format(
            len(stores_info)
        )
    else:
        detail = 'IPhone X now available at:\n{}'.format(
            '\n'.join(s['address']['address'] for s in stores_with_stock)
        )
        return True, detail


def sms_alert(phone_number, detail):
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    client.messages.create(
        to=phone_number,
        from_=client.incoming_phone_numbers.list()[0].phone_number,
        body=detail
    )


if __name__ == '__main__':
    arguments = docopt(__doc__)
    phone_number = arguments.get('ALERT_SMS_NUMBER')
    if not arguments.get('POST_CODE'):
        print('You must specify a post code')
    else:
        try:
            can_you, detail = can_i_order_iphone_x(
                post_code=arguments['POST_CODE']
            )
            print(detail)
        except ValueError as exc:
            print(str(exc))
        if phone_number and can_you is True and SMS_ENABLED:
            sms_alert(phone_number=phone_number, detail=detail)
