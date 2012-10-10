# Copyright 2012 VPAC
#
# This file is part of python-tldap.
#
# python-tldap is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# python-tldap is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with python-tldap  If not, see <http://www.gnu.org/licenses/>.

import tldap
import tldap.query
import django.utils.importlib

class LDAPmanager(object):
    def __init__(self):
        self._cls = None
        self._alias = None

    def contribute_to_class(self, cls, name):
        self._cls = cls
        setattr(cls, name, ManagerDescriptor(self))

    def db_manager(self, using):
        obj = copy.copy(self)
        obj._alias = using
        return obj

    #######################
    # PROXIES TO QUERYSET #
    #######################

    def get_query_set(self):
        return tldap.query.QuerySet(self._cls, self._alias)

    def all(self):
        return self.get_query_set()

    def get(self, *args, **kwargs):
        return self.get_query_set().get(*args, **kwargs)

    def get_or_create(self, **kwargs):
        return self.get_query_set().get_or_create(**kwargs)

    def create(self, **kwargs):
        return self.get_query_set().create(**kwargs)

    def filter(self, *args, **kwargs):
        return self.get_query_set().filter(*args, **kwargs)


    def using(self, *args, **kwargs):
        return self.get_query_set().using(*args, **kwargs)


    def base_dn(self, *args, **kwargs):
        return self.get_query_set().base_dn(*args, **kwargs)


class ManagerDescriptor(object):
    # This class ensures managers aren't accessible via model instances.
    # For example, Poll.objects works, but poll_obj.objects raises AttributeError.
    def __init__(self, manager):
        self._manager = manager

    def __get__(self, instance, type=None):
        if instance is not None:
            raise AttributeError("Manager isn't accessible via %s instances" % type.__name__)
        return self._manager

class FieldManager(LDAPmanager):
    def __init__(self, key, value, cls=None):
        super(FieldManager,self).__init__()
        self._key = key
        self._value = value
        self._cls = cls

    def get_query_set(self):
        kwargs = { self._key: self._value }
        return super(FieldManager,self).get_query_set().filter(**kwargs)

class FieldDescriptor(object):
    # This class ensures managers aren't accessible via model instances.
    # For example, Poll.objects works, but poll_obj.objects raises AttributeError.
    def __init__(self, src_key, dst_key, cls):
        self._src_key = src_key
        self._dst_key = dst_key

        self._cls = cls

    def __get__(self, instance, type=None):
        cls = self._cls
        if isinstance(cls, str):
            module_name, _, name = cls.rpartition(".")
            module = django.utils.importlib.import_module(module_name)
            cls = getattr(module, name)

        if instance is None:
            raise AttributeError("Manager isn't accessible via %s class" % type.__name__)
        return FieldManager(self._dst_key, getattr(instance, self._src_key), cls)

class FieldListManager(LDAPmanager):
    def __init__(self, key, value, cls=None):
        super(FieldListManager,self).__init__()
        self._key = key
        self._value = value
        self._cls = cls

    def get_query_set(self):
        value = self._value
        if not isinstance(value, list):
            value = [ value ]

        query = tldap.Q("OR")
        for v in value:
            kwargs = { self._key: v }
            query = query | tldap.Q(**kwargs)
        return super(FieldListManager,self).get_query_set().filter(query)


class FieldListDescriptor(object):
    # This class ensures managers aren't accessible via model instances.
    # For example, Poll.objects works, but poll_obj.objects raises AttributeError.
    def __init__(self, src_key, dst_key, cls):
        self._src_key = src_key
        self._dst_key = dst_key

        self._cls = cls

    def __get__(self, instance, type=None):
        cls = self._cls
        if isinstance(cls, str):
            module_name, _, name = cls.rpartition(".")
            module = django.utils.importlib.import_module(module_name)
            cls = getattr(module, name)

        if instance is None:
            raise AttributeError("Manager isn't accessible via %s class" % type.__name__)
        return FieldListManager(self._dst_key, getattr(instance, self._src_key), cls)
