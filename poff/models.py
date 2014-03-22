from . import db

import base64
from flask import Markup
from flask.ext.wtf import Form
import os
from wtforms.fields import HiddenField
from wtforms_alchemy import model_form_factory


class Domain(db.Model):
    __tablename__ = 'domains'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    master = db.Column(db.String(128))
    last_check = db.Column(db.Integer)
    type = db.Column(db.String(6), nullable=False, default='MASTER')
    notified_serial = db.Column(db.Integer)
    account = db.Column(db.String(40))


class Record(db.Model):
    __tablename__ = 'records'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'))
    name = db.Column(db.String(255))
    type = db.Column(db.String(10))
    content = db.Column(db.String(65535))
    ttl = db.Column(db.Integer, default=3600)
    prio = db.Column(db.Integer)
    change_date = db.Column(db.Integer)
    disabled = db.Column(db.Boolean, default=False)
    domain = db.relationship('Domain', backref=db.backref('records', lazy='dynamic', cascade='all,delete'))


class DynDNSClient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('records.id'))
    key = db.Column(db.LargeBinary(64), nullable=False)
    record = db.relationship('Record', backref=db.backref('dyndns_client', uselist=False))

    def __init__(self, *args, **kwargs):
        self.key = os.urandom(64)
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
                fields.append('%s: %s<br>' % (f.label, f()))
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
        )
