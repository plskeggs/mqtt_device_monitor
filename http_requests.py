'''HTTP Requests and Error Messages'''

import requests

def http_req(token, req_url, req_api_key):
    '''List or create account device certificates'''
    http_req_flag = ''
    auth_hdr = {'Authorization': 'Bearer ' + req_api_key}
    resp_json = ""
    try:
        if token == 'POST': #create new acc dev/certs
            resp = requests.post(req_url, headers=auth_hdr)
        elif token == 'GET':    #fetch info
            resp = requests.get(req_url, headers=auth_hdr)
        resp_json = resp.json()
        if resp.status_code >= 300:
            if "message" in resp_json:
                http_req_flag = f"Error: {resp_json['message']}, status_code:{resp.status_code}, code:{resp_json['code']}"
            else:
                http_req_flag = f"Error: status_code:{resp.status_code}, json:{resp_json}"
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

    return resp_json, http_req_flag
