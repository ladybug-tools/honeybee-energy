import pytest

@pytest.fixture
def userdatadict():
    udd = {"str_key":"str_val",
                    "float_key": 0.01,
                    "t_key":True,
                    "f_key":False,
                    "list_key":[1,0.1,"test",True,False]
                    }
    return(udd)