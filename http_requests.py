'''HTTP Requests and Error Messages'''

import requests

def http_req(token, req_url, req_api_key, http_req_flag):
    '''List or create account device certificates'''
    auth_hdr = {'Authorization': 'Bearer ' + req_api_key}

    try:
        if token == 'POST': #create new acc dev/certs
            resp = requests.post(req_url, headers=auth_hdr)
        elif token == 'GET':    #fetch info
            resp = requests.get(req_url, headers=auth_hdr)
        return resp.json()
    except requests.RequestException:
        return http_req_flag == 'requestException'
    except requests.ConnectionError:
        return http_req_flag == 'connectionError'
    except requests.HTTPError:
        return http_req_flag == 'HTTPError'
    except requests.TooManyRedirects:
        return http_req_flag == 'manyRedirects'
    except requests.ConnectTimeout:
        return http_req_flag == 'connectTimeout'
    except requests.ReadTimeout:
        return http_req_flag == 'readTimeout'
    except requests.Timeout:
        return http_req_flag == 'timeout'

    return None
