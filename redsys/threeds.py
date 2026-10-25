"""Builders for the Ds_Merchant_EMV3DS object used in 3-D Secure v2 (REST direct connection).

Flow: inicia (`card_data`) -> authorize (`authentication_data`) -> [challenge] ->
finalize (`challenge_response`). See docs/direct-connection.md. The
EMV3DS sub-field names are case-sensitive and passed through verbatim.

Each function returns the dict to assign to a request's `emv3ds` field, e.g.

    from redsys import threeds

    response = client.inicia(..., emv3ds=threeds.card_data()).send()
"""


def card_data() -> dict:
    """EMV3DS payload for the iniciaPeticionREST call (step 1)."""
    return {'threeDSInfo': 'CardData'}


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
    """Cardholder browser data the merchant page collects for the authorization."""
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
    *, three_ds_server_trans_id, notification_url, protocol_version, browser, three_ds_comp_ind='Y'
) -> dict:
    """EMV3DS payload for the authorization call (step 3). `browser` is `browser_info(...)`."""
    data = {
        'threeDSInfo': 'AuthenticationData',
        'protocolVersion': protocol_version,
        'threeDSServerTransID': three_ds_server_trans_id,
        'notificationURL': notification_url,
        'threeDSCompInd': three_ds_comp_ind,
    }
    data.update(browser)
    return data


def challenge_response(*, cres, protocol_version) -> dict:
    """EMV3DS payload to finalize the authorization after the challenge (step 5)."""
    return {'threeDSInfo': 'ChallengeResponse', 'protocolVersion': protocol_version, 'cres': cres}
