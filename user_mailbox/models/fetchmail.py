# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
"""Fetchmail Model."""

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60


class FetchmailServer(models.Model):
    """Add User and Default reference in Fetchmail Server ."""

    _inherit = 'fetchmail.server'

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
        return super(FetchmailServer, self).create(vals)

    @api.multi
    def write(self, vals):
        """Raise validation while more than one default fetchmail server."""
        if vals.get('default') and \
            self.search([('user_id', '=', self.user_id.id),
                         ('default', '=', vals.get('default'))]):
            raise UserError(_('You can only select one default account.'))
        return super(FetchmailServer, self).write(vals)

    @api.multi
    def fetch_mail(self):
        """Overridden fetch_mail method.

        WARNING: meant for cron usage only - will commit() after
        each email!.
        """
        additionnal_context = {
            'fetchmail_cron_running': True
        }
        mailthread = self.env['mail.thread']
        for server in self:
            _logger.info('start checking for new emails \
                on %s server %s', server.type, server.name)
            additionnal_context['fetchmail_server_id'] = server.id
            additionnal_context['server_type'] = server.type
            count, failed = 0, 0
            imap_server = None
            pop_server = None
            if server.type == 'imap':
                try:
                    imap_server = server.connect()
                    imap_server.select()
                    if server.date:
                        result, data = imap_server.search(
                            None, 'SINCE',
                            '%s' %
                            server.date.strftime('%d-%b-%Y'))
                    else:
                        # result, data = imap_server.search(None, '(ALL)')
                        result, data = imap_server.search(None, '(UNSEEN)')
                    # result, data = imap_server.search(None, '(UNSEEN)')
                    for num in data[0].split():
                        result, data = imap_server.fetch(num, '(RFC822)')
                        imap_server.store(num, '-FLAGS', '\\Seen')
                        try:
                            mailthread.with_context(
                                **additionnal_context).message_process(
                                server.object_id.model,
                                data[0][1],
                                save_original=server.original,
                                strip_attachments=(not server.attach))
                        except Exception:
                            _logger.info(
                                'Failed to process mail from %s server %s.',
                                server.type, server.name, exc_info=True)
                            failed += 1
                        imap_server.store(num, '+FLAGS', '\\Seen')
                        self._cr.commit()
                        count += 1
                    _logger.info("Fetched %d email(s) on %s \
                        server %s; %d succeeded, %d failed.",
                                 count, server.type, server.name,
                                 (count - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch \
                        mail from %s server %s.",
                                 server.type, server.name, exc_info=True)
                finally:
                    if imap_server:
                        imap_server.close()
                        imap_server.logout()
            elif server.type == 'pop':
                try:
                    while True:
                        pop_server = server.connect()
                        (num_messages, total_size) = pop_server.stat()
                        pop_server.list()
                        for num in range(1, min(MAX_POP_MESSAGES,
                                                num_messages) + 1):
                            (header, messages, octets) = pop_server.retr(num)
                            message = (b'\n').join(messages)
                            try:
                                mailthread.with_context(
                                    **additionnal_context).message_process(
                                    server.object_id.model, message,
                                    save_original=server.original,
                                    strip_attachments=(not server.attach))
                                pop_server.dele(num)
                            except Exception:
                                _logger.info(
                                    'Failed to process mail from %s \
                                    server %s.', server.type, server.name,
                                    exc_info=True)
                                failed += 1
                            self.env.cr.commit()
                        if num_messages < MAX_POP_MESSAGES:
                            break
                        pop_server.quit()
                        _logger.info("Fetched %d email(s) on %s \
                            server %s; %d succeeded, %d failed.",
                                     num_messages, server.type, server.name,
                                     (num_messages - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to \
                        fetch mail from %s server %s.",
                                 server.type, server.name, exc_info=True)
                finally:
                    if pop_server:
                        pop_server.quit()
            server.write({'date': fields.Datetime.now()})
        return True
