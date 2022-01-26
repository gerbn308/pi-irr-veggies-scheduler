CREATE TABLE weather_data (
    weather_timestamp   DATETIME,
    outdoor_temp        DECIMAL(5,2),
    outdoor_humidity    TINYINT,
    outdoor_precip      DECIMAL(5,2),
    outdoor_radiation   SMALLINT,
    greenhouse_temp     DECIMAL(5,2),
    greenhouse_humidity TINYINT,
    greenhouse_precip   DECIMAL(5,2) DEFAULT 0.00,
    garage_temp         DECIMAL(5,2),
    garage_humidity     TINYINT,
    house_temp          DECIMAL(5,2),
    house_humidity      TINYINT,
    PRIMARY KEY (weather_timestamp)
);

CREATE TABLE irrigation_data (
    irrigation_date             DATETIME,
    irrigation_daily_amount     DECIMAL(5,2) DEFAULT 0.00,
    irrigation_daily_need       DECIMAL(5,2),
    irrigation_weekly_amount    DECIMAL(5,2) DEFAULT 0.00,
    irrigation_weekly_need      DECIMAL(5,2),
    PRIMARY KEY (irrigation_date)
);
