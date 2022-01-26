import os, sys, time
import datetime
from datetime import datetime, timedelta
from pytz import timezone
import mysql.connector
import logging

DIR = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, DIR+'/../src/garage')
sys.path.insert(1, DIR+'/../src/greenhouse')
sys.path.insert(1, DIR+'/../src/irrigation')
sys.path.insert(1, DIR+'/../src/weather')

from ambientweather import AmbientWeather
from garage import Garage
from greenhouse import Greenhouse
from irrigation import Irrigation

LOCAL_RUN = False
for i, arg in enumerate(sys.argv):
    if arg in ('local', 'test'):
        LOCAL_RUN = True

if LOCAL_RUN is False:
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
else:
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)

# It would be better to do this via environment variables or other means than hard coded ¯\_(ツ)_/¯
DB_USER = 'youruser'
DB_PASS = 'yourpassword'
DB_NAME = 'yourdatabasename'

DB_HOST = 'yourhost'
DB_PORT = 30003 # Change to the right port, this was for my docker container

logging.info('Initialized')


def doIrrigation():
    mydb = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        port=DB_PORT
    )
    irr = Irrigation(dbConn=mydb)
    doApply,doAmount = irr.check()
    logging.info('Irrigate?'+str(doApply)+' '+str(doAmount)+'mm')

    if doApply is True:
        logging.info('need to apply and warm enough to do so.')
        now = datetime.now(timezone('US/Eastern'))# Do this one in local time for sanity
        currentHour = int(now.strftime("%H"))
        # UTC crossover can cause issues in the evening.
        if (currentHour >= 6 and currentHour < 8) or (currentHour >= 18 and currentHour < 20):
            irr.apply(doAmount)
        else:
            logging.info('Not the right timing.')
    irr.stop()# Just to make sure it closed last time
    del irr
    mydb.close()


def updateWeather():
    logging.info('    Connecting to database')
    mydb = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        port=DB_PORT
    )

    logging.info('    Stopping Irrigation')
    try:
        irr = Irrigation(dbConn=mydb)
        irr.stop()
    except Exception as err:
        logging.error(err)
        logging.info(data)
        exit()

    gar = Garage()
    gh = Greenhouse()
    wx = AmbientWeather(
        apiKey='your-api-key',# Input your key
        appKey = 'your-app-key',# Input your key
        deviceId = 'FE:ED:BE:EF:BE:EF'# Input your station MAC address
    )

    now = datetime.now(timezone('UTC'))
    #now = now.astimezone(timezone('US/Eastern'))
    startTime = now.strftime("%Y-%m-%d %H:%M")
    now = now - timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)
    startDate = now.strftime("%Y-%m-%d")
    startTime = now.strftime("%H:%M")
    startTimestamp = now.strftime("%Y-%m-%d %H:%M")
    logging.info(startTime)

    data = {}
    logging.info('    Getting Ambient Weather')
    try:
        tmp = wx.getWeather()
        if tmp is not None:
            data.update(tmp)
        else:
            data['outdoor'] = {'tmpC': None, 'humidity': None, 'precip': None, 'rad': None}
            data['indoor'] = {'tmpC': None, 'humidity': None, 'precip': None, 'rad': None}
    except Exception as err:
        logging.warning('Error getting Garage Weather: {}'.format(err))
        data['outdoor'] = {'tmpC': None, 'humidity': None, 'precip': None, 'rad': None}
        data['indoor'] = {'tmpC': None, 'humidity': None, 'precip': None, 'rad': None}

    logging.info('    Getting Greenhouse Weather')
    try:
        tmp = gh.getWeather()
        if tmp is not None:
            if 'humidity' not in tmp['greenhouse']:
                tmp['greenhouse']['humidity'] = None
            if 'tmpC' not in tmp['greenhouse']:
                tmp['greenhouse']['tmpC'] = None
            data.update(tmp)
        else:
            data['greenhouse'] = {'tmpC': None, 'humidity': None}
    except Exception as err:
        logging.error('Error getting Greenhouse Weather: {}'.format(err))
        data['greenhouse'] = {'tmpC': None, 'humidity': None}

    logging.info('    Getting Garage Weather')
    try:
        tmp = gar.getWeather()
        if tmp is not None:
            if 'humidity' not in tmp['garage']:
                tmp['garage']['humidity'] = None
            if 'tmpC' not in tmp['garage']:
                tmp['garage']['tmpC'] = None
            data.update(tmp)
        else:
            data['garage'] = {'tmpC': None, 'humidity': None}
    except Exception as err:
        logging.info('Error getting Garage Weather: {}'.format(err))
        data['garage'] = {'tmpC': None, 'humidity': None}

    sql = '''
    REPLACE INTO weather_data (weather_timestamp,
        outdoor_temp, outdoor_humidity, outdoor_precip, outdoor_radiation,
        greenhouse_temp, greenhouse_humidity,
        garage_temp, garage_humidity,
        house_temp, house_humidity
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    '''

    logging.info('    Inserting data')
    cur = mydb.cursor()
    try:
        cur.execute(sql, (startTimestamp,
            data['outdoor']['tmpC'], data['outdoor']['humidity'], data['outdoor']['precip'], data['outdoor']['rad'],
            data['greenhouse']['tmpC'], data['greenhouse']['humidity'],
            data['garage']['tmpC'], data['garage']['humidity'],
            data['indoor']['tmpC'], data['indoor']['humidity'],
        ))
        mydb.commit()
    except Exception as err:
        logging.error(err)
        logging.info(data)
        exit()

    cur.close()
    mydb.close()
    logging.info('    Done updating weather')

# Local testing mode to get instant results
if LOCAL_RUN is True:
    updateWeather()
    doIrrigation()
    exit()

# Yes there are better ways to handle this but it works for my needs.
logging.info('Beginning Infinite Loop')
while True:
    now = datetime.now(timezone('UTC'))
    minutes = int(now.strftime("%M"))
    if minutes == 0 or minutes == 15 or minutes == 30 or minutes == 45:
        updateWeather()
        doIrrigation()
    time.sleep(60)