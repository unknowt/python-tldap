# Copyright 2012 VPAC
#
# This file is part of django-placard.
#
# django-placard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# django-placard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with django-placard  If not, see <http://www.gnu.org/licenses/>.

""" This module provides the LDAP functions with transaction support faked,
with a subset of the functions from the real ldap module.  Note that the async
and sync functions are identical. When transactions are not enabled they will
behave like the sync functions and return the same information.i

When transactions are enabled, the action will be delayed until commit() is
called. This means that rollback() is normally a nop. This could also be easily
changed to make the changes immediately and rollback if required.

Note although the current state is simulated in cache, the ldap search method
will not use this information; instead it will retrieve current state from
LDAP database. Suggestions to fix this appreciated.

WARNING: DON'T use more then one object/connection per database; if you have
multiple LDAPObject values for the one database things could get confused
because each one will keep track of changes seperately - if this is an issue
the caching functionality could be split into a seperate class."""

import ldap
import ldap.modlist

# hardcoded settings for this module

debugging = True
delayed_connect = True

# debugging

def debug(*argv):
    argv = [ str(arg) for arg in argv ]
    if debugging:
        print " ".join(argv)

# public methods that return wrapper class

def initialize(*args, **kwargs):
    """ Initialize an LDAP connection, identical to function in ldap module. """
    return LDAPObject(args, kwargs)

# LDAPObject wrapper class
class LDAPObject(object):

    def __init__(self, init_args, init_kwargs):
        self._init_args = init_args
        self._init_kwargs = init_kwargs
        self.reset()
        self._obj = None
        if not delayed_connect:
            self._obj = ldap.initialize(*self._init_args, **self._init_kwargs)

    # connection management

    def _reconnect(self):
        self._obj = ldap.initialize(*self._init_args, **self._init_kwargs)
        if (self._bind_args) > 0:
            self._obj.simple_bind_s(*self._bind_args, **self._bind_kwargs)

    def _do_with_retry(self, fn):
        # if no connection
        if self._obj is None:
            # never connected; try to connect and then run fn
            self._reconnect()
            return fn(self._obj)

        # otherwise try to run fn
        try:
            return fn(self._obj)
        except ldap.SERVER_DOWN:
            # if it fails, reconnect then retry
            self._reconnect()
            return fn(self._obj)

    def simple_bind(self, *args, **kwargs):
        self._bind_args = args
        self._bind_kwargs = kwargs
        if self._obj is not None:
            self._do_with_retry(lambda obj: obj.simple_bind_s(*self._bind_args, **self._bind_kwargs))

    def unbind(self):
        if self._obj is not None:
            self._do_with_retry(lambda obj: obj.unbind_s())
        self._bind_args = None
        self._bind_kwargs = None

    # cache management

    def reset(self):
        """ Reset everything back to original state, discarding all uncompleted transactions. """
        self._transact = False
        self._oncommit = []
        self._onrollback = []
        self._cache = {}

    def _cache_get_for_dn(self, dn):
        """ Object state is cached. When an update is required the update will be simulated on this cache,
        so that rollback information can be correct. This function retrieves the cached data. """
        if dn not in self._cache:
            # no cached item, retrieve from ldap
            results = self._do_with_retry(lambda obj: obj.search_s(dn, ldap.SCOPE_BASE))
            if len(results) < 1:
                raise RuntimeError("No results finding current value")
            if len(results) > 1:
                raise RuntimeError("Too many results finding current value")
            self._cache[dn] = results[0][1]

        elif self._cache[dn] is None:
            # don't allow access to deleted items
            raise RuntimeError("Object with dn %s was deleted in cache"%dn)

        # return result
        return self._cache[dn]

    def _cache_create_for_dn(self, dn):
        """ Object state is cached. When an update is required the update will be simulated on this cache,
        so that rollback information can be correct. This function retrieves the cached data. """
        if dn in self._cache and self._cache[dn] is not None:
            raise RuntimeError("Object with dn %s already exists in cache"%dn)
        self._cache[dn] = {}
        return self._cache[dn]

    def _cache_rename_dn(self, dn, newrdn):
        """ The function will rename the DN in the cache. """
        if newdn in self._cache:
            raise RuntimeError("Object with dn %s already exists in cache"%dn)
        self._cache[newrdn] = _cache_get_for_dn(self, dn)
        self._cache_del_dn(dn)

    def _cache_del_dn(self, dn):
        """ This function will mark as deleted the DN created with _cache_get_for_dn and mark it as unsuable. """
        if dn in self._cache:
            self._cache[dn] = None

    # transaction management

    def is_dirty(self):
        """ Are there uncommitted changes? """
        if len(self._oncommit) > 0:
            return True
        if len(self._onrollback) > 0:
            return True
        return False

    def enter_transaction_management(self):
        """ Start a transaction. """
        if self._transact:
            raise RuntimeError("enter_transaction_management called inside transaction")

        self._transact = True
        self._oncommit = []
        self._onrollback = []

    def leave_transaction_management(self):
        """ End a transaction. Must not be dirty when doing so. ie. commit() or
        rollback() must be called if changes made. """
        if not self._transact:
            raise RuntimeError("leave_transaction_management called outside transaction")
        if len(self._oncommit) > 0:
            raise RuntimeError("leave_transaction_management called with uncommited changes")
        if len(self._onrollback) > 0:
            raise RuntimeError("leave_transaction_management called with uncommited rollbacks")
        self.reset()

    def commit(self):
        """ Attempt to commit all changes to LDAP database, NOW! However stay inside transaction management. """
        if not self._transact:
            raise RuntimeError("commit called outside transaction")

        debug("commit", self._oncommit)
        try:
            # for every action ...
            for oncommit, onrollback in self._oncommit:
                # execute it
                debug("commiting", self._oncommit)
                self._do_with_retry(oncommit)
                # add statement to rollback log in case something goes wrong
                self._onrollback.insert(0,onrollback)
                debug(self._onrollback)
        except:
            # oops. Something went wrong. Attempt to rollback.
            debug("commit failed")
            self.rollback()
            # rollback appears to have worked, reraise exception
            raise
        finally:
            # reset everything to clean state
            self._oncommit = []
            self._onrollback = []
            self._cache = {}

    def rollback(self):
        """ Roll back to previous database state. However stay inside transaction management. """
        if not self._transact:
            raise RuntimeError("rollback called outside transaction")

        debug("rollback:", self._onrollback)
        # if something goes wrong here, nothing we can do about it, leave
        # database as is.
        try:
            # for every rollback action ...
            for onrollback in self._onrollback:
                # execute it
                debug("rolling back", onrollback)
                self._do_with_retry(onrollback)
        finally:
            # reset everything to clean state
            self._oncommit = []
            self._onrollback = []
            self._cache = {}

    def _process(self, oncommit, onrollback):
        """ Add action to list. oncommit is a callback to execute on commit(),
        onrollback is a callback to execute if the oncommit() has been called and
        a rollback is required """
        if not self._transact:
            return self._do_with_retry(oncommit)
        else:
            self._oncommit.append( (oncommit, onrollback) )
            return None

    # statements needing transactions

    def add(self, dn, *args, **kwargs):
        """ Add a DN to the LDAP database; See ldap module. Doesn't return a
        result if transactions enabled. """

        # if rollback of add required, delete it
        oncommit   = lambda obj: obj.add_s(dn, *args, **kwargs)
        onrollback = lambda obj: obj.delete_s(dn)

        # simulate this action in cache
        self._cache_create_for_dn(dn)

        # process this action
        return self._process(oncommit, onrollback)


    def modify(self, dn, modlist, *args, **kwargs):
        """ Modify a DN in the LDAP database; See ldap module. Doesn't return a
        result if transactions enabled. """

        # need to work out how to reverse changes in modlist; result in revlist
        revlist = []

        # get the current cached attributes
        result = self._cache_get_for_dn(dn)
        debug(result)

        # find the how to reverse modlist (for rollback) and put result in
        # revlist. Also simulate actions on cache.
        for mod_op,mod_type,mod_vals in modlist:
            debug("=========", mod_op, mod_type, mod_vals)
            if mod_op == ldap.MOD_ADD:
                # reverse of MOD_ADD is MOD_DELETE
                revlist.insert(0, (ldap.MOD_DELETE,mod_type,mod_vals) )

                # also carry out simulation in cache
                if mod_type not in result:
                    result[mod_type] = []
                if isinstance(mod_vals, str):
                    result[mod_type].append(mod_vals)
                else:
                    for val in mod_vals:
                        result[mod_type].append(val)
            elif mod_op == ldap.MOD_DELETE and mod_vals is not None:
                # Reverse of MOD_DELETE is MOD_ADD, but only if value is given
                # if mod_vals is None, this means all values where deleted.
                revlist.insert(0, (ldap.MOD_ADD,mod,mod_vals) )

                # also carry out simulation in cache
                if mod_type in result:
                    if isinstance(mod_vals, str):
                        result[mod_type].remove(mod_vals)
                    else:
                        for val in mod_vals:
                            result[mod_type].remove(val)
            elif mod_op == ldap.MOD_DELETE or mod_op == ldap.MOD_REPLACE:
                if mod_type in result:
                    # If MOD_DELETE with no values or MOD_REPLACE then we
                    # have to replace all attributes with cached state
                    revlist.insert(0, (ldap.MOD_REPLACE,mod_type,result[mod_type]) )
                else:
                    # except if we have no cached state for this DN, in which case we delete it.
                    revlist.insert(0, (ldap.MOD_DELETE,mod_type,None) )

                # also carry out simulation in cache
                if mod_vals is not None:
                    result[mod_type] = mod_vals
                elif mod_type in result:
                    del result[mod_type]

            debug("xxxxxxxx", revlist)
            debug(result)

        # now the hard stuff is over, we get to the easy stuff
        oncommit   = lambda obj: obj.modify_s(dn, modlist, *args, **kwargs)
        onrollback = lambda obj: obj.modify_s(dn, revlist, *args, **kwargs)
        return self._process(oncommit, onrollback)

    def delete(self, dn, *args, **kwargs):
        """ delete a dn in the ldap database; see ldap module. doesn't return a
        result if transactions enabled. """

        result = self._cache_get_for_dn(dn)
        modlist = ldap.modlist.addModlist(result)
        self._cache_del_dn(dn)

        # on commit carry out action; on rollback restore cached state
        oncommit   = lambda obj: obj.delete_s(dn, *args, **kwargs)
        onrollback = lambda obj: obj.add_s(dn, modlist)
        return self._process(oncommit, onrollback)

    def rename(self, dn, newrdn, *args, **kwargs):
        """ rename a dn in the ldap database; see ldap module. doesn't return a
        result if transactions enabled. """

        # on commit carry out action; on rollback reverse rename
        oncommit   = lambda obj: obj.rename_s(dn, newrdn, *args, **kwargs)
        onrollback = lambda obj: obj.rename_s(newrdn, dn, *args, **kwargs)
        self._cache_rename_dn(dn, newrdn)
        return self._process(oncommit, onrollback)

    # read only stuff

    def search_s(self, *args, **kwargs):
        return self._do_with_retry(lambda obj: obj.search_s(*args, **kwargs))

    # compatability hacks

    def simple_bind_s(self, *args, **kwargs):
        self.simple_bind(*args, **kwargs)

    def unbind_s(self, *args, **kwargs):
        self.unbind(*args, **kwargs)

    def add_s(self, *args, **kwargs):
        return self.add(*args, **kwargs)

    def modify_s(self, *args, **kwargs):
        return self.modify(*args, **kwargs)

    def delete_s(self, *args, **kwargs):
        return self.delete(*args, **kwargs)

    def rename_s(self, *args, **kwargs):
        return self.rename(*args, **kwargs)



