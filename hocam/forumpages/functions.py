# functions module includes
# functions that are used in this project
import pytz


def localizetime(utctime):
    # function for turning utc to localtime (for display reasons)
    utctime = utctime.replace(tzinfo=pytz.UTC)
    localtime = utctime.astimezone(pytz.timezone("ASIA/ISTANBUL"))
    localtime = localtime.strftime("%d/%b/%y %X ")
    return localtime
