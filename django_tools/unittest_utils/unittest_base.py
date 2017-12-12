# coding: utf-8

"""
    unittest base
    ~~~~~~~~~~~~~

    :copyleft: 2009-2017 by the django-tools team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import textwrap

from django.test import TestCase

from .BrowserDebug import debug_response


class BaseUnittestCase(TestCase):
    """
    Extensions to plain Unittest TestCase
    """
    maxDiff = 2500

    def _dedent(self, txt):
        # Remove any common leading whitespace from every line
        txt = textwrap.dedent(txt)

        # strip whitespace at the end of every line
        txt = "\n".join([line.rstrip() for line in txt.splitlines()])
        txt = txt.strip()
        return txt

    def assertEqual_dedent(self, first, second, msg=None):
        first = self._dedent(first)
        second = self._dedent(second)
        try:
            self.assertEqual(first, second, msg)
        except AssertionError as err:
            # Py2 has a bad error message
            msg = (
                "%s\n"
                "------------- [first] -------------\n"
                "%s\n"
                "------------- [second] ------------\n"
                "%s\n"
                "-----------------------------------\n"
            ) % (err, first, second)
            raise AssertionError(msg)

    def assertIn_dedent(self, member, container, msg=None):
        member = self._dedent(member)
        container = self._dedent(container)
        try:
            self.assertIn(member, container, msg)
        except AssertionError as err:
            # Py2 has a bad error message
            msg = (
                "%s\n"
                "------------- [member] -------------\n"
                "%s\n"
                "----------- [container] ------------\n"
                "%s\n"
                "------------------------------------\n"
            ) % (err, member, container)
            raise AssertionError(msg)

    def assert_is_dir(self, path):
        if not os.path.isdir(path):
            self.fail('Directory "%s" doesn\'t exists!' % path)

    def assert_not_is_dir(self, path):
        if os.path.isdir(path):
            self.fail('Directory "%s" exists, but should not exists!' % path)

    def assert_is_file(self, path):
        if not os.path.isfile(path):
            self.fail('File "%s" doesn\'t exists!' % path)

    def assert_not_is_File(self, path):
        if os.path.isfile(path):
            self.fail('File "%s" exists, but should not exists!' % path)

    def assert_startswith(self, text, prefix):
        if not text.startswith(prefix):
            self.fail("String %r doesn't starts with %r" % (text, prefix))

    def assert_endswith(self, text, prefix):
        if not text.endswith(prefix):
            self.fail("String %r doesn't ends with %r" % (text, prefix))



class BaseTestCase(BaseUnittestCase):
    # Should we open a browser traceback?
    browser_traceback = True

    def raise_browser_traceback(self, response, msg):
        debug_response(
            response, self.browser_traceback, msg, display_tb=False
        )
        msg += ' (url: "%s")' % response.request.get("PATH_INFO", "???")
        raise self.failureException(msg)

    def assertStatusCode(self, response, excepted_code=200):
        """
        assert response status code, if wrong, do a browser traceback.
        """
        if response.status_code == excepted_code:
            return # Status code is ok.
        msg = 'assertStatusCode error: "%s" != "%s"' % (response.status_code, excepted_code)
        self.raise_browser_traceback(response, msg)

    # def _assert_and_parse_html(self, html, user_msg, msg):
    #     """
    #     convert a html snippet into a DOM tree.
    #     raise error if snippet is no valid html.
    #     """
    #     try:
    #         return parse_html(html)
    #     except HTMLParseError as e:
    #         self.fail('html code is not valid: %s - code: "%s"' % (e, html))
    #
    # def _assert_and_parse_html_response(self, response):
    #     """
    #     convert html response content into a DOM tree.
    #     raise browser traceback, if content is no valid html.
    #     """
    #     try:
    #         return parse_html(response.content)
    #     except HTMLParseError as e:
    #         self.raise_browser_traceback(response, "Response's content is no valid html: %s' % e)

    def assertDOM(self, response, must_contain=(), must_not_contain=(), use_browser_traceback=True):
        """
        Asserts that html response contains 'must_contain' nodes, but no
        nodes from must_not_contain.
        """
        for txt in must_contain:
            try:
                self.assertContains(response, txt, html=True)
            except AssertionError as err:
                if use_browser_traceback:
                    self.raise_browser_traceback(response, err)
                raise

        for txt in must_not_contain:
            try:
                self.assertNotContains(response, txt, html=True)
            except AssertionError as err:
                if use_browser_traceback:
                    self.raise_browser_traceback(response, err)
                raise

    def assertResponse(self, response,
            must_contain=None, must_not_contain=None,
            status_code=200,
            template_name=None,
            html=False,
            browser_traceback=True):
        """
        Check the content of the response
        must_contain - a list with string how must be exists in the response.
        must_not_contain - a list of string how should not exists.
        """
        if must_contain is not None:
            for must_contain_snippet in must_contain:
                try:
                    self.assertContains(response, must_contain_snippet,
                        status_code=status_code, html=html
                    )
                except AssertionError as err:
                    if browser_traceback:
                        msg = 'Text not in response: "%s": %s' % (
                            must_contain_snippet, err
                        )
                        debug_response(
                            response, self.browser_traceback, msg, display_tb=True
                        )
                    raise

        if must_not_contain is not None:
            for must_not_contain_snippet in must_not_contain:
                try:
                    self.assertNotContains(response, must_not_contain_snippet,
                        status_code=status_code, html=html
                    )
                except AssertionError as err:
                    if browser_traceback:
                        msg = 'Text should not be in response: "%s": %s' % (
                            must_not_contain_snippet, err
                        )
                        debug_response(
                            response, self.browser_traceback, msg, display_tb=True
                        )
                    raise

        try:
            self.assertEqual(response.status_code, status_code)
        except AssertionError as err:
            if browser_traceback:
                msg = 'Wrong status code: %s' % err
                debug_response(
                    response, self.browser_traceback, msg, display_tb=True
                )
            raise

        if template_name is not None:
            try:
                self.assertTemplateUsed(response, template_name=template_name)
            except AssertionError as err:
                if browser_traceback:
                    msg = 'Template not used: %s' % err
                    debug_response(
                        response, self.browser_traceback, msg, display_tb=True
                    )
                raise
