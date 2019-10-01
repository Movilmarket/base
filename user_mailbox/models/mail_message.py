# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
"""mail Message Model."""


from odoo import models, api


class Message(models.Model):
    """Overwrite create method in Mail Message."""

    _inherit = 'mail.message'

    @api.model
    def create(self, values):
        """Overwrite create method for add reference of partner."""
        message = super(Message, self).create(values)
        fetchmail_ser_id = \
            self.env.context.get('fetchmail_server_id', False)
        if fetchmail_ser_id:
            fetchmail_server = \
                self.env["fetchmail.server"].browse(fetchmail_ser_id)
            if fetchmail_server.user_id and \
                    fetchmail_server.user_id.partner_id:
                curr_user = self.env['res.users'].browse(self._uid)
                if values.get("author_id", False):
                    partner = values['author_id']
                else:
                    partner = curr_user.partner_id.id or False
                if message and partner:
                    message.partner_ids = [(4, partner)]
                    message.needaction_partner_ids = [(4, partner)]
                    message.author_id = partner
        return message
