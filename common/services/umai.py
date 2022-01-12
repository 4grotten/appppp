import json

import requests
from django.conf import settings

from common.models import UmaiWallet
from common.services import slack


class Umai:
    megacom = ['0550', '0551', '0552', '0553', '0554', '0555', '0556', '0557', '0558', '0559',
               '0750', '0751', '0752', '0753', '0754', '0755', '0756', '0757', '0758', '0759',
               '0990', '0995', '0997', '0998', '0999']
    nurtelecom = ['0500', '0501', '0502', '0503', '0504', '0505', '0506', '0507', '0508', '0509',
                  '0700', '0701', '0702', '0703', '0704', '0705', '0706', '0707', '0708', '0709']
    beeline = ['0220', '0221', '0222', '0223', '0224', '0225', '0226', '0227', '0228', '0229',
               '0770', '0771', '0772', '0773', '0774', '0775', '0776', '0777', '0778', '0779',
               '0996']
    salam = ['0880']
    types = {
        "Nurtelecom": nurtelecom,
        "Beeline2": beeline,
        "MegaCom": megacom,
        "Salam": salam
    }

    login_url = 'https://umai.kg/api/auth/local'

    # umai_wallet = UmaiWallet.objects.last()
    password = '123'
    wallet = '123'
    version = '123'

    request_headers = {
        "Host": "umai.kg",
        "Origin": "https://umai.kg",
        "Referer": "https://umai.kg/login",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru-RU",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/95.0.4638.54 Safari/537.36"
    }

    def __init__(self, phone_number, wallet=None):
        self.amount = wallet.amount
        self.phone_number = phone_number.replace('+996', '0')
        self.token = self.get_token()
        self.phone_type = self.get_numbers_type()
        self.payment_id = None

    def get_token(self):
        try:
            login_payload = {
                "password": f"{self.password}",
                "phone": f"{self.wallet}",
                "frontend": {
                    "device": "",
                    "version": f"{self.version}",
                }
            }
            payload = json.dumps(login_payload)

            request_headers = self.add_headers(content_length=len(payload))

            answer = requests.post(url=self.login_url, data=payload, headers=request_headers)
            # print('============ Login status ===============')
            # print(answer.status_code)
            answer = json.loads(answer.content)
            token = answer['token']
            self.request_headers['Authorization'] = f"Bearer {token}"
            return token
        except Exception:
            pass

    def get_numbers_type(self):
        try:
            # print('====== get type =====')
            # print(self.phone_number)
            for key, value in self.types.items():
                if self.phone_number[:4] in value:
                    # print('====== TYPE =======', key)
                    return key
                if self.phone_number[:6] == '031258':  # Прямой Билайн
                    return "Beeline2"
        except Exception:
            pass

    def create_payment(self):
        try:
            create_payment_url = 'https://umai.kg/api/v2/payments'
            create_payment_data = {
                "destination": {
                    "type": f"{self.phone_type}",
                    "id": f"{self.phone_number}"
                }
            }

            payload = json.dumps(create_payment_data)

            request_headers = self.add_headers(content_length=len(payload))
            request_headers['Referer'] = f"https://umai.kg/payment-flow/{self.phone_type}"

            answer = requests.post(url=create_payment_url, data=payload, headers=request_headers)

            answer = json.loads(answer.content)
            # print(answer)
            self.payment_id = answer['_id']
            # print('============ Create payment ==============')
            # print(self.payment_id)
            return answer
        except Exception:
            pass

    def filling_out_payment(self):
        try:
            all_payment_data = self.create_payment()

            filling_out_payment_url = f'https://umai.kg/api/v2/payments/{self.payment_id}'

            all_payment_data['amount'] = self.amount
            payload = json.dumps(all_payment_data)

            content_length = len(payload)

            request_headers = self.add_headers(content_length=content_length)
            request_headers['Referer'] = filling_out_payment_url

            answer = requests.put(url=filling_out_payment_url, data=payload, headers=request_headers)

            answer = json.loads(answer.content)
            # print('=============== Filling out payment ==============')
            # print(answer)
            return answer
        except Exception:
            pass

    def commit_payment(self):
        try:
            commit_data = self.filling_out_payment()

            commit_transactions_url = f'https://umai.kg/api/v2/payments/{self.payment_id}/commit'

            commit_data['fee'] = 0
            commit_data['monthlyLimit'] = 60000
            payload = json.dumps(commit_data)
            # print('============ Commit payment ===============')
            # print(payload)
            content_length = len(payload)

            request_headers = self.add_headers(content_length=content_length)
            request_headers['Referer'] = f"https://umai.kg/payment-flow/{self.phone_type}/{self.payment_id}/confirm"

            answer = requests.post(url=commit_transactions_url, data=payload, headers=request_headers)
            if answer.status_code == 202:
                slack.bot(f'{self.phone_number}'
                          f'\n {self.amount} сом.'
                          f'\n status_code-{answer.status_code}')
                slack.bot(f'\nНа вашем балансе осталось - {self.get_balance()} сом'
                          f'\n==============================')
            # print(answer.status_code)
            # print(answer)
        except Exception:
            pass

    def add_headers(self, content_length):
        request_headers = self.request_headers
        request_headers['Content-Length'] = f"{content_length}"
        return request_headers

    def get_balance(self):
        users_me_url = 'https://umai.kg/api/v2/users/me'
        resp = requests.get(url=users_me_url, headers={'Authorization': f'Bearer {self.token}'})
        balance = json.loads(resp.content)
        return balance["balance"]
