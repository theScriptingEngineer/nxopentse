# Base imports
import os
import math
from typing import List
from typing import Dict

# Siemens NXOpen imports
import NXOpen


the_session: NXOpen.Session = NXOpen.Session.GetSession()
the_wp = the_session.Parts.Work


def get_user_attribute_names_wp() -> List[str]:
    """
    Get all user attributes from the current workpart

    Parameters
    ----------
    None

    Returns
    -------
    List[str]
        A list of attribute names
    """
    if the_wp is None:
        return[]
        # the case that there is no current worpart
    names: List[str] = []
    for a in the_wp.GetUserAttributes():
        try:
            names.append(a.Title)
        except:
            pass
    return names

def get_user_attribute_names(obj: NXOpen.NXObject) -> List[str]:
    """
    Get all user attribute names from a given NX object.

    Parameters
    ----------
    obj : NXOpen.NXObject
        The NX object (e.g. Part, Body, Component, etc.) to get all attributes

    Returns
    ------- 
    List[str]
        A list of all attribute names
    """

    if obj is None:
        return []
    names: List[str] = []
    try:
        for a in obj.GetUserAttributes():
            try:
                names.append(a.Title)
            except:
                pass
    except:
        pass
        # in case that the object does not support attributes

    return names

def get_attributes_dict_wp() -> Dict[str, str]:
    """
    Get all user attributes from the current Workpart as a dictionary.

    Parameters
    ----------
    None

    Returns
    -------
    Dict[str, str]
        A dictionary of attribute names and their values
    """
    attrs: Dict[str, str] = {}
    
    if the_wp is None:
        return {}
    for a in the_wp.GetUserAttributes():
        try:
            if a.TYpe == NXOpen.NXObject.AttributeType.String:
                value = a.StringValue
            else:
                value = str(a.Value)
            attrs[a.Title] = value
        except:pass
    return attrs

def get_attributes_dict(obj: NXOpen.NXObject) -> Dict[str, str]:
    """
    Get all user attributes from a given NX object as a dictionary.

    Parameters
    ----------
    obj : NXOpen.NXObject
        The NX object (e.g., Part, Body, Feature, Component, etc.)

    Returns
    -------
    Dict[str, str]
        A dictionary of attribute names and their values
    """
    attrs: Dict[str, str] = {}
    try:
        for a in obj.GetUserAttributes():
            try:
                if a.Type == NXOpen.NXObject.AttributeType.String:
                    value = a.StringValue
                else:
                    value = str(a.Value)
                attrs[a.Title] = value
            except:
                pass
    except:
        pass
        # in case that the object does not support attributes
    return attrs

