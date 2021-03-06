from __future__ import unicode_literals, absolute_import

import time

import requests
import six
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlencode

from django.utils.translation import ugettext_lazy as _

from temba.channels.views import AuthenticatedExternalClaimView
from temba.contacts.models import TEL_SCHEME
from temba.msgs.models import WIRED
from temba.utils.http import HttpEvent
from ...models import Channel, ChannelType, SendException, TEMBA_HEADERS


class HighConnectionType(ChannelType):
    """
    An High Connection channel (http://www.highconnexion.com/en/)
    """

    code = 'HX'
    category = ChannelType.Category.PHONE

    name = "High Connection"
    slug = "high_connection"

    claim_blurb = _("""If you are based in France, you can purchase a number from High Connexion
                  <a href="http://www.highconnexion.com/en/">High Connection</a> and connect it in a few simple steps.""")
    claim_view = AuthenticatedExternalClaimView

    schemes = [TEL_SCHEME]
    max_length = 1500
    attachment_support = False

    def is_available_to(self, user):
        org = user.get_org()
        return org.timezone and six.text_type(org.timezone) in ["Europe/Paris"]

    def send(self, channel, msg, text):

        payload = {
            'accountid': channel.config[Channel.CONFIG_USERNAME],
            'password': channel.config[Channel.CONFIG_PASSWORD],
            'text': text,
            'to': msg.urn_path,
            'ret_id': msg.id,
            'datacoding': 8,
            'userdata': 'textit',
            'ret_url': 'https://%s%s' % (settings.HOSTNAME, reverse('handlers.hcnx_handler', args=['status', channel.uuid])),
            'ret_mo_url': 'https://%s%s' % (settings.HOSTNAME, reverse('handlers.hcnx_handler', args=['receive', channel.uuid]))
        }

        # build our send URL
        url = 'https://highpushfastapi-v2.hcnx.eu/api' + '?' + urlencode(payload)
        log_payload = urlencode(payload)
        start = time.time()

        event = HttpEvent('GET', url, log_payload)

        try:
            response = requests.get(url, headers=TEMBA_HEADERS, timeout=30)
            event.status_code = response.status_code
            event.response_body = response.text
        except Exception as e:
            raise SendException(six.text_type(e), event=event, start=start)

        if response.status_code != 200 and response.status_code != 201 and response.status_code != 202:
            raise SendException("Got non-200 response [%d] from API" % response.status_code,
                                event=event, start=start)

        Channel.success(channel, msg, WIRED, start, event=event)
