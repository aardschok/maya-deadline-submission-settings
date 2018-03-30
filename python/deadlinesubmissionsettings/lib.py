"""Library function for the Deadline Submission Setting application

Dependencies:
    - Avalon
"""

import logging

import os

from avalon import io, api, pipeline
from avalon.vendor import requests


log = logging.getLogger("DSS - Lib")


def get_work_directory():
    """Get the work directory to Fusion through the template"""

    session = api.Session.copy()
    project = io.find_one({"type": "project",
                           "name": api.Session["AVALON_PROJECT"]})
    assert project, "This is a bug"
    template = project["config"]["template"]["work"]

    session["AVALON_TASK"] = "comp"
    session["AVALON_APP"] = "fusion"
    work_directory = pipeline._format_work_template(template, session)

    if not os.path.isdir(work_directory):
        print("Fusion app folder does not exist:\n%s" % work_directory)
        work_directory = pipeline._format_work_template(template, api.Session)

    return work_directory


def query(argument):
    """Lazy wrapper for request.get"""

    response = requests.get(argument)
    if not response.ok:
        log.error("Non-script command is not available:'{}'".format(query))
        log.error("Details: {}".format(response.text))
        result = []
    else:
        result = response.json()

    return result


def get_machine_list(debug=None):
    """Fetch the machine list (slaves) from Deadline"""
    AVALON_DEADLINE = debug or api.Session["AVALON_DEADLINE"]
    argument = "{}/api/slaves?NamesOnly=true".format(AVALON_DEADLINE)
    return query(argument=argument)


def get_pool_list(debug=None):
    """Get all pools from Deadline"""
    AVALON_DEADLINE = debug or api.Session["AVALON_DEADLINE"]
    argument = "{}/api/pools?NamesOnly=true".format(AVALON_DEADLINE)
    return query(argument)


def get_group_list(debug=None):
    """Get all groups from Deadline"""
    AVALON_DEADLINE = debug or api.Session["AVALON_DEADLINE"]
    argument = "{}/api/groups?NamesOnly=true".format(AVALON_DEADLINE)
    return query(argument)


def get_machine_state():
    pass
