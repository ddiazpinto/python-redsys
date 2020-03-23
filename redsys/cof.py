# -*- coding: utf-8 -*-

"""  Installments """
INSTALLMENTS = 'I'

""" Recurring """
RECURRING = 'R'

""" Reauthorization """
REAUTHORIZATION = 'H'

""" Resubmission """
RESUBMISSION = 'E'

""" Delayed """
DELAYED = 'D'

""" Incremental """
INCREMENTAL = 'M'

""" No Show """
NO_SHOW = 'N'

""" Others """
OTHERS = 'C'

COF_TYPES = [
    INSTALLMENTS,
    RECURRING,
    REAUTHORIZATION,
    RESUBMISSION,
    DELAYED,
    INCREMENTAL,
    NO_SHOW,
    OTHERS
]

""" First COF yes """
SI = 'S'

""" First COF no """
NO = 'N'

""" First Boolean """
COF_FIRST_BOOLEAN = [
    SI,
    NO
]
