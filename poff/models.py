from . import db, base62

from flask import Markup
from flask_wtf import Form
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

_TSIG_ALGORITHMS = (
    'hmac-sha256',
    'hmac-md5',
    'hmac-sha1',
    'hmac-sha224',
    'hmac-sha384',
    'hmac-sha512',
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

    @property
    def records(self):
        """ Sort records such that subdomains are grouped together. """
        return sorted(self._records, key=lambda r: '.'.join(reversed(r.name.split('.'))))


    def update_soa(self):
        """ Update the serial number of the SOA associated with this domain. """
        soa_record = Record.query.filter(Record.type=='SOA', Record.name==self.name).one()
        soa_record.update_serial()


    @property
    def tsigkeys(self):
        keys = TsigKey.query.join(DomainMeta, TsigKey.name == DomainMeta.content)\
            .filter(DomainMeta.kind=='TSIG-ALLOW-DNSUPDATE')\
            .filter(DomainMeta.domain_id==self.id)\
            .all()
        return keys


class DomainMeta(db.Model):
    __tablename__ = 'domainmetadata'
    id = db.Column(db.Integer, primary_key=True)
    domain = db.relationship('Domain', backref=db.backref('_metadata', lazy='dynamic', cascade='delete'))
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'))
    kind = db.Column(db.String(16))
    content = db.Column(db.Text())


class TsigKey(db.Model):
    __tablename__ = 'tsigkeys'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    algorithm = db.Column(db.String(50), info={
        'choices': [(t, t) for t in _TSIG_ALGORITHMS],
    }, default='hmac-sha256')
    secret = db.Column(db.String(255))

    def __init__(self, **kwargs):
        if not 'secret' in kwargs:
            kwargs['secret'] = base64.b64encode(os.urandom(16))

        super(TsigKey, self).__init__(**kwargs)


class Record(db.Model):
    __tablename__ = 'records'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'))
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(10), info={
        'choices': [(t, t) for t in _RECORD_TYPES],
    })
    content = db.Column(db.String(65535))
    ttl = db.Column(db.Integer, default=3600)
    prio = db.Column(db.Integer)
    change_date = db.Column(db.Integer)
    disabled = db.Column(db.Boolean, default=False)
    domain = db.relationship('Domain', backref=db.backref('_records', lazy='dynamic', cascade='all,delete'))

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
        self.set_new_key()
        super(DynDNSClient, self).__init__(*args, **kwargs)


    def set_new_key(self):
        self.key = os.urandom(30)


    @property
    def printable_key(self):
        return base62.encode(self.key)


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


class TsigKeyForm(_PrintableForm):
    class Meta:
        model = TsigKey
        only = (
            'name',
            'algorithm',
        )
