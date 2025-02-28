devCert_URL = 'https://api.nrfcloud.com/v1/account/certificates'
ACC_URL = 'https://api.nrfcloud.com/v1/account'
DEV_URL = 'https://api.nrfcloud.com/v1/devices'


base_url = None

def setStage(stage):
    global base_url
    if stage == 'prod':
        stage = ''
    else:
        stage = stage + "."
    base_url = f"https://api.{stage}nrfcloud.com/v1/"

def getBaseURL():
    return base_url
