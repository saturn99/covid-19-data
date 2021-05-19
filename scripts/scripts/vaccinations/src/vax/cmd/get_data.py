import importlib

from joblib import Parallel, delayed

from vax.batch import __all__ as batch_countries
from vax.incremental import __all__ as incremental_countries
from vax.cmd.utils import get_logger, print_eoe


# Logger
logger = get_logger()

# Import modules
country_to_module_batch = {c: f"vax.batch.{c}" for c in batch_countries}
country_to_module_incremental = {c: f"vax.incremental.{c}" for c in incremental_countries}
country_to_module = {
    **country_to_module_batch,
    **country_to_module_incremental,
}
modules_name_batch = list(country_to_module_batch.values())
modules_name_incremental = list(country_to_module_incremental.values())
modules_name = modules_name_batch + modules_name_incremental


def _get_data_country(module_name: str, paths: str, greece_api_token: str, skip_countries: list):
    country = module_name.split(".")[-1]
    if country.lower() in skip_countries:
        logger.info(f"{module_name}: skipped! ⚠️")
        return {
            "module_name": module_name,
            "success": None,
            "skipped": True
        }
    logger.info(f"{module_name}: started")
    module = importlib.import_module(module_name)
    try:
        if "greece" in module_name:
            module.main(paths, greece_api_token)
        else:
            module.main(paths)
    except Exception as err:
        success = False
        logger.error(f"{module_name}: ❌ {err}", exc_info=True)
    else:
        success = True
        logger.info(f"{module_name}: SUCCESS ✅")
    return {
        "module_name": module_name,
        "success": success,
        "skipped": False
    }


def main_get_data(paths, parallel: bool = False, n_jobs: int = -2, modules_name: list = modules_name,
                  greece_api_token: str = None, skip_countries: list = []):
    """Get data from sources and export to output folder.

    Is equivalent to script `run_python_scripts.py`
    """
    print("-- Getting data... --")
    skip_countries = [x.lower() for x in skip_countries]
    if parallel:
        modules_execution_results = Parallel(n_jobs=n_jobs, backend="threading")(
            delayed(_get_data_country)(
                module_name,
                paths,
                greece_api_token,
                skip_countries,
            ) for module_name in modules_name
        )
    else:
        modules_execution_results = []
        for module_name in modules_name:
            modules_execution_results.append(_get_data_country(
                module_name,
                paths,
                greece_api_token,
                skip_countries,
            ))

    modules_failed = [m["module_name"] for m in modules_execution_results if m["success"] is False]
    # Retry failed modules
    logger.info(f"\n---\n\nRETRIALS ({len(modules_failed)})")
    modules_execution_results = []
    for module_name in modules_failed:
        modules_execution_results.append(
            _get_data_country(module_name, paths, greece_api_token, skip_countries)
        )
    modules_failed_retrial = [m["module_name"] for m in modules_execution_results if m["success"] is False]
    if len(modules_failed_retrial) > 0:
        failed_str = "\n".join([f"* {m}" for m in modules_failed_retrial])
        print(f"\n---\n\nThe following scripts failed to run ({len(modules_failed_retrial)}):\n{failed_str}")
    print_eoe()
