import datetime, json, requests, time, urllib
from datetime import datetime, timedelta

class Garage:
    apiUrl = 'http://192.168.1.121:3001/api/'
    retryMax = 5
    retryWait = 5


    def _convertTemp(self, degF):
        return round(((float(degF) - 32) * (5/9)), 2)
    def _convertDepth(self, inches):
        return round(float(inches)* 25.4, 2)


    def getWeather(self, retry=0):
        data = {
            'garage': {}
        }

        try:
            response = requests.get(self.apiUrl+"weather", params={}, timeout=5)

            raw = json.loads(response.text)

            if 'tempC' in raw:
                data['garage']['tmpC'] = float(raw['tempC'])
            else:
                raise Exception("Missing Garage Temperature")
            if 'humidity' in raw:
                data['garage']['humidity'] = int(raw['humidity'])
        except Exception as err:
            if retry < self.retryMax:
                retry += 1
                time.sleep(self.retryWait)
                data = self.getWeather(retry=retry)
            else:
                print(err)
                return None

        return data
        
