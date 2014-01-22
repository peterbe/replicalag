#!/usr/bin/env python
import calendar
import datetime
import random
import os
from collections import defaultdict

from flask import Flask, request, make_response, abort, jsonify, send_file
from flask.ext.sqlalchemy import SQLAlchemy
from flask.views import MethodView
from werkzeug.routing import BaseConverter


DEBUG = os.environ.get('DEBUG', False) in ('true', '1')

SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URI',
    'sqlite:////tmp/replicalag.db'
)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)


class LagLog(db.Model):
    __tablename__ = 'lag_log'

    name = db.Column(db.String(100))
    moment = db.Column(db.DateTime(timezone=True))
    lag = db.Column(db.Integer)
    master = db.Column(db.String(100))

    __mapper_args__ = {'primary_key': (name, moment, lag, master)}


class LagLogView(MethodView):

    MAX_BYTES_WARNING = 1020
    MAX_BYTES_CRITICAL = 1100

    def get(self):
        all = defaultdict(list)
        sql = """
        select name, lag, moment, avg(lag)
        over (partition by name order by moment desc rows between 1 following and 12 following) as average
        from lag_log
        order by moment
        """
        averages = defaultdict(list)
        for r in db.engine.execute(sql):
            ts = calendar.timegm(r.moment.utctimetuple())
            all[r.name].append({'x': ts, 'y': r.lag})
            print (r.name, r.average)
            if r.average:
                averages[r.name].append({'x': ts, 'y': int(r.average)})
            else:
                averages[r.name].append({'x': ts, 'y': 0})
        replicas = []
        for name, rows in all.items():
            message = None
            last_average = averages[name][-1]['y']
            last_value = rows[-1]['y']
            print "LAST", (name, last_average)
            if last_average > self.MAX_BYTES_CRITICAL:
                message = 'CRITICAL'
            elif last_average > self.MAX_BYTES_WARNING:
                message = 'WARNING'

            replicas.append({
                'name': name,
                'rows': rows,
                'averages': averages[name],
                'message': message,
                'last_average': last_average,
                'last_value': last_value,
            })
        replicas.sort(key=lambda x: x['name'])

        from pprint import pprint
 #       pprint(replicas)
        data = {'replicas': replicas}
        return make_response(jsonify(data))

    def _get_random_data(self, name):
        M = 100
        now = datetime.datetime.now()
        for i in range(M):
            moment = now - datetime.timedelta(seconds=(M - i)*60)
            bytes = random.randint(100, 200)
            yield (
                calendar.timegm(moment.utctimetuple()),
                bytes
            )


app.add_url_rule('/api/', view_func=LagLogView.as_view('lag_log'))


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter


@app.route('/<regex("styles|scripts|views|images|font"):start>/<path:path>')
def static_stuff(start, path):
    return send_file('static/%s/%s' % (start, path))


@app.route('/', defaults={'path':''})
@app.route('/<path:path>')
def catch_all(path):
    path = path or 'index.html'
    return send_file(path)
    # return send_file('../dist/%s' % path)


if __name__ == '__main__':
    db.create_all()
    app.debug = DEBUG
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port)
