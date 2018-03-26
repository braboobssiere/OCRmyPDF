# © 2018 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.


import pytest
import PyPDF2 as pypdf
import fitz

from ocrmypdf.pdfa import file_claims_pdfa
from ocrmypdf.exceptions import ExitCode

# pytest.helpers is dynamic
# pylint: disable=no-member
# pylint: disable=w0612

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
spoof = pytest.helpers.spoof


@pytest.mark.parametrize("output_type", [
    'pdfa', 'pdf'
    ])
def test_preserve_metadata(spoof_tesseract_noop, output_type,
                           resources, outpdf):
    pdf_before = pypdf.PdfFileReader(str(resources / 'graph.pdf'))

    output = check_ocrmypdf(
            resources / 'graph.pdf', outpdf,
            '--output-type', output_type,
            env=spoof_tesseract_noop)

    pdf_after = pypdf.PdfFileReader(str(output))

    for key in ('/Title', '/Author'):
        assert pdf_before.documentInfo[key] == pdf_after.documentInfo[key]

    pdfa_info = file_claims_pdfa(str(output))
    assert pdfa_info['output'] == output_type


@pytest.mark.parametrize("output_type", [
    'pdfa', 'pdf'
    ])
def test_override_metadata(spoof_tesseract_noop, output_type, resources,
                           outpdf):
    input_file = resources / 'c02-22.pdf'
    german = 'Du siehst den Wald vor lauter Bäumen nicht.'
    chinese = '孔子'

    p, out, err = run_ocrmypdf(
        input_file, outpdf,
        '--title', german,
        '--author', chinese,
        '--output-type', output_type,
        env=spoof_tesseract_noop)

    assert p.returncode == ExitCode.ok, err

    reader = pypdf.PdfFileReader(outpdf)

    assert reader.documentInfo['/Title'] == german
    assert reader.documentInfo['/Author'] == chinese
    assert reader.documentInfo.get('/Keywords', '') == ''

    pdfa_info = file_claims_pdfa(outpdf)
    assert pdfa_info['output'] == output_type


def test_high_unicode(spoof_tesseract_noop, resources, no_outpdf):

    # Ghostscript doesn't support high Unicode, so neither do we, to be
    # safe
    input_file = resources / 'c02-22.pdf'
    high_unicode = 'U+1030C is: 𐌌'

    p, out, err = run_ocrmypdf(
        input_file, no_outpdf,
        '--subject', high_unicode,
        '--output-type', 'pdfa',
        env=spoof_tesseract_noop)

    assert p.returncode == ExitCode.bad_args, err


@pytest.mark.parametrize('ocr_option', ['--skip-text', '--force-ocr'])
@pytest.mark.parametrize('output_type', ['pdf', 'pdfa'])
def test_bookmarks_preserved(spoof_tesseract_noop, output_type, ocr_option,
                             resources, outpdf):
    input_file = resources / 'toc.pdf'
    before_toc = fitz.Document(str(input_file)).getToC()

    check_ocrmypdf(
        input_file, outpdf,
        ocr_option,
        '--output-type', output_type,
        env=spoof_tesseract_noop)

    after_toc = fitz.Document(str(outpdf)).getToC()
    print(before_toc)
    print(after_toc)
    assert before_toc == after_toc
