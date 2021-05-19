import argparse

from vax.cmd._config import get_config
from vax.cmd import main_get_data, main_process_data, main_generate_dataset
from vax.cmd.export import main_export
from vax.cmd.check_with_r import test_check_with_r
from vax.utils.paths import Paths


def main():
    config = get_config()
    paths = Paths(config.project_dir)
    creds = config.CredentialsConfig()

    if config.display:
        print(config)
    
    print(config.mode)

    if "get" in config.mode:
        cfg = config.GetDataConfig()
        main_get_data(
            paths=paths,
            parallel=cfg.parallel,
            n_jobs=cfg.njobs,
            modules_name=cfg.countries,
            greece_api_token=creds.greece_api_token,
            skip_countries=cfg.skip_countries,
        )
    if "process" in config.mode:
        cfg = config.ProcessDataConfig()
        main_process_data(
            paths=paths,
            google_credentials=creds.google_credentials,
            google_spreadsheet_vax_id=creds.google_spreadsheet_vax_id,
            skip_complete=cfg.skip_complete,
            skip_monotonic=cfg.skip_monotonic_check,
            skip_anomaly=cfg.skip_anomaly_check,
        )
    if "generate" in config.mode:
        if config.check_r:
            test_check_with_r(paths=paths)
        else:
            main_generate_dataset(
                paths=paths,
            )
    if "export" in config.mode:
        main_export(
            paths=paths,
            url=creds.owid_cloud_table_post
        )


if __name__ == "__main__":
    main()
