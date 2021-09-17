import pytest
"""To Be Continued Need to Add fixture"""


udd = {"str_key":"str_val",
                    "float_key": 0.01,
                    "t_key":True,
                    "f_key":False,
                    "list_key":[1,0.1,"test",True,False]
                    }


@pytest.fixture
def userdatadict():
    
    return(udd)

"""
userdatadict = {"str_key":"str_val",
                    "float_key": 0.01,
                    "t_key":True,
                    "f_key":False,
                    "list_key":[1,0.1,"test",True,False]
                    }


def apply_ud(obj):
    obj.user_data = userdatadict
    return(obj)
"""