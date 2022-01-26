import datetime, json, requests, urllib
from datetime import datetime

"""
Sorry that this is a mix of US Customary and Metric units, the source information was in US Customary and I prefer working with Metric.
"""
class Irrigation:
    apiIrrigationApply = 'http://127.0.0.1:3001/api/irrigation/'# Url to send irrigation request to.
    dbConn = None
    myTimezoneDB = 'America/New_York'

    def __init__(self, dbConn):
        self.dbConn = dbConn
        self.IRRIGATION_URL = 'http://127.0.0.1:3001/api/irrigation/'# Url to send irrigation request to.
        self.MIN_IRRIGATION = 12#mm
        self.MAX_IRRIGATION = 200#mm
        self.MIN_TEMPERATURE_TO_APPLY = 7#degC
        self.MAX_APP_TIME = 600#seconds
        self.BASE_WEEKLY_WATER = 25#mm
        self.BASE_TEMP = 15#degC
        self.BASE_TEMP_RANGE = 5#degC
        self.BASE_TEMP_INCREASE = 13#mm
        self.IRRIGATION_SPINUP_SECONDS = 10#Modify for your setup
        self.CUPS_PER_5MIN = 1.333#Modify for your setup, If you are using Metric you'll want to convert liters to Imperial cups
        self.BASE_TEMP_INCREASE_PER_DEGREE = self.BASE_TEMP_INCREASE / self.BASE_TEMP_RANGE / 7
        self.BASE_DAILY_WATER = self.BASE_WEEKLY_WATER / 7
        self.galPerMin = (self.CUPS_PER_5MIN/5) * 0.0625
        self.squareFeetPerHole = 0.05# Area = 12in x 6in, adjust for your setup
        self.IRRIGATION_1MM_DURATION = self.getIrrigationRate(self.galPerMin, self.squareFeetPerHole)# seconds/mm

    def _convertTemp(self, degF):
        return round(((float(degF) - 32) * (5/9)), 2)
    def _convertDepth(self, inches):
        return round(float(inches)* 25.4, 2)
    

    def apply(self, amount):
        duration = int(float(amount * self.IRRIGATION_1MM_DURATION) + self.IRRIGATION_SPINUP_SECONDS)
        if duration > self.MAX_APP_TIME:
            duration = self.MAX_APP_TIME
        print('Apply for '+str(duration)+' seconds')
        
        response = requests.get(self.apiIrrigationApply+"apply?", params={'seconds': duration}, timeout=5+self.MAX_APP_TIME)
        raw = json.loads(response.text)

        if 'applicationTimeMS' in raw:
            applied = float(raw['applicationTimeMS'])/1000 - self.IRRIGATION_SPINUP_SECONDS
            applied = applied/self.IRRIGATION_1MM_DURATION

            cur = self.dbConn.cursor(dictionary=True)
            # cur.execute('SET time_zone =%s', (self.myTimezoneDB,))
            sql = 'UPDATE irrigation_data SET irrigation_weekly_amount=irrigation_weekly_amount+%s, irrigation_daily_amount=irrigation_daily_amount+%s WHERE irrigation_date=CURRENT_DATE'
            cur.execute(sql, (applied,applied,))
            self.dbConn.commit()
            cur.close()
            print('Applied '+str(applied)+'mm')
        self.stop() # Make sure we stopped


    def getIrrigationRate(self,galPerMin,sqFtPerHole):
        # 96.25 - A constant that converts gallons per minute (GPM) to inches per hour.
        # It is derived from 60 minutes per hour divided by 7.48 gallons per cubic foot. times 12 inches per foot.
        # http://www.sprinklerwarehouse.com/DIY-Calculating-Precipitation-Rate-s/7942.htm
        inPerHour = (96.25 * galPerMin) / sqFtPerHole
        mmPerHour = 25.4 * inPerHour
        mmPerSecond = (mmPerHour / 60) / 60
        mmPerSecond = inPerHour * 0.00705556

        return 1/mmPerSecond

    def check(self):
        shouldApply = False
        applicationAmt = 0

        cur = self.dbConn.cursor(dictionary=True)
        cur2 = self.dbConn.cursor(dictionary=True)
        # cur.execute('SET time_zone =%s', (self.myTimezoneDB,))
        # cur2.execute('SET time_zone =%s', (self.myTimezoneDB,))

        # Update the daily and weekly needs
        sql = """
            SELECT DATE(weather_timestamp) AS date, MIN(outdoor_temp) as out_min, MAX(outdoor_temp) AS out_max, MAX(outdoor_precip) AS rain,
                MIN(greenhouse_temp) as gh_min, MAX(greenhouse_temp) AS gh_max
            FROM weather_data
            WHERE weather_timestamp >= CURRENT_DATE - INTERVAL 8 DAY
            GROUP BY DATE(weather_timestamp)
            ORDER BY DATE(weather_timestamp) ASC
        """
        sqlWeekly = """
            SELECT SUM(irrigation_daily_need) AS weekly_need, SUM(irrigation_daily_amount) AS weekly_applied
            FROM irrigation_data
            WHERE irrigation_date<%s AND irrigation_date>=%s - INTERVAL 6 DAY
        """
        sqlUpdateNeed = """
            INSERT INTO irrigation_data (irrigation_date, irrigation_daily_need, irrigation_weekly_need) VALUES (%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                irrigation_daily_need=%s, irrigation_weekly_need=%s
        """

        cur.execute(sql)
        results = cur.fetchall()
        for row in results:
            if row['gh_min'] is None:
                row['gh_min'] = 0
            if row['gh_max'] is None:
                row['gh_max'] = 0
            dailyNeed = self.BASE_DAILY_WATER
            avgTmp = (float(row['gh_min']) + float(row['gh_max'])) / 2# Yes min+max and not the actual daily average.
            avgTmp -= self.BASE_TEMP
            if avgTmp > 0:
                dailyNeed += avgTmp*self.BASE_TEMP_INCREASE_PER_DEGREE

            wxdate = row['date'].strftime("%Y-%m-%d %H:%M")

            cur2.execute(sqlWeekly, (wxdate,wxdate,))
            weekly = cur2.fetchone()
            weeklyNeed = 0
            if weekly['weekly_need'] is not None:
                weeklyNeed = float(weekly['weekly_need'])
            weeklyNeed += dailyNeed

            res = cur2.execute(sqlUpdateNeed, (wxdate, dailyNeed, weeklyNeed, dailyNeed, weeklyNeed))
        self.dbConn.commit()

        # Update Weekly Irrigation Total, if you want to irrigate outdoors you'd want to add rainfall to this.
        sqlWeekly = """
            SELECT SUM(irrigation_daily_amount) AS weekly_applied, MAX(irrigation_date) AS date
            FROM irrigation_data
            WHERE irrigation_date>=CURRENT_DATE - INTERVAL 6 DAY
        """
        sql = "UPDATE irrigation_data SET irrigation_weekly_amount=%s WHERE irrigation_date=%s"
        cur.execute(sqlWeekly)
        weekly = cur.fetchone()
        res = cur.execute(sql, (float(weekly['weekly_applied']), weekly['date'].strftime("%Y-%m-%d %H:%M")))
        self.dbConn.commit()

        # What about today?
        sql = "SELECT irrigation_weekly_need - irrigation_weekly_amount AS net FROM irrigation_data WHERE irrigation_date=CURRENT_DATE"
        cur.execute(sql)
        today = cur.fetchone()
        if today['net'] is not None and float(today['net']) > 0:
            applicationAmt = float(today['net'])

        # Check if water applied in the last few days.
        sql = """
            SELECT irrigation_date
            FROM irrigation_data WHERE irrigation_daily_amount>0 AND irrigation_date > CURRENT_DATE - INTERVAL 3 DAY
        """
        junk = cur.fetchall()
        junk = cur2.fetchall()
        cur.execute(sql)
        junk = cur.fetchall()
        if len(junk) == 0:
            print('    Too long since last application')
            shouldApply = True
            if applicationAmt < self.MIN_IRRIGATION:
                applicationAmt = self.MIN_IRRIGATION
        junk = cur2.fetchall()

        if applicationAmt >= self.MIN_IRRIGATION:
            shouldApply = True
            sql = 'SELECT MIN(outdoor_temp) as out_min FROM weather_data WHERE weather_timestamp>=NOW()-INTERVAL 2 hour'
            cur.execute(sql)
            today = cur.fetchone()
            if today['out_min'] < self.MIN_TEMPERATURE_TO_APPLY:
                print('    Too cold to apply '+str(today['out_min']))
                shouldApply = False

        # Check if water applied in the last 24 hours.
        sql = """
            SELECT irrigation_date
            FROM irrigation_data WHERE irrigation_daily_amount>0 AND irrigation_date >= CURRENT_DATE - INTERVAL 1 DAY
        """
        cur.execute(sql)
        junk = cur.fetchall()
        if len(junk) > 0 and shouldApply is True:
            print('    Applied in the last two days')
            shouldApply = False

        cur2.close()
        cur.close()

        # Too much water in a day is a bad thing.
        if applicationAmt > self.MAX_IRRIGATION:
            applicationAmt = self.MAX_IRRIGATION

        # If irrigating outdoors somewhere near here would be a good place to check rainfall forecasts to avoid apply water if its going to rain.

        return (shouldApply,applicationAmt)
    

    def stop(self):
        response = requests.get(self.apiIrrigationApply+"stop/bool", params={}, timeout=5+self.MAX_APP_TIME)
