import logging

import maya.cmds as cmds
from avalon.maya import lib

log = logging.getLogger("DSS Maya Lib")


def lock_attr(attribute):
    cmds.setAttr(attribute, lock=True)


def unlock_attr(attribute):
    cmds.setAttr(attribute, lock=False)


def validate_render_instance(instance):
    """Validate if the attributes are correct"""

    data = lib.read(instance)

    assert data["id"] == "avalon.renderglobals", ("Node '%s' is not a "
                                                  "renderglobal node"
                                                  % instance)
    assert data["family"] == "colorbleed.renderglobals", ("Family is not"
                                                          "renderglobals")

    machine_list_attr = "{}.machineList".format(instance)
    locked_list = cmds.getAttr(machine_list_attr, lock=True)
    if not locked_list:
        lock_attr(machine_list_attr)


def find_render_instance():
    """Find the current render settings instance

    Returns:
        str
    """

    instance = "renderglobalsDefault"
    if not cmds.objExists(instance):
        log.error("No node found callen '{}'".format(instance))
        return

    instances = cmds.ls("*:{}".format(instance))
    if len(instances) > 1:
        raise RuntimeError("Found multiple rendergloablDefault instances, "
                           "there can only be one")

    # Ensure attributes are
    validate_render_instance(instance)

    return instance


def apply_settings(instance, settings):
    """Set the attributes of the instance based on the UI settings

    Args:
        instance(str): name of the renderglobalsDefault instance
        settings(dict): values from the

    """
    if "whitelist" in settings:
        cmds.setAttr("%s.whitelist" % instance, True)
        settings.pop("whitelist", None)

    for attr_name, value in settings.items():

        attr = "%s.%s" % (instance, attr_name)

        # Check if attr is locked
        lock = cmds.getAttr(attr, lock=True)
        if lock:
            unlock_attr(attr)

        args = {}
        if isinstance(value, basestring):
            args = {"type": "string"}

        cmds.setAttr(attr, value, **args)

        # Re lock attr
        if lock:
            lock_attr(attr)

    log.info("Applied settings ..")


def read_settings(instance):
    """Read the render globals instance settings

    Args:
        instance(str): name of the node

    Returns:
        dict
    """

    suspend_attr = "{}.suspendPublishJob".format(instance)
    include_def_layer = "{}.includeDefaultRenderLayer".format(instance)
    run_slapcomp_attr = "{}.runSlapComp".format(instance)
    priority_attr = "{}.priority".format(instance)
    whitelist_attr = "{}.whitelist".format(instance)
    machinelist_attr = "{}.machineList".format(instance)
    flow_file_attr = "{}.flowFile".format(instance)

    settings = {
        "suspendPublishJob": cmds.getAttr(suspend_attr),
        "runSlapComp": cmds.getAttr(run_slapcomp_attr),
        "priority": cmds.getAttr(priority_attr),
        "includeDefaultRenderLayer": cmds.getAttr(include_def_layer),
        "flowFile": cmds.getAttr(flow_file_attr),
        "machineList": cmds.getAttr(machinelist_attr)
    }

    if cmds.getAttr(whitelist_attr):
        settings["whiteList"] = ""

    return settings

