from . import db, base62
from .models import (Domain, DomainForm, DynDNSClient, Record, RecordForm, DomainMeta, TsigKey,
    TsigKeyForm)

from flask import abort, redirect, render_template, flash, request, Blueprint
from flask.views import MethodView
from logging import getLogger
from itsdangerous import constant_time_compare
import os

_logger = getLogger('poff.views')

mod = Blueprint('views', __name__)


@mod.context_processor
def default_context():
    domains = Domain.query.order_by(Domain.name).all()
    return {
        'domains': domains,
        'tsigkeyform': TsigKeyForm(),
        'domainform': DomainForm(),
        'recordform': RecordForm(),
    }


@mod.route('/')
def main():
    return render_template('domains.html')


@mod.route('/domains', methods=['POST'])
def domains():
    form = DomainForm()
    if form.validate_on_submit():
        domain = Domain()
        form.populate_obj(domain)

        soa_record = Record(content='%(domain)s hostmaster.%(domain)s 1970010100' % {
            'domain': domain.name,
            },
            domain=domain,
            type='SOA',
            name=domain.name,
        )
        soa_record.update_serial()

        spf_record = Record(content='v=spf1 -all', domain=domain, type='TXT',
            name=domain.name)

        db.session.add(domain)
        db.session.add(soa_record)
        db.session.add(spf_record)
        db.session.add(DomainMeta(domain=domain, kind='SOA-EDIT', content='INCEPTION-INCREMENT'))
        db.session.add(DomainMeta(domain=domain, kind='NSEC3NARROW', content='1'))
        nsec3params = '1 0 1 %s' % os.urandom(16).encode('hex')
        db.session.add(DomainMeta(domain=domain, kind='NSEC3PARAMS', content=nsec3params))
        _logger.info('New domain saved: %s', domain.name)
        flash('New domain added successfully!', 'success')
    else:
        flash('Failed to validate new domain, check the errors in the form below', 'error')
        _logger.debug('New domain failed form validation.')
        return render_template('domains.html', domainform=form), 400
    return redirect('/')


class MethodOverrideView(MethodView):
    """ Helper class that rewrites POST requests with a `_method` param to the given HTTP method.
    """

    allowed_methods = frozenset([
        'GET',
        'HEAD',
        'POST',
        'DELETE',
        'PUT',
        'PATCH',
        'OPTIONS'
    ])

    # Make sure POST requests always are allowed to this view
    methods = ['POST']

    def dispatch_request(self, *args, **kwargs):
        """ Find the target HTTP method and execute it. """
        meth = getattr(self, request.method.lower(), None)

        # if the request method is HEAD and we don't have a handler for it retry with GET
        if meth is None and request.method == 'HEAD':
            meth = getattr(self, 'get', None)

        # If an override is desired, load that if we have it
        method_override = request.form.get('_method', '').upper()
        if method_override in MethodOverrideView.allowed_methods and hasattr(self, method_override.lower()):
            meth = getattr(self, method_override.lower())

        assert meth is not None, 'Unimplemented method %r' % request.method
        return meth(*args, **kwargs)


class DomainView(MethodOverrideView):

    def delete(self, domain_id):
        domain = Domain.query.get_or_404(domain_id)
        db.session.delete(domain)
        _logger.info("Deleting domain %s", domain.name)
        flash('Domain %s deleted successfully' % domain.name, 'info')
        return redirect('/')


class RecordView(MethodOverrideView):

    def post(self, record_id):
        record = Record.query.get_or_404(record_id)
        form = RecordForm()
        if form.validate_on_submit():
            form.populate_obj(record)
            domain = record.domain
            domain.update_soa()
            _logger.info('Record %s modified', record.name)
            flash('Record successfully modified.', 'success')
            return redirect('/')
        else:
            _logger.info('Record modification failed form validation: %s', form.errors)
            flash('Failed to validate record modifications', 'warning')
            context = {
                'form_errors': form.errors,
                'recordform': form,
            }
            return render_template('domains.html', **context), 400


    def delete(self, record_id):
        record = Record.query.get_or_404(record_id)
        record.domain.update_soa()
        db.session.delete(record)
        _logger.info("Deleting record %s", record.name)
        flash('Record %s deleted successfully.' % record.name, 'success')
        return redirect('/')


@mod.route('/domains/<int:domain_id>/new_record', methods=['POST'])
def new_record(domain_id):
    domain = Domain.query.get_or_404(domain_id)
    form = RecordForm()
    if form.validate_on_submit():
        record = Record()
        record.domain = domain
        form.populate_obj(record)
        domain.update_soa()
        db.session.add(record)
        _logger.info('New record saved: %s', record.name)
        flash('New record saved successfully!', 'success')
    else:
        _logger.debug('Record failed form validation')
        flash('Failed to validate new record, check the errors in the form below!', 'warning')
        return render_template('domains.html', recordform=form), 400
    return redirect('/')


@mod.route('/domains/<int:domain_id>/tsigkeys', methods=['POST'])
def domain_tsigkeys(domain_id):
    domain = Domain.query.get_or_404(domain_id)
    form = TsigKeyForm()

    if not form.validate_on_submit():
        _logger.debug('TsigKey failed form validation')
        flash('Failed to validate new DynDNS key', 'warning')
        return render_template('domains.html', tsigkeyform=form), 400

    tsigkey = TsigKey()
    form.populate_obj(tsigkey)

    domain_tsigkey = DomainMeta(domain=domain, kind='TSIG-ALLOW-DNSUPDATE',
        content=tsigkey.name)

    db.session.add(tsigkey)
    db.session.add(domain_tsigkey)

    _logger.info('Added tsigkey for for "%s"', domain.name)
    flash('New dyndns key added successfully!', 'success')
    return redirect('/')


@mod.route('/records/<int:record_id>/new-dyndns-client', methods=['POST'])
def new_dyndns_client(record_id):
    record = Record.query.get_or_404(record_id)
    client = DynDNSClient(record=record)
    db.session.add(client)
    _logger.info('New DynDNS client created for record %s', record.name)
    flash('New DynDNS client created!', 'success')
    return redirect('/')


@mod.route('/records/<int:record_id>/rekey', methods=['POST'])
def rekey_dyndns_record(record_id):
    record = Record.query.get(record_id)
    if not record or not record.dyndns_client:
        abort(404)
    dyndns_client = record.dyndns_client
    dyndns_client.set_new_key()
    return redirect('/')


@mod.route('/update-record', methods=['POST'])
def update_record():
    record_name = request.form.get('record')
    record = Record.query.filter_by(name=record_name, type='A').first()
    if not record or not record.dyndns_client:
        abort(404)
    submitted_key = str(request.form.get('key', ''))
    record_key = base62.encode(record.dyndns_client.key)
    if constant_time_compare(submitted_key, record_key):
        origin_ip = request.access_route[0]
        if origin_ip.startswith('::ffff:'):
            origin_ip = origin_ip[len('::ffff:'):]
        if record.content != origin_ip:
            _logger.info('Updating record %s to %s', record.name, origin_ip)
            flash('Successfully updated record to new IP: %s' % origin_ip, 'success')
            record.content = origin_ip
            record.domain.update_soa()
            return '', 201
        else:
            flash('Still on the same IP, no change applied', 'success')
            return ''
    else:
        _logger.warning('Bad auth for trying to update record %s', record.name)
        abort(403)


class DynDNSClientView(MethodOverrideView):

    def delete(self, client_id):
        client = DynDNSClient.query.get_or_404(client_id)
        db.session.delete(client)
        _logger.info('DynDNS client for record %s deleted.', client.record.name)
        flash('DynDNS client deleted!')
        return redirect('/')


mod.add_url_rule('/domains/<int:domain_id>', view_func=DomainView.as_view('domain_details'))
mod.add_url_rule('/records/<int:record_id>', view_func=RecordView.as_view('record_details'))
mod.add_url_rule('/dyndns-clients/<int:client_id>', view_func=DynDNSClientView.as_view('client_details'))
