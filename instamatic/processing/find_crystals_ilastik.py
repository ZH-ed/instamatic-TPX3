from pathlib import Path

import yaml

from instamatic.config import defaults


predicrystal_path = Path(defaults.predicrystal['location'])  # noqa
import predicrystal  # noqa


class CrystalFinder:
    """Find crystals using models trained in Ilastik using code developed here:
    https://gitlab.tudelft.nl/aj-lab/predicrystal.

    Parameters
    ----------
    nav: str
        Nav file from SerialEM containing the image metadata.
    mrc: str
        Image data in mrc format corresponding to the `.nav file`.
    """

    def __init__(self, nav: str, mrc: str):
        super().__init__()

        self.nav = Path(nav).absolute()
        self.mrc = Path(mrc).absolute()
        self.work_directory = self.nav.parent

        for fn in self.nav, self.mrc:
            if not fn.exists():
                raise OSError(f'`{fn}` does not exist!')

        self._pixel_classification = Path(defaults.predicrystal['pixel_classification'])
        self._object_classification = Path(defaults.predicrystal['object_classification'])

        assert self._pixel_classification.exists()
        assert self._object_classification.exists()

    @property
    def pixel_classification(self):
        """Path to the Ilastik pixel classification project file (`.ilp`)"""
        return self._pixel_classification

    @property
    def object_classification(self):
        """Path to the Ilastik object classification project file (`.ilp`)"""
        return self._object_classification

    def write_metadata(self, fn='settings.yaml', drc='.'):
        """Store metadata to a yaml file.

        Used for compatibility with `predicrystal`. `fn` is the
        filename, and `drc` the directory to store it in.
        """
        drc = Path(drc)
        with open(drc / fn, 'w') as f:
            yaml.dump(self.metadata, stream=f)

    def convert_to_tiff(self):
        """Convert mrc file to tiff files compatible with `Ilastik`"""
        metadata = predicrystal.generate_test_data(nav=self.nav, mrc=self.mrc)
        self.metadata = metadata

        self.scaling_factor = metadata['scaling factor']
        self.im_size = metadata['image size']
        self.nav_file = Path(metadata['nav file'])
        self.mrc_file = Path(metadata['mrc file'])
        self.tiff_folder = Path(metadata['tiff folder'])

        self.write_metadata()

    def run_ilastik(self):
        """Run the Ilastik classifiers (pixel / object)."""
        tiff_folder = self.tiff_folder
        mrc_folder = self.mrc_file.parent

        output_folder = predicrystal.run_classifiers(
            tiff_folder=tiff_folder,
            mrc_folder=mrc_folder,
            pixel_classification=self.pixel_classification,
            object_classification=self.object_classification,
        )

        self.metadata['output filename'] = str(output_folder)
        self.output_folder = output_folder

        self.write_metadata()

    def results_to_nav(
        self,
        filter_distance=defaults.predicrystal['filter_distance'],
    ):
        """Conver the `Ilastik` results to a new `.nav` file that can be read
        by SerialEM.

        `filter_distance` is the minimum accepted distance in
        micrometers between particles.
        """

        csv_folder = self.output_folder
        scaling_factor = self.scaling_factor
        im_size = self.im_size
        nav_file = self.nav_file  # Open the nav file which can be used as a template
        mrc_file = self.mrc_file

        predicrystal.results_to_nav(
            csv_folder=csv_folder,
            nav_file=nav_file,
            mrc_file=mrc_file,
            scaling_factor=scaling_factor,
            min_sep=filter_distance,
            im_size=im_size,
        )


if __name__ == '__main__':
    nav = 'nav.nav'
    mrc = 'mmm.mrc'

    cf = CrystalFinder(nav=nav, mrc=mrc)
    cf.convert_to_tiff()
    cf.run_ilastik()
    cf.results_to_nav()
