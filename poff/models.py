from . import db

from flask import Markup
from flask.ext.wtf import Form
from wtforms.fields import HiddenField
from wtforms_alchemy import model_form_factory
import base64
import datetime
import os

# Types supported by PowerDNS, see http://doc.powerdns.com/html/types.html
_RECORD_TYPES = (
    'A',
    'AAAA',
    'AFSDB',
    'CERT',
    'CNAME',
    'DNSKEY',
    'DS',
    'HINFO',
    'KEY',
    'LOC',
    'MX',
    'NAPTR',
    'NS',
    'NSEC',
    'PTR',
    'RP',
    'RRSIG',
    'SOA',
    'SPF',
    'SSHFP',
    'SRV',
    'TXT',
)


class Domain(db.Model):
    __tablename__ = 'domains'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    master = db.Column(db.String(128))
    last_check = db.Column(db.Integer)
    type = db.Column(db.String(6), nullable=False, default='MASTER')
    notified_serial = db.Column(db.Integer)
    account = db.Column(db.String(40))


    def update_soa(self):
        """ Update the serial number of the SOA associated with this domain. """
        soa_record = Record.query.filter(Record.type=='SOA', Record.name==self.name).one()
        soa_record.update_serial()


class Record(db.Model):
    __tablename__ = 'records'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'))
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(10), info={
        'choices': [(t, t) for t in _RECORD_TYPES],
    })
    content = db.Column(db.String(65535), nullable=False)
    ttl = db.Column(db.Integer, default=3600)
    prio = db.Column(db.Integer)
    change_date = db.Column(db.Integer)
    disabled = db.Column(db.Boolean, default=False)
    domain = db.relationship('Domain', backref=db.backref('records', lazy='dynamic', cascade='all,delete'))

    @property
    def serial(self):
        """ Get the serial number of a SOA record. """
        assert self.type == 'SOA', 'tried to get serial from non-SOA record'
        parts = self.content.split()
        assert len(parts) >= 2, "SOA record didn't have serial number"
        serial_number = parts[2]
        return serial_number


    @serial.setter
    def serial(self, value):
        assert self.type == 'SOA', 'tried to set serial number of non-SOA record'
        parts = self.content.split()
        assert len(parts) >= 2, 'Malformed SOA record, no serial number set'
        # content is formatted 'hostname admin_email serial_number ..'
        parts[2] = value
        self.content = ' '.join(parts)


    def update_serial(self, date=None):
        """ Update the serial number of the SOA record, assuming the given date.

        Will set the serial number according to the YYYYMMDDss convention, where ss is a number
        incremented once per change per day, and reset every day.
        """
        assert self.type == 'SOA', 'tried to update serial number of non-SOA record'
        if not date:
            date = datetime.datetime.now().date()
        current_serial = self.serial
        serial_date = datetime.datetime.strptime(current_serial[:8], '%Y%m%d')
        change_num = int(current_serial[8:])
        if serial_date.date() == date:
            change_num += 1
        else:
            change_num = 0
        self.serial = '%s%02d' % (date.strftime('%Y%m%d'), change_num)


class DynDNSClient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('records.id'))
    key = db.Column(db.LargeBinary(64), nullable=False)
    record = db.relationship('Record', backref=db.backref('dyndns_client', uselist=False))


    def __init__(self, *args, **kwargs):
        self.key = os.urandom(30)
        super(DynDNSClient, self).__init__(*args, **kwargs)


    @property
    def b64_key(self):
        return base64.b64encode(self.key)


class _PrintableForm(model_form_factory(Form)):

    def render(self):
        fields = []
        for f in self:
            if isinstance(f, HiddenField):
                fields.append('<input type="hidden" name="%(name)s" value="%(value)s">' % {
                    'name': f.name,
                    'value': f._value(),
                })
            else:
                fields.append('%s: %s' % (f.label, f()))
        return Markup('\n'.join(fields))


class DomainForm(_PrintableForm):
    class Meta:
        model = Domain
        only = (
            'name',
        )


class RecordForm(_PrintableForm):
    class Meta:
        model = Record
        only = (
            'name',
            'type',
            'content',
            'ttl',
            'prio',
        )
