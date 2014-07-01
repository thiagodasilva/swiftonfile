# Copyright (c) 2012-2014 Red Hat, Inc.
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

"""
``constraints`` is a middleware which will check storage policies 
specific constraints on PUT requests.

The ``constraints`` middleware should be added to the pipeline in your
``/etc/swift/proxy-server.conf`` file, and a mapping of storage policies and 
constraints classes be listed under the constraints filter section. 
For example::

    [pipeline:main]
    pipeline = catch_errors constraints cache proxy-server

    [filter:constraints]
    use = egg:gluster-swift#constraints
    policy_2=gluster.swift.common.sof_constraints
"""
    
import sys
from urllib import unquote
from swift.common.utils import get_logger
from swift.common.swob import Request
from swift.proxy.controllers.base import get_container_info


class CheckConstraintsMiddleware(object):

    def __init__(self, app, conf):
        self.app = app
        self.logger = get_logger(conf, log_route='constraints')
        self.swift_dir = conf.get('swift_dir', '/etc/swift')
        self.policy_constraints = {}
        for conf_key in conf:
            if conf_key.startswith('policy_'):
                self.policy_constraints[conf_key] = conf[conf_key]

    def __call__(self, env, start_response):
        request = Request(env)

        if request.method == 'PUT':
            try:
                version, account, container, obj = \
                    request.split_path(1, 4, True)
            except ValueError:
                return self.app(env, start_response)

            if obj is not None:
                obj = unquote(obj)
            else:
                return self.app(env, start_response)

            # get the constraints module for the policy for this container
            # if policy is not specified in the configuration file, use
            # default value (e.g., 'swift.common.constraints')
            container_info = get_container_info(
                env, self.app, swift_source='LE')
            try:
                policy_idx = 'policy_%s' % container_info['storage_policy']
                constraint_module = self.policy_constraints[policy_idx]
            except KeyError:
                constraint_module = 'swift.common.constraints'

            # load constraints module on the fly
            self.logger.warn("constraint_module: %s" % constraint_module)
            __import__(constraint_module)
            check_object_creation = \
                sys.modules[constraint_module].check_object_creation
            error_response = check_object_creation(request, obj)
            if error_response:
                self.logger.warn("returning error: %s", error_response)
                return error_response(env, start_response)
        return self.app(env, start_response)


def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def check_constraints_filter(app):
        return CheckConstraintsMiddleware(app, conf)

    return check_constraints_filter
