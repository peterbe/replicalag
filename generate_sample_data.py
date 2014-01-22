import random
import datetime

names = ['DB1', 'DB2', 'DB3']

M = 100
now = datetime.datetime.now()
for i in range(M):
    moment = now - datetime.timedelta(seconds=(M - i)*60)

    for name in names:
        if name =='DB3':
            bytes = random.randint(180, 500 - i)
        else:
            bytes = random.randint(170 + i * 10, 300 + i * 12)
        print (
          "INSERT INTO lag_log (name, moment, lag) values "
          "('%s', '%s', %s);"
          % (name, moment, bytes)
        )
