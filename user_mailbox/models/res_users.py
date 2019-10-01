# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
"""Res Users Model."""


from odoo import models, fields


class ResUsers(models.Model):
    """Added list of incoming and outgoing mail server for user."""

    _inherit = 'res.users'

    incoming_mail_server_ids = fields.One2many("fetchmail.server", "user_id",
                                               string="Incoming Mail Servers")
    outgoing_mail_server_ids = fields.One2many("ir.mail_server", "user_id",
                                               string="Outgoing Mail Servers")
