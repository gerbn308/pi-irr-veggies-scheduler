import datetime, json, requests, time, urllib
from datetime import datetime, timedelta

"""
You could replace this API with a direct connection to a Temperature probe.
This API connection connects to a Pi in my greenhouse that uses the sensor below.

DHT22 Sensor - https://smile.amazon.com/gp/product/B0795F19W6/
"""
#  I used a 
class Greenhouse:
    apiUrl = 'http://127.0.0.1:3001/api/'
    retryMax = 5
    retryWait = 5


    def _convertTemp(self, degF):
        return round(((float(degF) - 32) * (5/9)), 2)
    def _convertDepth(self, inches):
        return round(float(inches)* 25.4, 2)


    def getWeather(self, retry=0):
        data = {
            
            'greenhouse': {}
        }

        try:
            response = requests.get(self.apiUrl+"weather", params={}, timeout=5)

            raw = json.loads(response.text)

            if 'tempC' in raw:
                data['greenhouse']['tmpC'] = float(raw['tempC'])
            else:
                raise Exception("Missing Greenhouse Temperature")
            if 'humidity' in raw:
                data['greenhouse']['humidity'] = int(raw['humidity'])
        except Exception as err:
            if retry < self.retryMax:
                retry += 1
                time.sleep(self.retryWait)
                data = self.getWeather(retry=retry)
            else:
                print(err)
                return None

        return data
