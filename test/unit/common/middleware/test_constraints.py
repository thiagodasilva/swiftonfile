# Copyright (c) 2014 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from swift.common.swob import Request, Response
from swiftonfile.swift.common.middleware import check_constraints
from mock import Mock, patch
from contextlib import nested


class FakeApp(object):

    def __call__(self, env, start_response):
        return Response(body="OK")(env, start_response)


def check_object_creation(req, object_name):
        return


class TestConstraintsMiddleware(unittest.TestCase):

    """ Tests for common.middleware.constraints.check_constraints """

    def setUp(self):
        self.conf = {
            'policy_2': 'test.unit.common.middleware.test_constraints'}
        self.test_check = check_constraints.filter_factory(
            self.conf)(FakeApp())

    def test_GET(self):
        path = '/V1.0/a/c/o'
        resp = Request.blank(path, environ={'REQUEST_METHOD': 'GET'}
                             ).get_response(self.test_check)
        self.assertEquals(resp.body, 'OK')

    def test_PUT_container(self):
        path = '/V1.0/a/c'
        resp = Request.blank(path, environ={'REQUEST_METHOD': 'PUT'}
                             ).get_response(self.test_check)
        self.assertEquals(resp.body, 'OK')

    def test_PUT_invalid_path(self):
        path = 'a'
        resp = Request.blank(path, environ={'REQUEST_METHOD': 'PUT'}
                             ).get_response(self.test_check)
        self.assertEquals(resp.body, 'OK')

    def test_PUT_object_with_policy2(self):
        path = '/V1.0/a/c/o'
        container_info_mock = Mock()
        container_info_mock.return_value = {'status': 0,
            'sync_key': None, 'storage_policy': '2', 'meta': {},
            'cors': {'allow_origin': None, 'expose_headers': None,
            'max_age': None}, 'sysmeta': {}, 'read_acl': None,
            'object_count': None, 'write_acl': None, 'versions': None,
            'bytes': None}

        with patch("swiftonfile.swift.common.middleware.check_constraints."
                   "get_container_info", container_info_mock):
            resp = Request.blank(path, environ={'REQUEST_METHOD': 'PUT'}
                                 ).get_response(self.test_check)
            self.assertEquals(resp.body, 'OK')

    def test_PUT_object_with_policy0(self):
        path = '/V1.0/a/c/o'
        check_object_creation_mock = Mock()
        check_object_creation_mock.return_value = ''
        container_info_mock = Mock()
        container_info_mock.return_value = {'status': 0,
            'sync_key': None, 'storage_policy': '0', 'meta': {},
            'cors': {'allow_origin': None, 'expose_headers': None,
            'max_age': None}, 'sysmeta': {}, 'read_acl': None,
            'object_count': None, 'write_acl': None, 'versions': None,
            'bytes': None}

        with nested(patch("swiftonfile.swift.common.middleware."
                          "check_constraints.get_container_info",
                          container_info_mock),
                    patch("swift.common.constraints.check_object_creation",
                          check_object_creation_mock)):
            resp = Request.blank(path, environ={'REQUEST_METHOD': 'PUT'}
                                 ).get_response(self.test_check)
            self.assertEquals(resp.body, 'OK')
