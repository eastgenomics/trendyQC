from pathlib import Path
import tarfile

from django.test import TestCase


class TestIngestion(TestCase):
    def get_reports_tar(self):
        test_file_path = Path(__file__).resolve()
        test_reports_dir = Path(f"{test_file_path.parent}/test_reports")
        test_reports_tar = list(test_reports_dir.iterdir())

        assert len(test_reports_tar) == 1, "Multiple files in test_reports dir"

        test_reports_tar = test_reports_tar[0]

        assert test_reports_tar.name == "reports.tar.gz", (
            "Name of report tar is not as expected"
        )

        return test_reports_tar

    def untar_stream_reports(self, tar):
        with tarfile.open(tar) as tf:
            for obj in tf:
                data = tf.extractfile(obj)

                # None is returned for folders, so skipping them
                if data is not None:
                    yield data

    def test_import_reports(self):
        reports_tar = self.get_reports_tar()

        for report in self.untar_stream_reports(reports_tar):
            self.assertEqual(report, "blarg")

