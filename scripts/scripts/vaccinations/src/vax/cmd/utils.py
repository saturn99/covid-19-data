import logging


def get_logger():
    # Logging config
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger()
    return logger


def normalize_country_name(country_name: str):
    return country_name.strip().replace(" ", "_").lower()


def print_eoe():
    print("----------------------------\n----------------------------\n----------------------------\n")