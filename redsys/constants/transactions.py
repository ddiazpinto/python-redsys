# -*- coding: utf-8 -*-

""" Standard payment """
STANDARD_PAYMENT = "0"

""" Pre-authorization """
PREAUTHORIZATION = "1"

""" Confirmation of pre-authorization """
PREAUTHORIZATION_CONFIRMATION = "2"

""" Partial or total refund """
REFUND = "3"

""" Recurring transaction """
RECURRING_TRANSACTION = "5"

""" Successive transaction """
SUCCESSIVE_TRANSACTION = "6"

""" Authentication """
AUTHENTICATION = "7"

""" Confirmation of authentication """
AUTHENTICATION_CONFIRMATION = "8"

""" Cancellation of pre-authorization """
PREAUTHORIZATION_CANCELATION = "9"

""" Deferred pre-authorization """
DEFERRED_PREAUTHORIZATION = "O"

""" Confirmation of deferred pre-authorization """
DEFERRED_PREAUTHORIZATION_CONFIRMATION = "P"

""" Cancelation of deferred pre-authorization """
DEFERRED_PREAUTHORIZATION_CANCELATION = "Q"

""" Recurring deferred pre-authorization """
RECURRING_DEFERRED_PREAUTHORIZATION = "R"

""" Confirmation of recurring deferred pre-authorization and successive transaction """
SUCCESSIVE_RECURRING_TRANSACTION = "S"

TRANSACTION_TYPES = [
    STANDARD_PAYMENT,
    PREAUTHORIZATION,
    PREAUTHORIZATION_CONFIRMATION,
    REFUND,
    RECURRING_TRANSACTION,
    SUCCESSIVE_TRANSACTION,
    AUTHENTICATION,
    AUTHENTICATION_CONFIRMATION,
    PREAUTHORIZATION_CANCELATION,
    DEFERRED_PREAUTHORIZATION,
    DEFERRED_PREAUTHORIZATION_CONFIRMATION,
    DEFERRED_PREAUTHORIZATION_CANCELATION,
    RECURRING_DEFERRED_PREAUTHORIZATION,
    SUCCESSIVE_RECURRING_TRANSACTION,
]
