"""
Helper functions for running tests
"""
import os
import subprocess as sp
import csv
import json
from settings import CWL_ARGS
from collections import OrderedDict
import unittest
from tempfile import mkdtemp
import shutil

class TmpDirTestCase(unittest.TestCase):
    """
    unittest.TestCase wrapper that includes a tmpdir
    """
    def setUp(self):
        self.preserve = False # save the tmpdir
        self.tmpdir = mkdtemp() # dir = THIS_DIR

    def tearDown(self):
        if not self.preserve:
            # remove the tmpdir upon test completion
            shutil.rmtree(self.tmpdir)

def run_command(args):
    """
    Helper function to run a shell command easier

    Parameters
    ----------
    args: list
        a list of shell args to execute
    """
    process = sp.Popen(args, stdout = sp.PIPE, stderr = sp.PIPE, universal_newlines = True)
    proc_stdout, proc_stderr = process.communicate()
    returncode = process.returncode
    proc_stdout = proc_stdout.strip()
    proc_stderr = proc_stderr.strip()
    return(returncode, proc_stdout, proc_stderr)

def run_cwl(
    testcase, # 'self' in the unittest.TestCase instance
    tmpdir, # dir where execution is taking place and files are staged & written
    input_json, # CWL input data
    cwl_file, # CWL file to run
    CWL_ARGS = CWL_ARGS, # default cwltool args to use
    print_stdout = False,
    print_command = False,
    check_returncode = True
    ):
    """Run the CWL"""
    input_json_file = os.path.join(tmpdir, "input.json")
    with open(input_json_file, "w") as json_out:
        json.dump(input_json, json_out)

    output_dir = os.path.join(tmpdir, "output")
    tmp_dir = os.path.join(tmpdir, "tmp")
    cache_dir = os.path.join(tmpdir, "cache")

    command = [
        "cwl-runner",
        *CWL_ARGS,
        "--outdir", output_dir,
        "--tmpdir-prefix", tmp_dir,
        "--cachedir", cache_dir,
        cwl_file, input_json_file
        ]
    if print_command:
        print(command)

    returncode, proc_stdout, proc_stderr = run_command(command)


    if print_stdout:
        print(proc_stdout)

    if returncode != 0:
        print(proc_stderr)

    if check_returncode:
        testcase.assertEqual(returncode, 0)

    output_json = json.loads(proc_stdout)
    return(output_json, output_dir)


def parse_header_comments(filename):
    """
    Parse a file with comments in its header to return the comments and the line number to start reader from

    comments, start_line = parse_header_comments(filename)
    with open(portal_file) as fin:
        while start_line > 0:
            next(fin)
            start_line -= 1
        reader = csv.DictReader(fin, delimiter = '\t') # header_line = next(fin)
        portal_lines = [ row for row in reader ]
    """
    comments = []
    start_line = 0
    # find the first line without comments
    with open(filename) as fin:
        for i, line in enumerate(fin):
            if line.startswith('#'):
                comments.append(line.strip())
                start_line += 1
    return(comments, start_line)

def load_mutations(filename):
    """
    Load the mutations from a file to use for testing
    """
    comments, start_line = parse_header_comments(filename)
    with open(filename) as fin:
        while start_line > 0:
            next(fin)
            start_line -= 1
        reader = csv.DictReader(fin, delimiter = '\t')
        mutations = [ row for row in reader ]
    return(comments, mutations)

def write_table(tmpdir, filename, lines, delimiter = '\t'):
    """
    Write a table to a temp location
    """
    filepath = os.path.join(tmpdir, filename)
    with open(filepath, "w") as f:
        for line in lines:
            line_str = delimiter.join(line) + '\n'
            f.write(line_str)
    return(filepath)

def dicts2lines(dict_list, comment_list = None):
    """
    Helper function to convert a list of dicts into a list of lines to use with write_table
    create a list of line parts to pass for write_table;
    [ ['# comment1'], ['col1', 'col2'], ['val1', 'val2'], ... ]
    """
    fieldnames = OrderedDict() # use as an ordered set
    # get the ordered fieldnames
    for row in dict_list:
        for key in row.keys():
            fieldnames[key] = ''
    # list to hold the lines to be written out
    demo_maf_lines = []
    if comment_list:
        for line in comment_list:
            demo_maf_lines.append(line)
    fieldnames = [ f for f in fieldnames.keys() ]
    demo_maf_lines.append(fieldnames)
    for row in dict_list:
        demo_maf_lines.append([ v for v in row.values() ])
    return(demo_maf_lines)
