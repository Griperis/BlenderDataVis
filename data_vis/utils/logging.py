# ©copyright Zdenek Dolezal 2024-, License GPL

import logging
import logging.config
import os
import bpy
import json
import typing


def init_logging():
    config_file = os.path.join(os.path.dirname(__file__), "log_config.json")
    with open(config_file, "r") as f:
        config = json.load(f)
    logging.config.dictConfig(config)
    logger = logging.getLogger("data_vis")
    logger.debug(f"Logging initialized from {config_file}")


init_logging()


# Logging decorator based on https://github.com/polygoniq/engon/blob/master/python_deps/polib/log_helpers_bpy.py
def logged_operator(cls: typing.Type[bpy.types.Operator]):
    assert issubclass(
        cls, bpy.types.Operator
    ), "logged_operator only accepts classes inheriting bpy.types.Operator"

    logger = logging.getLogger("data_vis")

    if hasattr(cls, "execute"):
        cls._original_execute = cls.execute

        def new_execute(self, context: bpy.types.Context):
            logger.info(
                f"{cls.__name__} operator execute started with arguments {self.as_keywords()}"
            )
            try:
                ret = cls._original_execute(self, context)
                logger.info(f"{cls.__name__} operator returned {ret}")
                return ret
            except:
                logger.exception(f"Uncaught exception raised in {cls}.execute")
                # We return finished even in case an error happened, that way the user will be able
                # to undo any changes the operator has made up until the error happened
                return {'CANCELLED'}

        cls.execute = new_execute

    if hasattr(cls, "invoke"):
        cls._original_invoke = cls.invoke

        def new_invoke(self, context: bpy.types.Context, event: bpy.types.Event):
            logger.debug(f"{cls.__name__} operator invoke started")
            try:
                ret = cls._original_invoke(self, context, event)
                logger.debug(f"{cls.__name__} operator invoke finished")
                return ret
            except:
                logger.exception(f"Uncaught exception raised in {cls}.invoke")
                # We return finished even in case an error happened, that way the user will be able
                # to undo any changes the operator has made up until the error happened
                return {'FINISHED'}

        cls.invoke = new_invoke

    return cls
