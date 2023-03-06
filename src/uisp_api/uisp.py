'''UISP Rest API handler.
'''

import logging
import requests
import urllib.parse


logger = logging.getLogger(__name__)


class APIException(Exception):
    '''UISP API Exception'''
    pass


class UispApi:
    '''Main UISP API class.
    '''

    def __init__(self, uisp_server, app_key, crm_version='v1.0',
                 nms_version='v2.1', secure=True) -> None:
        '''Constructor
        '''
        super().__init__()

        self._secure = secure
        self._server = uisp_server
        self._api_version_crm = crm_version
        self._api_version_nms = nms_version
        self._app_key = app_key

    def _build_url_crm(self, sub_path) -> str:
        '''Build the request URL for the CRM side of the API.
        '''
        if self._secure:
            protocol = 'https'
        else:
            protocol = 'http'

        return "{0}://{1}/crm/api/{2}/{3}".format(
            protocol,
            self._server,
            self._api_version_crm,
            sub_path,
        )

    def _call_api_crm(self, call_method, api_call, parameters=None,
                      return_type='json'):
        '''Perform a call to the CRM side of the API.
        '''

        logger.debug(f"Entered _call_api crm '{api_call}' => {parameters}")

        if call_method not in ['delete', 'get', 'patch', 'post']:
            raise APIException(f"Unknown call method: {call_method}")

        api_url = self._build_url_crm(api_call)

        headers = {
            'Content-Type': 'application/json',
            'X-Auth-App-Key': self._app_key,
        }

        if call_method == 'get':
            result = requests.get(api_url, headers=headers, params=parameters)
            logging.debug("raw return: {0}".format(result.text))
            if return_type == 'json':
                return result.json()
        else:
            raise APIException("Unimplemented call method: {call_method}")

    def _build_url_nms(self, sub_path) -> str:
        '''Build the request URL for the NMS side of the API.

        '''
        if self._secure:
            protocol = 'https'
        else:
            protocol = 'http'

        url = "{0}://{1}/nms/api/{2}/{3}".format(
            protocol,
            self._server,
            self._api_version_nms,
            sub_path,
        )

        # Check for and remove any duplicate '/'

        return url

    def _call_api_nms(self, call_method, api_call, parameters=None,
                      return_type='json'):
        '''Perform a call to the NMS side of the API.
        '''

        api_url = self._build_url_nms(api_call)

        logger.debug("_call_api_nms base URL: {0}".format(api_url))
        headers = {
            'accept': 'application/json',
            'x-auth-token': self._app_key,
        }

        req = requests.get(
            api_url,
            headers=headers,
            params=parameters,
        )

        if req.status_code == 200:
            if return_type == 'json':
                return req.json()
            return req.raw
        else:
            raise RuntimeError("Got error '{r.status_code}' while executing "
                               "request")

    def version_get(self, ) -> str:

        result = self._call_api_crm('get', 'version')

        return result['version']

    def device_list(self, **kwargs):
        '''

        # Fetch Device by name
        # Fetch device by mac

        # Fetch all devices with a particular role
        APs = uispH.device_list(role='ap')
        '''

        params = {}
        for key, value in kwargs.items():
            params[key] = value

        logger.debug("Get device list search params: {0}".format(params))

        result = self._call_api_nms(
            'get',
            'devices',
            parameters=params,
        )

        return result

    def get_device_by_mac(self, mac: str):
        '''Get device by MAC address.

        '''

        result = self._call_api_nms(
            'get',
            f'devices/mac/{urllib.parse.quote_plus(mac)}',
        )

        return result

    def get_device_creds(self, device_id: str):
        '''

        e.g.
        dev_creds = uispH.get_device_creds('<device uuid>')
        print(dev_creds)

        output:
        {'credentials': {'username': 'ubnt', 'password': 'ubnt',
         'createdAt': '2021-02-01T08:01:41.353Z'},
         'isPassphraseMissing': False}
        '''

        result = self._call_api_nms(
            'get',
            f'vault/{device_id}/credentials'
        )

        return result

    def get_gateways(self,):
        '''Get UISP Gateways.

        curl -X GET "https://wisp.stech.com.au/nms/api/v2.1/gateways"
             -H  "accept: application/json"
             -H  "x-auth-token: <api key>"
        '''

        result = self._call_api_nms(
            'get',
            'gateways'
        )

        return result


if __name__ == '__main__':
    logging.BASIC_FORMAT = ('%(asctime)s - %(name)s - %(thread)d - '
        '%(levelname)s - %(message)s')
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)
    logging.basicConfig(level=logging.DEBUG, format=logging.BASIC_FORMAT)
    logging.info("Start")

    with open('key.txt', 'r') as f:
        UISP_KEY = f.read().strip()

    with open('host.txt', 'r') as f:
        UISP_SERVER = f.read().strip()

    uispH = UispApi(UISP_SERVER, UISP_KEY)

    server_version = uispH.version_get()

    logging.debug("Server version: {0}".format(server_version))

    devices = uispH.device_list()

    count = 0
    for curr_device in devices:
        count += 1

    logging.info("Device count: {0}".format(count))

    logging.info("Done")
