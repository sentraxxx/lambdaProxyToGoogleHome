import requests
import json
import sys
import boto3
from boto3.dynamodb.conditions import Key, Attr

# event
# "text": GoogleHomeにしゃべらせるメッセージ (MUST)


def getNgrokHost():
    print('getNgrokHost: --start')
    db = boto3.resource('dynamodb')
    t = db.Table('MY_HOST')
    res = t.query(
        KeyConditionExpression=Key('NAME').eq('ngrok')
    )
    ngrok_url = res['Items'][0]['HOST']
    print('getNgrokHost: ngrok_url=', ngrok_url)
    print('getNgrokHost: --end')
    return ngrok_url


def main_handler(event, context):
    print('main_handler: --start')
    homeurl = getNgrokHost()
    apipath = '/makeNotify'

    print('event=', event)

    if event == None:
        message = 'eventデータなし。'
        print('event is None. use Deafault message', message)
    else:
        print('event has message, decoding received event')
        print('event[text]', event['text'])
        message = event['text']

    print('POST notify message to ' + homeurl + apipath)
    print('message', message)

    postevent = json.dumps({
        'text': message,
        'id': 1
    })

    res = requests.post(
        homeurl+apipath,
        postevent,
        headers={'Content-Type': 'application/json'})

    print("POST request result: ", res)
    print('main_handler: --end')

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


if __name__ == '__main__':
    print('** start __main__ **')
    args = sys.argv
    # print('len of args',len(args))
    # print('args[0]',args[0])

    if len(args) > 1:
        #第一引数: しゃべらせたいメッセージ
        print('args have message', args[1])
        message = {'text': args[1]}
        event = message
    else:
        print('no args inputed. -> use default message')
        event = None

    host = getNgrokHost()
    print('get ngrokhost=', host)

    print('Call main_handler')
    main_handler(event, None)
