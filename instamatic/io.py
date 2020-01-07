from pathlib import Path

from instamatic import config


def get_new_work_subdirectory(stem='experiment', drc=None, number=1, mkdir=True):
    """Simple function to grab new empty working directory."""
    if not drc:
        drc = config.cfg.work_directory
    else:
        drc = Path(drc)

    path = drc / f'{stem}_{number}'
    while path.exists():
        number += 1
        path = drc / f'{stem}_{number}'

    if mkdir:
        path.mkdir(exist_ok=True, parents=True)

    return path
