'''
Check for all three certificates or create an account device along 
with its certificates.
'''

import http_requests
import argparse
from os import makedirs, path

devCert_URL = 'https://api.nrfcloud.com/v1/account/certificates'


def parse_args():
    parser = argparse.ArgumentParser(description="Device Credentials Installer",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--path", type=str,
                        help="Path to save files.  Selects -s", default="./")
    return parser.parse_args()

args = parse_args()

def write_file(pathname, filename, string):
    '''save string to file'''
    if not path.isdir(pathname):
        try:
            makedirs(pathname, exist_ok=True)
        except OSError as e:
            raise RuntimeError("Error creating file path", e)
    full_path = path.join(pathname, filename)
    try:
        f = open(full_path, "w")
    except OSError:
        raise RuntimeError("Error opening file: " + full_path)
    f.write(string)
    print("File created: " + path.abspath(f.name))
    f.close()
    return

def create_device(account_type, api_key, client_cert, priv_key, http_req_flag):
    http_req_flag = ''
    create_dev_cert = http_requests.http_req('POST', devCert_URL, api_key, http_req_flag)  #create uses 'POST'
    
    if http_req_flag != '':   #there was an error, send error type back to main
        return http_req_flag 
        

    print(create_dev_cert)
    keyOnly = create_dev_cert['privateKey']
    caOnly = create_dev_cert['caCert']
    clientOnly = create_dev_cert['clientCert']
    '''Create pem files and save the certificates generated above'''
    write_file(args.path, account_type + '_privateKey.pem', keyOnly)    #save privateKey as pem file
    write_file(args.path, 'caCert.pem', caOnly)     #save caCert as pem file
    write_file(args.path, account_type + '_clientCert.pem', clientOnly)  #save clientCert as pem file

    client_cert = './' + account_type + '_clientCert.pem'
    priv_key = './' + account_type + '_privateKey.pem'

    return client_cert, priv_key 
