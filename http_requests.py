'''HTTP Requests and Error Messages'''

import requests

def http_req(token, req_url, req_api_key):
    '''List or create account device certificates'''
    try:
        if token == 'POST': #create new acc dev/certs
            resp = requests.post(req_url, headers={'Authorization': 'Bearer ' + req_api_key})
        elif token == 'GET':    #fetch info
            resp = requests.get(req_url, headers={'Authorization': 'Bearer ' + req_api_key})
    except requests.RequestException:
        print('Request Exception')
    except requests.ConnectionError:
        print('Connection Error')
    except requests.HTTPError:
        print('HTTP Error')
    except requests.TooManyRedirects:
        print('Too many redirects')
    except requests.ConnectTimeout:
        print('Connect Timeout')
    except requests.ReadTimeout:
        print('Read Timeout')
    except requests.Timeout:
        print('Timeout')
    '''
    if token == 'POST' and resp.status_code != 201: #201 means successfully created account device + certs
        print('Error code: ' + str(resp.status_code))
    else:
        #print('Created account device.')
        pass
    if token == 'GET' and resp.status_code != 200:  #200 means successfully obtained info
        print('Error code: ' + str(resp.status_code))
    else:
        #print('Request successfully made!')
        pass
    '''
    return resp.json()
