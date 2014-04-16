import calendar
import logging
from collections import namedtuple

from datetime import datetime, timedelta

from sqlalchemy.ext.declarative import AbstractConcreteBase

from .model_lib import base
from . import db


class Pool(base):
    """ This class stores metadata on all blocks found by the pool """
    # the hash of the block for orphan checking
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    typ = db.Column(db.String, nullable=False)
    link = db.Column(db.String)
    api_link = db.Column(db.String)

    @classmethod
    def create(cls, name, typ, link, api_link):
        pool = cls(name=name, typ=typ, link=link, api_link=api_link)
        # add and flush
        db.session.add(pool)
        db.session.flush()
        return pool


class SliceMixin(object):
    @classmethod
    def create(cls, user, value, time, worker):
        dt = cls.floor_time(time)
        slc = cls(user=user, value=value, time=dt, worker=worker)
        db.session.add(slc)
        return slc

    @classmethod
    def add_value(cls, user, value, time, worker):
        dt = cls.floor_time(time)
        slc = cls.query.with_lockmode('update').filter_by(
            user=user, time=dt, worker=worker).one()
        slc.value += value

    @classmethod
    def floor_time(cls, time):
        """ Changes an integer timestamp to the minute for which it falls in.
        Allows abstraction of create and add share logic for each time slice
        object. """
        if isinstance(time, datetime):
            time = calendar.timegm(time.utctimetuple())
        return datetime.utcfromtimestamp(
            (time // cls.slice_seconds) * cls.slice_seconds)

    @classmethod
    def compress(cls):
        """ Moves statistics that are past the `window` time into the next
        time slice size, effectively compressing the data. """
        # get the minute shares that are old enough to be compressed and
        # deleted
        recent = cls.floor_time(datetime.utcnow()) - cls.window
        # the five minute slice currently being processed
        current_slice = None
        # dictionary of lists keyed by user
        users = {}

        def create_upper():
            # add a time slice for each user in this pending period
            for key, slices in users.iteritems():
                new_val = cls.combine(*[slc.value for slc in slices])

                # put it in the database
                upper = cls.upper.query.filter_by(time=current_slice, **key._asdict()).with_lockmode('update').first()
                # wasn't in the db? create it
                if not upper:
                    dt = cls.floor_time(current_slice)
                    upper = cls.upper(time=dt, value=new_val, **key._asdict())
                    db.session.add(upper)
                else:
                    upper.value = cls.combine(upper.value, new_val)

                for slc in slices:
                    db.session.delete(slc)

        # traverse minute shares that are old enough in time order
        for slc in (cls.query.filter(cls.time < recent).
                    order_by(cls.time)):
            slice_time = cls.upper.floor_time(slc.time)

            if current_slice is None:
                current_slice = slice_time

            # we've encountered the next time slice, so commit the pending one
            if slice_time != current_slice:
                logging.debug("Processing slice " + str(current_slice))
                create_upper()
                users.clear()
                current_slice = slice_time

            # add the one min shares for this user the list of pending shares
            # to be grouped together
            key = slc.make_key()
            users.setdefault(key, [])
            users[key].append(slc)

        create_upper()


class PoolTimeSlice(AbstractConcreteBase, SliceMixin, base):
    pool = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, primary_key=True)
    value = db.Column(db.Integer)

    @classmethod
    def combine(cls, *lst):
        """ Takes an iterable and combines the values. Usually either returns
        an average or a sum. Can assume at least one item in list """
        return sum(lst) / len(lst)

    key = namedtuple('Key', ['pool'])

    def make_key(self):
        return self.key(typ=self.pool)


class OneHour(object):
    window = timedelta(days=60)
    slice = timedelta(hours=1)
    slice_seconds = slice.total_seconds()


class FifteenMinute(object):
    window = timedelta(days=1)
    slice = timedelta(minutes=15)
    slice_seconds = slice.total_seconds()


# The stats for each pool
class OneHourPool(PoolTimeSlice, OneHour):
    __tablename__ = 'one_hour_pool'
    __mapper_args__ = {
        'polymorphic_identity': 'one_hour_pool',
        'concrete': True
    }


class FifteenMinutePool(PoolTimeSlice, FifteenMinute):
    __tablename__ = 'fifteen_minute_pool'
    upper = OneHourPool
    __mapper_args__ = {
        'polymorphic_identity': 'fifteen_minute_pool',
        'concrete': True
    }
