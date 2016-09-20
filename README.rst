=========================
Welcome to python-redsys!
=========================

A simple, clean and less dependant client for handle payments through RedSys platform (previously known as Sermepa)
using the two types of conexion defined by the platform: *direct conexion* (or webservice) and *redirect conexion*.

The aim of this package is to provide a normalized interface between RedSys and other applications.

Although RedSys platform's *redirect conexion* depends on a webserver to resolve the communication step,
the `RedirectClient` provided in this package does not assumes any kind of procedure to resolve this
communication step; it merely prepares the necessary parameters for making a request and handle the
response parameters.

Example using *redirect conexion*
=================================

1. Create the client
--------------------
.. code-block:: python

    from decimal import Decimal as D, ROUND_HALF_UP
    from redsys import currencies, languages, parameters, transactions
    from redsys.client import RedirectClient

    secret_key = u'123456789abcdef'
    sandbox = False
    client = RedirectClient(secret_key, sandbox)


2. Create a request
-------------------
.. code-block:: python

    request = client.create_request()

3. Pass the necessary parameters to the request
-----------------------------------------------
.. code-block:: python

    request.merchant_code = u'100000001'
    request.terminal = u'1'
    request.transaction_type = transactions.STANDARD_PAYMENT
    request.currency = currencies.EUR
    request.order = u'000000001'
    # The amount must be defined as decimal and pre-formated with only two decimals
    request.amount = D('10.56489').quantize(D('.01'), ROUND_HALF_UP)
    request.merchant_data = 'merchant data for tracking purpose'
    request.merchant_name = "Example Commerce"
    request.titular = "Example Ltd."
    request.product_description = "Products of Example Commerce"
    request.merchant_url = "https://example.com/redsys/response"

4. Prepare de request
---------------------
Returns a dict using the provided request, that can be directly used as post parameters.

.. code-block:: python

    args = client.prepare_request(request)

5. Create a response and check the response
-------------------------------------------
The `create_response()` throws an `ValueError` in case that the `signature` does not corresponding
with the provided `merchant_paramenters`. This normally means that the response *is not comming from RedSys*.

.. code-block:: python

    signature = "YqFenHc2HpB273l8c995...."
    merchant_parameters = "AndvIh66VZdkC5TG3nYL5j4XfCnFFbo3VkOu9TAeTs58fxddgc..."
    signature_version = "HMAC_SHA256_V1"
    response = client.create_response(signature, merchant_parameters, signature_version)
    if response.is_paid():
        # Make the corresponding actions after a successful payment
    else:
        # Make the corresponding actions after a failed payment
        raise Exception(response.response, response.message)
