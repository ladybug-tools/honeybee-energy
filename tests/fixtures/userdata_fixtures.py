import pytest

@pytest.fixture
def userdatadict():
    """ A fixture to keep from cluttering tests.py with This 
    'all(almost all) the types dict', and also to type less """
       
    udd = {"str_key":"str_val",
                    "float_key": 0.01,
                    "t_key":True,
                    "f_key":False,
                    "list_key":[1,0.1,"test",True,False]
                    }
    return(udd)