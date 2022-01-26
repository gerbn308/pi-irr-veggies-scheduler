import datetime, json, requests, time, urllib
from datetime import datetime, timedelta

class AmbientWeather:
    apiDeviceUrl = 'https://api.ambientweather.net/v1/devices/'
    retryMax = 5
    retryWait = 5


    def __init__(self, apiKey, appKey, deviceId):
        self.apiKey = apiKey
        self.appKey = appKey
        self.deviceId = deviceId


    def _convertTemp(self, degF):
        return round(((float(degF) - 32) * (5/9)), 2)
    def _convertDepth(self, inches):
        return round(float(inches)* 25.4, 2)


    def getWeather(self, retry=0):
        parameters = {
            'apiKey': self.apiKey,
            'applicationKey': self.appKey,
            'limit': 1
        }
        data = {
            'outdoor': {},
            'indoor': {}
        }
        
        try:
            response = requests.get(self.apiDeviceUrl+urllib.parse.quote_plus(self.deviceId), params=parameters, timeout=5)

            raw = json.loads(response.text)
            raw = raw[0]
            now = datetime.now()

            if datetime.fromtimestamp(raw['dateutc']/1e3) < now-timedelta(minutes=15):
                print('Weather data older than 15 minutes')
                return None

            if 'tempf' in raw:
                data['outdoor']['tmpC'] = self._convertTemp(raw['tempf'])
            if 'humidity' in raw:
                data['outdoor']['humidity'] = int(raw['humidity'])
            if 'dailyrainin' in raw:
                data['outdoor']['precip'] = self._convertDepth(raw['dailyrainin'])
            if 'solarradiation' in raw:
                data['outdoor']['rad'] = int(raw['solarradiation'])
            if 'tempinf' in raw:
                data['indoor']['tmpC'] = self._convertTemp(raw['tempinf'])
            if 'humidityin' in raw:
                data['indoor']['humidity'] = int(raw['humidityin'])
        except Exception as err:
            if retry < self.retryMax:
                retry += 1
                time.sleep(self.retryWait)
                data = self.getWeather(retry=retry)
            else:
                print(err)
                return None

        return data
