Usage:
------

.. code-block:: python
    from decimal import Decimal as D, ROUND_HALF_UP
    from redsys import currencies, languages, parameters, transactions
    from redsys.client import RedirectClient

    secret_key = u'123456789abcdef'
    sandbox = False
    client = RedirectClient(secret_key, sandbox)

    ## Request step
    # Create a Request object with client default parameters and the provided
    request = client.create_request()
    request.merchant_code = u'000000001'
    request.terminal = u'1'
    request.transaction_type = transactions.STANDARD_PAYMENT
    request.order = u'1234'
    request.currency = currencies.EUR
    # The amount must be decimal and pre-formated with two decimals
    request.amount = D('10.56489').quantize(D('.01'), ROUND_HALF_UP)
    args = client.prepare_request(request)

    # Returning args can be used as a post variables

    ## Response step
    from Redsys import DeferredClient
    # Check if the response is valid and well signed throwing an exception in other case
    response = client.create_response(signature, parameters)
    if response.is_paid():
        # Make the actions after payment
    else:
        raise Exception(response.get_code(), response.get_message())
