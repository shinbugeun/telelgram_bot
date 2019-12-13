from flask import Flask
from flask import request
from flask import render_template
from decouple import config
import requests
import random
app = Flask(__name__)

token = config('TELEGRAM_BOT_TOKEN')
app_url = f'https://api.telegram.org/bot{token}'

naver_client_id = config('NAVER_CLIENT_ID')
naver_client_secret = config('NAVER_CLIENT_SECRET')


@app.route(f'/{token}',methods=["POST"])
def telegram():
    from_telegram = request.get_json()

    chat_id = from_telegram.get('message').get('from').get('id')
    text = from_telegram.get('message').get('text')

    if from_telegram.get('message').get('photo') is not None:
        # 클로바 코드 요기에 작성!
        #1. 우선 파일의 아이디 값을 가져온다.
        file_id = from_telegram.get('message').get('photo')[-1].get('file_id')
        #2. 
        file_res = requests.get(f'{app_url}/getFile?file_id={file_id}')
        #3. file path
        file_path = file_res.json().get('result').get('file_path')
        #4.
        file_url = f'https://api.telegram.org/file/bot{token}/{file_path}'

        #5
        real_file_res = requests.get(file_url, stream=True)

        headers = {
            'X-Naver-Client-Id': naver_client_id,
            'X-Naver-Client-Secret':naver_client_secret
        }
        clova_res = requests.post(
            'https://openapi.naver.com/v1/vision/celebrity',
            headers=headers,
            files = {
                'image': real_file_res.raw.read()
            }
        )
        

        if clova_res.json().get('info').get('faceCount'):
            celebrity = clova_res.json().get('faces')[0].get('celebrity')
            reply = f"{celebrity.get('value')} - {celebrity.get('confidence')*100}%"
        else:
            reply = '인식된 사람이 없습니다.'

    else:
        # text가 왔을 때 실행

        if text == '/로또':
            reply = random.sample(range(1,46), 6)
        if text[0:4] == '/번역 ':
            headers = {
                'X-Naver-Client-Id':naver_client_id,
                'X-Naver-Client-Secret':naver_client_secret,
            }
            data = {
                'source': 'en',
                'target': 'ko',
                'text': text[4:]
            }
            papago_url ='https://openapi.naver.com/v1/papago/n2mt'
            papago_res = requests.post(papago_url, data=data, headers=headers) 
            papago_res = papago_res.json()
            reply = papago_res.get("message").get("result").get("translatedText")

        else:
            reply = text


    requests.get(f'{app_url}/sendMessage?chat_id={chat_id}&text={reply}')
    return '', 200

if __name__ == '__main__':
    app.run(debug=True)