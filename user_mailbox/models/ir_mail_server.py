# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
"""Ir Mail Server Related Models."""

import logging
import smtplib
import threading
from odoo.exceptions import UserError
from odoo.tools import ustr, pycompat
from odoo import models, fields, api, tools, _

_logger = logging.getLogger(__name__)
_test_logger = logging.getLogger('odoo.tests')

SMTP_TIMEOUT = 60


class IrMailServer(models.Model):
    """Add User and Default reference in Mail Server ."""

    _inherit = "ir.mail_server"

    user_id = fields.Many2one("res.users", "User",
                              default=lambda self: self.env.uid)
    default = fields.Boolean()

    @api.model
    def create(self, vals):
        """Raise validation while more than one default fetchmail server."""
        if vals.get('default') and \
            self.search([('user_id', '=', vals.get('user_id')),
                         ('default', '=', vals.get('default'))]):
            raise UserError(_('You can only select one default account.'))
        return super(IrMailServer, self).create(vals)

    @api.multi
    def write(self, vals):
        """Raise validation while more than one default fetchmail server."""
        if vals.get('default') and \
            self.search([('user_id', '=', self.user_id.id),
                         ('default', '=', vals.get('default'))]):
            raise UserError(_('You can only select one default account.'))
        return super(IrMailServer, self).write(vals)

    def connect(self, host=None, port=None, user=None,
                password=None, encryption=None,
                smtp_debug=False, mail_server_id=None):
        """Overridden Connect Method.

        Returns a new SMTP connection to the given SMTP server.
        When running in test mode, this method does nothing and
        returns `None`.

        :param host: host or IP of SMTP server to connect to,
        if mail_server_id not passed
        :param int port: SMTP port to connect to
        :param user: optional username to authenticate with
        :param password: optional password to authenticate with
        :param string encryption: optional, ``'ssl'`` | ``'starttls'``
        :param bool smtp_debug: toggle debugging of SMTP sessions (all i/o
                        will be output in logs)
        :param mail_server_id: ID of specific mail server to use
        (overrides other parameters)
        """
        # Do not actually connect while running in test mode
        if getattr(threading.currentThread(), 'testing', False):
            return None

        mail_server = smtp_encryption = None
        if mail_server_id:
            mail_server = self.sudo().browse(mail_server_id)
        elif not host:
            if self._context and self._context.get('uid', False):
                mail_server = self.search(
                    [('user_id', '=', self._context['uid']),
                     ('default', '=', True)],
                    order='sequence', limit=1)
                if not mail_server:
                    mail_server = self.sudo().search([], order='sequence',
                                                     limit=1)
            else:
                mail_server = self.sudo().search([], order='sequence', limit=1)
        if mail_server:
            smtp_server = mail_server.smtp_host
            smtp_port = mail_server.smtp_port
            smtp_user = mail_server.smtp_user
            smtp_password = mail_server.smtp_pass
            smtp_encryption = mail_server.smtp_encryption
            smtp_debug = smtp_debug or mail_server.smtp_debug
        else:
            # we were passed individual smtp parameters or nothing and there is
            # no default server
            smtp_server = host or tools.config.get('smtp_server')
            smtp_port = tools.config.get(
                'smtp_port', 25) if port is None else port
            smtp_user = user or tools.config.get('smtp_user')
            smtp_password = password or tools.config.get('smtp_password')
            smtp_encryption = encryption
            if smtp_encryption is None and tools.config.get('smtp_ssl'):
                smtp_encryption = 'starttls'  # smtp_ssl => STARTTLS as of v7

        if not smtp_server:
            raise UserError(
                (_("Missing SMTP Server") + "\n" +
                 _("Please define at least one SMTP server, "
                   "or provide the SMTP parameters explicitly.")))

        if smtp_encryption == 'ssl':
            if 'SMTP_SSL' not in smtplib.__all__:
                raise UserError(
                    _("Your Odoo Server does not support SMTP-over-SSL. "
                      "You could use STARTTLS instead. "
                      "If SSL is needed, an upgrade to Python 2.6 \
                      on the server-side "
                      "should do the trick."))
            connection = smtplib.SMTP_SSL(
                smtp_server, smtp_port, timeout=SMTP_TIMEOUT)
        else:
            connection = smtplib.SMTP(
                smtp_server, smtp_port, timeout=SMTP_TIMEOUT)
        connection.set_debuglevel(smtp_debug)
        if smtp_encryption == 'starttls':
            # starttls() will perform ehlo() if needed first
            # and will discard the previous list of services
            # after successfully performing STARTTLS command,
            # (as per RFC 3207) so for example any AUTH
            # capability that appears only on encrypted channels
            # will be correctly detected for next step
            connection.starttls()

        if smtp_user:
            # Attempt authentication - will raise if AUTH service not supported
            # The user/password must be converted to bytestrings in
            #         order to be usable for
            # certain hashing schemes, like HMAC.
            # See also bug #597143 and python issue #5285
            smtp_user = pycompat.to_native(ustr(smtp_user))
            smtp_password = pycompat.to_native(ustr(smtp_password))
            connection.login(smtp_user, smtp_password)
        return connection
