import requests
import json
import sys
import boto3
from boto3.dynamodb.conditions import Key, Attr

# event
# "text": GoogleHomeにしゃべらせるメッセージ (MUST)

## Client種別
CLIENT_LINE = "line"
CLIENT_STD = "standard_input"
CLIENT_WEBHOOK = "webhook"


def getNgrokHost():
    """[最新のngrokアドレスを取得する]
    
    Returns:
        [str]] -- [ngrok_url]
    """    
    print('getNgrokHost: --start')
    db = boto3.resource('dynamodb',verify=False)
    t = db.Table('MY_HOST')
    res = t.query(
        KeyConditionExpression=Key('NAME').eq('ngrok'),
        ScanIndexForward= False,
        Limit= 1
    )
    ngrok_url = res['Items'][0]['HOST']
    print('getNgrokHost: ngrok_url=', ngrok_url)
    print('getNgrokHost: --end')
    return ngrok_url


def main_handler(event, context):

    print('main_handler: --start')
    homeurl = getNgrokHost()
    apipath = '/makeNotify'

    print('event=', json.loads(event['body']))

    message = "no_input"
    client = "none"

    if event == None:
        message = 'eventデータなし。'
        client = CLIENT_STD
        print('event is None. use Deafault message', message)    

    else:
        print('event has message, decoding received event')
        print('event[body]', json.loads(event['body']))

        body = json.loads(event['body'])

        if 'text' in body:
            # Webhookからtextのみのbodyを受け取った場合
            message = json.loads(event['body'])['text']

        elif 'queryResult' in body:
            # LINEからのメッセージの場合
            queryResult = body['queryResult']
            if 'fulfillmentMessages' in queryResult:
                # print(queryResult)
                fulfillmentMessages = queryResult['fulfillmentMessages']
                if 'platform' in fulfillmentMessages[0]:
                    # print(fulfillmentMessages)
                    platform = fulfillmentMessages[0]['platform']
                    if platform == 'LINE':
                        print('platform=', platform)
                        message = queryResult['queryText']
                        client = CLIENT_LINE

    print('POST notify message to ' + homeurl + apipath)
    print('message=', message)

    # GoogleHomeへメッセージ送信
    res = sendMessageToGoogleHome(message, homeurl, apipath)

    # クライアントへのレスポンス
    res_body = makeResMessage(res, client)


    return {
        'statusCode': res.status_code,
        'body': res_body
    }

def sendMessageToGoogleHome(message, url, apipath):

    postevent = json.dumps({
        'text': message,
    })

    res = requests.post(
        url+apipath,
        postevent,
        headers={'Content-Type': 'application/json'},
        verify = False
        )

    print("POST request result: ", res.status_code)

    return res


def makeResMessage(res, client):

    if client == CLIENT_WEBHOOK or client == CLIENT_STD:
        s = str('Message send to ngrok(google home)')
        body = json.dumps({s})

    elif client == CLIENT_LINE:
        body = json.dumps({
                "fulfillment_text": "show text from aws lambda",
                "fulfillment_messages": [
                    {
                        "text": {
                            "text": [
                                "res"
                            ]
                        }
                    },
                    {
                        "platform": "LINE"
                    }
                ]
            })

    return body


if __name__ == '__main__':
    print('** start __main__ **')
    args = sys.argv
    # print('len of args',len(args))
    # print('args[0]',args[0])

    if len(args) > 1:
        #第一引数: しゃべらせたいメッセージ
        print('args have message', args[1])
        message = {
            'body':{
                'text': args[1]
                }
        }
        event = message
    else:
        print('no args inputed. -> use default message')
        event = None

    host = getNgrokHost()
    print('get ngrokhost=', host)

    print('Call main_handler')
    main_handler(event, None)
