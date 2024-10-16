"""
test_implgen.py:

Checks that the implgen tool is properly generating its impl cpp/hpp.

@author jishii
"""

import filecmp
import os
import time

import pexpect
from pexpect import EOF, TIMEOUT


# Version label for now
class Version:
    id = "0.1"
    comment = "Initial prototype"


VERSION = Version()


def file_diff(file1, file2):
    """
    Returns set of line numbers from file1 which differ from file2
    """
    diff_lines = set()
    with open(file1) as file1open:
        with open(file2) as file2open:
            count = 0
            # Compare line by line until a file hits EOF
            while 1:
                line1 = file1open.readline(5_000_000)
                line2 = file2open.readline(5_000_000)
                if not line1 or not line2:
                    break
                elif not line1 == line2:
                    diff_lines.add(count)
                count += 1

    # Warn user if one file is longer than the other
    if file_len(file1) < file_len(file2):
        print("WARNING: " + file2 + " has more lines than " + file1)
    elif file_len(file1) < file_len(file2):
        print("WARNING: " + file1 + " has more lines than " + file2)

    return diff_lines


def file_len(fname):
    """
    Helper method to get number of lines in file
    """
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def remove_headers(filename):
    """
    Remove header comment so that date doesn't
    mess up the file comparison - also removes all docstrings
    """
    with open(filename, "r+") as f:
        lines = f.readlines()
        f.seek(0)
        num = 0
        # Skip_docstring removes all lines in between two """ characters
        skip_docstring = False
        for line in lines:
            if not skip_docstring:
                if not (
                    num == 0
                    and ("*" in line or "//" in line or "'''" in line or '"""' in line)
                ):
                    # Don't want to print empty first line
                    if num != 0 or line.strip():
                        f.write(line)
                        num += 1

            if "'''" in line or '"""' in line:
                skip_docstring = not skip_docstring

        f.truncate()


def compare_genfile(filename):
    """
    Compares genfile with expected genfile
    """
    if ".py" in filename:
        filename = "DefaultDict/serializable/{}".format(filename)

    remove_headers(filename)

    if not (
        filecmp.cmp(
            filename,
            os.path.join(
                testdir, "templates", "{}.txt".format(filename).replace(".", "_")
            ),
        )
    ):
        print(
            "WARNING: {} generated incorrectly according to Autocoders".format(
                os.path.join(
                    "Python",
                    "test",
                    "enum_xml",
                    "templates",
                    "{}.txt".format(filename.replace(".", "_")),
                )
            )
        )
        diff_lines = file_diff(
            filename,
            os.path.join(
                testdir, "templates", "{}.txt".format(filename).replace(".", "_")
            ),
        )
        print(
            "WARNING: the following lines from {} differ from the template: {}".format(
                filename, str(diff_lines)
            )
        )
    else:
        print("{} is consistent with expected template".format(filename))


def test_testgen():
    """
    Tests that tests are being generated correctly
    """
    global testdir

    try:
        # cd into test directory to find test files (code/test/dictgen can only find files this way)
        curdir = os.getcwd()
        testdir = os.path.join(
            os.environ["BUILD_ROOT"], "Autocoders", "Python", "test", "implgen"
        )
        os.chdir(testdir)

        bindir = os.path.join(os.environ["BUILD_ROOT"], "Autocoders", "Python", "bin")

        if os.path.exists("MathSenderComponentImpl.cpp-template"):
            os.remove("MathSenderComponentImpl.cpp-template")
        if os.path.exists("MathSenderComponentImpl.hpp-template"):
            os.remove("MathSenderComponentImpl.hpp-template")

        # Run component through implgen
        p = pexpect.spawn(
            "python "
            + os.path.join(bindir, "implgen.py")
            + " -v "
            + os.path.join(testdir, "MathSenderComponentAi.xml")
        )
        p.expect("(?!.*ERROR).*", timeout=5)

        print("Successfully ran implgen on MathSenderComponent")

        time.sleep(3)

        # Test whether all generated files match expected
        compare_genfile("MathSenderComponentImpl.cpp-template")
        compare_genfile("MathSenderComponentImpl.hpp-template")

        os.chdir(curdir)

    ## A timeout occurs when pexpect cannot match the executable
    ## output with the designated expectation. In this case the
    ## key expectation is p.expect(expect_string, timeout=3)
    ## which tests what the method name describes
    except TIMEOUT as e:
        print("Timeout Error. Expected Value not returned.")
        #        print ("-------Program Output-------")
        #        print (ptestrun.before)
        print("-------Expected Output-------")
        print(e.get_trace())
        assert False
    except EOF:
        print("EOF Error. Pexpect did not find expected output in program output.")
        #        print ("-------Program Output-------")
        #        print (ptestrun.before)
        assert False
