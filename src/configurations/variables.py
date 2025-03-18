from infrastracture.env_vars_manager.env_vars_manager import EnvVarsManager, EnvVarsParams
from configurations.variables_model import Variables


def get_variables(logger):
    params = EnvVarsParams(
        Variables,
        logger
    )

    env_vars = EnvVarsManager[Variables](params)

    return env_vars.get_env_vars()
