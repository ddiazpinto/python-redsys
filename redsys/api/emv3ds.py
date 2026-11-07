"""Values inside the ``Ds_Merchant_EMV3DS`` request object and the ``Ds_EMV3DS`` response object."""

CARD_DATA = 'CardData'
"""Request ``threeDSInfo``: the 3DS initialization asks for the card's 3DS data."""

AUTHENTICATION_DATA = 'AuthenticationData'
"""Request ``threeDSInfo``: authentication with the browser data."""

CHALLENGE_RESPONSE = 'ChallengeResponse'
"""Request ``threeDSInfo``: the step after a challenge, with ``cres``."""

RECURRING_3RI = '3RI-Recurring'
"""Request ``threeDSInfo``: 3DS requestor initiated recurring payment."""

OTA_3RI = '3RI-OTA'
"""Request ``threeDSInfo``: 3DS requestor initiated online travel agency operation."""

REQUEST_INFOS = (CARD_DATA, AUTHENTICATION_DATA, CHALLENGE_RESPONSE, RECURRING_3RI, OTA_3RI)

CARD_CONFIGURATION = 'CardConfiguration'
"""Response ``threeDSInfo``: the answer of the 3DS initialization."""

CHALLENGE_REQUEST = 'ChallengeRequest'
"""Response ``threeDSInfo``: the issuer requires a challenge (``acsURL`` and ``creq``)."""

RESPONSE_INFOS = (CARD_CONFIGURATION, CHALLENGE_REQUEST)

PROTOCOL_1_0_2 = '1.0.2'
"""``protocolVersion`` 1.0.2."""

PROTOCOL_2_1_0 = '2.1.0'
"""``protocolVersion`` 2.1.0."""

PROTOCOL_2_2_0 = '2.2.0'
"""``protocolVersion`` 2.2.0."""

NO_3DS_V2 = 'NO_3DS_V2'
"""Response ``protocolVersion``: the card has no 3-D Secure v2."""

PROTOCOL_VERSIONS = (PROTOCOL_1_0_2, PROTOCOL_2_1_0, PROTOCOL_2_2_0, NO_3DS_V2)

METHOD_COMPLETED = 'Y'
"""``threeDSCompInd``: the 3DS Method finished."""

METHOD_FAILED = 'N'
"""``threeDSCompInd``: the 3DS Method failed, timed out after 10 seconds, or the card has no method URL."""

METHOD_NOT_RUN = 'U'
"""``threeDSCompInd``: the 3DS Method did not run."""

METHOD_COMPLETION_INDICATORS = (METHOD_COMPLETED, METHOD_FAILED, METHOD_NOT_RUN)

WINDOW_250X400 = '01'
"""``challengeWindowSize``: 250 by 400 pixels."""

WINDOW_390X400 = '02'
"""``challengeWindowSize``: 390 by 400 pixels."""

WINDOW_500X600 = '03'
"""``challengeWindowSize``: 500 by 600 pixels."""

WINDOW_600X400 = '04'
"""``challengeWindowSize``: 600 by 400 pixels."""

WINDOW_FULL_SCREEN = '05'
"""``challengeWindowSize``: full screen, the default."""

CHALLENGE_WINDOW_SIZES = (WINDOW_250X400, WINDOW_390X400, WINDOW_500X600, WINDOW_600X400, WINDOW_FULL_SCREEN)

CHALLENGE_REQUESTED = '03'
"""``threeDSRequestorChallengeInd``: the merchant asks for strong customer authentication."""

CHALLENGE_MANDATED = '04'
"""``threeDSRequestorChallengeInd``: a mandate requires it, as after a ``0195`` soft decline."""

CHALLENGE_INDICATORS = (CHALLENGE_REQUESTED, CHALLENGE_MANDATED)

WHITELIST_NOT_LISTED = 'N'
"""Response ``whiteListStatus``: the merchant is not on the customer's trusted list."""

WHITELIST_NOT_ELIGIBLE = 'E'
"""Response ``whiteListStatus``: the customer has no trusted list."""

WHITELIST_PENDING = 'P'
"""Response ``whiteListStatus``: enrollment pending."""

WHITELIST_REJECTED = 'R'
"""Response ``whiteListStatus``: the customer refused."""

WHITELIST_UNKNOWN = 'U'
"""Response ``whiteListStatus``: unknown."""

WHITELIST_STATUSES = (
    WHITELIST_NOT_LISTED,
    WHITELIST_NOT_ELIGIBLE,
    WHITELIST_PENDING,
    WHITELIST_REJECTED,
    WHITELIST_UNKNOWN,
)
