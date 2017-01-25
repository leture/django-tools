# coding: utf-8

from __future__ import unicode_literals


import os
import sys

import django

from django.contrib.auth.models import User
from django.test import SimpleTestCase
from django.utils import six
from django_tools.template.render import render_string_template
from django_tools.unittest_utils.celery import task_always_eager
from django_tools.unittest_utils.print_sql import PrintQueries
from django_tools.unittest_utils.stdout_redirect import StdoutStderrBuffer
from django_tools.unittest_utils.tempdir import TempDir
from django_tools.unittest_utils.template import TEMPLATE_INVALID_PREFIX, set_string_if_invalid
from django_tools.unittest_utils.unittest_base import BaseUnittestCase, \
    BaseTestCase


class TestBaseUnittestCase(BaseUnittestCase):
    def test_dedent(self):
        """
        Test for BaseUnittestCase._dedent()
        """
        out1 = self._dedent("""
            one line
            line two""")
        self.assertEqual(out1, "one line\nline two")

        out2 = self._dedent("""
            one line
            line two
        """)
        self.assertEqual(out2, "one line\nline two")

        out3 = self._dedent("""
            one line

            line two
        """)
        self.assertEqual(out3, "one line\n\nline two")

        out4 = self._dedent("""
            one line
                line two

        """)
        self.assertEqual(out4, "one line\n    line two")

        # removing whitespace and the end
        self.assertEqual(self._dedent("\n  111  \n  222"), "111\n222")

        out5 = self._dedent("""
            one line
                line two
            dritte Zeile
        """)
        self.assertEqual(out5, "one line\n    line two\ndritte Zeile")

    def test_assert_is_dir(self):
        existing_path = os.path.dirname(__file__)
        self.assert_is_dir(existing_path)
        try:
            self.assert_is_dir("foobar_dir")
        except AssertionError as err:
            self.assertEqual(
                six.text_type(err),
                six.text_type('Directory "foobar_dir" doesn\'t exists!')
            )

    def test_assert_not_is_dir(self):
        self.assert_not_is_dir("foobar_dir")
        existing_path = os.path.dirname(__file__)
        try:
            self.assert_not_is_dir(existing_path)
        except AssertionError as err:
            self.assertEqual(
                six.text_type(err),
                six.text_type('Directory "%s" exists, but should not exists!' % existing_path)
            )


    def test_assert_is_file(self):
        self.assert_is_file(__file__)
        try:
            self.assert_is_file("foobar_file.txt")
        except AssertionError as err:
            self.assertEqual(
                six.text_type(err),
                six.text_type('File "foobar_file.txt" doesn\'t exists!')
            )

    def test_assert_not_is_File(self):
        self.assert_not_is_File("foobar_file.txt")
        try:
            self.assert_not_is_File(__file__)
        except AssertionError as err:
            self.assertEqual(
                six.text_type(err),
                six.text_type('File "%s" exists, but should not exists!' % __file__)
            )


class TestTempDir(BaseUnittestCase):

    def testTempDir(self):
        """ test TempDir() """
        with TempDir(prefix="foo_") as tempfolder:
            self.assert_is_dir(tempfolder)
            self.assertIn(os.sep + "foo_", tempfolder)

            test_filepath = os.path.join(tempfolder, "bar")
            open(test_filepath, "w").close()
            self.assert_is_file(test_filepath)

        # cleaned?
        self.assert_not_is_dir(tempfolder)
        self.assert_not_is_File(test_filepath)


class TestStdoutStderrBuffer(BaseUnittestCase):
    def test_text_type(self):
        with StdoutStderrBuffer() as buffer:
            print(six.text_type("print text_type"))
            sys.stdout.write(six.text_type("stdout.write text_type\n"))
            sys.stderr.write(six.text_type("stderr.write text_type"))
        self.assertEqual_dedent(buffer.get_output(), """
            print text_type
            stdout.write text_type
            stderr.write text_type
        """)

    def test_binary_type(self):
        if six.PY2:
            with StdoutStderrBuffer() as buffer:
                print("print str")
                sys.stdout.write("stdout.write str\n")
                sys.stderr.write("stderr.write str")
            self.assertEqual_dedent(buffer.get_output(), """
                print str
                stdout.write str
                stderr.write str
            """)
        elif six.PY3:
            # The print function will use repr
            with StdoutStderrBuffer() as buffer:
                print(b"print binary_type")
                sys.stdout.write(b"stdout.write binary_type\n")
                sys.stderr.write(b"stderr.write binary_type")
            self.assertEqual_dedent(buffer.get_output(), """
                b'print binary_type'
                stdout.write binary_type
                stderr.write binary_type
            """)
        else:
            self.fail()


class TestPrintSQL(BaseTestCase):
    def test(self):
        with StdoutStderrBuffer() as buffer:
            with PrintQueries("Create object"):
                User.objects.all().count()

        output = buffer.get_output()
        # print(output)

        self.assertIn("*** Create object ***", output)
        # FIXME: Will fail if not SQLite/MySQL is used?!?
        if django.VERSION < (1, 9):
            self.assertIn("1 - QUERY = 'SELECT COUNT(", output)
        else:
            self.assertIn("1 - SELECT COUNT(", output)
        self.assertIn('FROM "auth_user"', output)



@set_string_if_invalid()
class TestSetStringIfInvalidDecorator(SimpleTestCase):
    def assert_activation(self):
        from django.conf import settings
        string_if_invalid = settings.TEMPLATES[0]['OPTIONS']['string_if_invalid']
        self.assertIn(TEMPLATE_INVALID_PREFIX, string_if_invalid)

    def test_valid_tag(self):
        self.assert_activation()
        content = render_string_template("pre{{ tag }}post", {"tag": "FooBar!"})
        self.assertEqual(content, 'preFooBar!post')
        self.assertNotIn(TEMPLATE_INVALID_PREFIX, content)

    def test_invalid_tag(self):
        self.assert_activation()
        content = render_string_template("pre{{ tag }}post", {})
        self.assertEqual(content, 'pre***invalid:tag***post')
        self.assertIn(TEMPLATE_INVALID_PREFIX, content)


@task_always_eager()
class TestCeleryDecorator(SimpleTestCase):
    def test_settings_set(self):
        from django.conf import settings
        self.assertTrue(settings.CELERY_ALWAYS_EAGER)

    def test_disabled_celery(self):
        from celery import current_app
        self.assertTrue(current_app.conf.CELERY_ALWAYS_EAGER)
        self.assertTrue(current_app.conf['task_always_eager'])
