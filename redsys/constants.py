# Currencies
""" Euro """
EUR = 978
""" United States dollar """
USD = 840
""" Pound sterling """
GBP = 826
""" Japanese yen """
JPY = 392
""" Argentine peso """
ARS = 32
""" Canadian dollar """
CAD = 124
""" Chilean Peso """
CLP = 152
""" Colombian peso """
COP = 170
""" Indian rupee """
INR = 356
""" Mexican peso """
MXN = 484
""" Peruvian Sol """
PEN = 604
""" Swiss franc """
CHF = 756
""" Brazilian real """
BRL = 986
""" Venezuelan bolivar """
VEF = 937
""" Turkish lira """
TRY = 949

CURRENCIES = [EUR, USD, GBP, JPY, ARS, CAD, CLP, COP, INR, MXN, PEN, CHF, BRL, VEF, TRY]

# Languages
CUSTOMER = "000"
SPANISH = "001"
ENGLISH = "002"
CATALAN = "003"
FRENCH = "004"
GERMAN = "005"
DUTCH = "006"
ITALIAN = "007"
SWEDISH = "008"
PORTUGUESE = "009"
VALENCIAN = "010"
POLISH = "011"
GALICIAN = "012"
EUSKERA = "013"

LANGUAGES = [
    CUSTOMER,
    SPANISH,
    ENGLISH,
    CATALAN,
    FRENCH,
    GERMAN,
    DUTCH,
    ITALIAN,
    SWEDISH,
    PORTUGUESE,
    VALENCIAN,
    POLISH,
    GALICIAN,
    EUSKERA,
]

# Transaction types
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

TRANSACTIONS = [
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
