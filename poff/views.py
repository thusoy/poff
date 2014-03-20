from . import db
from .models import Domain, DomainForm, DynDNSClient, Record, RecordForm

import base64
from flask import abort, redirect, render_template, flash, request, Blueprint
from flask.views import MethodView
from logging import getLogger
from itsdangerous import constant_time_compare

_logger = getLogger('poff.views')

mod = Blueprint('views', __name__)

@mod.route('/')
def main():
    domains = Domain.query.all()
    return render_template('base.html', **{
        'domains': domains,
        'domainform': DomainForm(),
        'recordform': RecordForm(),
    })


@mod.route('/domains', methods=['POST'])
def domains():
    form = DomainForm()
    if form.validate_on_submit():
        domain = Domain()
        form.populate_obj(domain)
        db.session.add(domain)
        _logger.info('New domain saved: %s', domain.name)
        flash('New domain added successfully!', 'success')
    else:
        flash('Failed to validate new domain, check the errors in the form below', 'error')
        _logger.debug('New domain failed form validation.')
        return render_template('base.html', domainform=form), 400
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

    methods = ['POST']

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)
        # if the request method is HEAD and we don't have a handler for it
        # retry with GET
        if meth is None and request.method == 'HEAD':
            meth = getattr(self, 'get', None)

        method_overide = request.form.get('_method', '').upper()
        if method_overide in MethodOverrideView.allowed_methods and hasattr(self, method_overide.lower()):
            return getattr(self, method_overide.lower())(*args, **kwargs)
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

    def delete(self, record_id):
        record = Record.query.get_or_404(record_id)
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
        db.session.add(record)
        _logger.info('New record saved: %s', record.name)
        flash('New record saved successfully!', 'success')
    else:
        _logger.debug('Record failed form validation')
        flash('Failed to validate new record, check the errors in the form below!', 'error')
        return render_template('base.html', recordform=form)
    return redirect('/')


@mod.route('/records/<int:record_id>/new-dyndns-client', methods=['POST'])
def new_dyndns_client(record_id):
    record = Record.query.get_or_404(record_id)
    client = DynDNSClient(record=record)
    db.session.add(client)
    _logger.info('New DynDNS client created for record %s', record.name)
    flash('New DynDNS client created!', 'success')
    return redirect('/')


@mod.route('/update-record', methods=['POST'])
def update_record():
    record_name = request.form.get('record')
    record = Record.query.filter_by(name=record_name).first()
    if not record or not record.dyndns_client:
        abort(404)
    auth_key_base64 = request.form.get('key', '')
    auth_key = base64.b64decode(auth_key_base64)
    if constant_time_compare(auth_key, record.dyndns_client.key):
        _logger.info('Updating record %s to %s', record.name, request.remote_addr)
        flash('Successfully updated record to new IP: %s' % request.remote_addr, 'success')
        record.content = request.remote_addr
        return redirect('/')
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
