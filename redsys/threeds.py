"""Builders for the ``Ds_Merchant_EMV3DS`` object of 3-D Secure v2 on the direct connection.

The step numbers follow docs/direct-connection.md. The sub-field names are case-sensitive.

    client.payment(emv3ds=threeds.authentication_data(..., three_ds_comp_ind=emv3ds.METHOD_COMPLETED), ...)
"""

from base64 import urlsafe_b64encode
from json import dumps

from redsys.api import emv3ds


def card_data() -> dict:
    """``emv3ds`` of the 3-D Secure initialization, iniciaPeticionREST (step 1)."""
    return {'threeDSInfo': emv3ds.CARD_DATA}


def method_data(*, three_ds_server_trans_id, notification_url) -> str:
    """Value of the ``threeDSMethodData`` form field the browser posts to ``threeDSMethodURL`` (step 2)."""
    payload = {'threeDSServerTransID': three_ds_server_trans_id, 'threeDSMethodNotificationURL': notification_url}
    return urlsafe_b64encode(dumps(payload, separators=(',', ':')).encode('utf-8')).decode('ascii').rstrip('=')


def browser_info(
    *,
    accept_header,
    user_agent,
    language,
    color_depth,
    screen_height,
    screen_width,
    tz,
    java_enabled=False,
    javascript_enabled=True,
    ip=None,
) -> dict:
    """Cardholder browser data, collected by the merchant page, for ``authentication_data()``."""
    data = {
        'browserAcceptHeader': accept_header,
        'browserUserAgent': user_agent,
        'browserJavaEnabled': 'true' if java_enabled else 'false',
        'browserJavascriptEnabled': 'true' if javascript_enabled else 'false',
        'browserLanguage': language,
        'browserColorDepth': str(color_depth),
        'browserScreenHeight': str(screen_height),
        'browserScreenWidth': str(screen_width),
        'browserTZ': str(tz),
    }
    if ip is not None:
        data['browserIP'] = ip
    return data


def authentication_data(
    *, three_ds_server_trans_id, notification_url, protocol_version, browser, three_ds_comp_ind=emv3ds.METHOD_COMPLETED
) -> dict:
    """``emv3ds`` of the authentication (step 3); ``browser`` is ``browser_info(...)``."""
    data = {
        'threeDSInfo': emv3ds.AUTHENTICATION_DATA,
        'protocolVersion': protocol_version,
        'threeDSServerTransID': three_ds_server_trans_id,
        'notificationURL': notification_url,
        'threeDSCompInd': three_ds_comp_ind,
    }
    data.update(browser)
    return data


def challenge_response(*, cres, protocol_version) -> dict:
    """``emv3ds`` of the operation after the challenge (step 5)."""
    return {'threeDSInfo': emv3ds.CHALLENGE_RESPONSE, 'protocolVersion': protocol_version, 'cres': cres}
