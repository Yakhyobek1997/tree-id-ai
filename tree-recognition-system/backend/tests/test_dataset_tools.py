from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from PIL import Image

# Import through backend, avoiding collision with Hugging Face's datasets package.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.datasets.download_public import get_image, list_files
from backend.datasets.download_barknet import import_archive
from backend.datasets.inventory import TreeImageDataset, summarize


def picture():
    output = BytesIO()
    Image.new('RGB', (300, 300), (40, 110, 45)).save(output, 'JPEG')
    return output.getvalue()


class DatasetToolTests(unittest.TestCase):
    def test_barknet_preserves_tree_id_and_converts_circumference(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / 'ERB.zip'
            with zipfile.ZipFile(archive, 'w') as output:
                output.writestr('ERB/42_ERB_31.4159_GalaxyS5_20170607_134920_2.jpg', picture())
            rows = import_archive(archive, root, 'ERB')
            self.assertEqual(rows[0]['tree_id'], 'barknet-42')
            self.assertEqual(rows[0]['species_label'], 'Acer platanoides')
            self.assertAlmostEqual(rows[0]['dbh_cm'], 10, places=2)
            self.assertIsNone(rows[0]['biological_age_years'])
            self.assertIsNone(rows[0]['disease'])
            (root / 'manifests').mkdir()
            (root / 'manifests' / 'test.jsonl').write_text(json.dumps(rows[0]) + '\n', encoding='utf-8')
            result = summarize(root, verify=True)
            self.assertEqual(result['total_images'], 1)
            self.assertEqual(result['errors'], [])
            dataset = TreeImageDataset(rows, root)
            self.assertEqual(dataset[0][0].mode, 'RGB')
            self.assertEqual(dataset[0][1], 0)

    def test_loader_rejects_path_outside_dataset(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset = TreeImageDataset([{'path': '../outside.jpg', 'species_label': 'oak'}], folder)
            with self.assertRaises(ValueError):
                dataset[0]

    def test_pagination_follows_token(self):
        pages = [{'datasetFiles': [{'name': 'a.jpg'}], 'nextPageToken': 'page2'},
                 {'datasetFiles': [{'name': 'b.jpg'}], 'nextPageToken': ''}]
        with patch('backend.datasets.download_public.read_json', side_effect=pages) as request:
            self.assertEqual(len(list_files('dataset')), 2)
            self.assertEqual(request.call_args.args[1]['pageToken'], 'page2')

    def test_download_rejects_html_and_accepts_single_image_zip(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.iter_content.return_value = [b'<html>Login required</html>']
        with patch('backend.datasets.download_public.requests.get', return_value=response):
            with self.assertRaises(OSError):
                get_image('https://example.invalid/image')
            output = BytesIO()
            with zipfile.ZipFile(output, 'w') as archive:
                archive.writestr('../../image.jpg', picture())
            response.iter_content.return_value = [output.getvalue()]
            self.assertEqual(get_image('https://example.invalid/image'), picture())


if __name__ == '__main__':
    unittest.main()
