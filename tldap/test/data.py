# Copyright 2012-2014 VPAC
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


from django.conf import settings

GROUP_DN = settings.LDAP['default']['LDAP_GROUP_BASE']
GROUP_OU = GROUP_DN.split(',')[0].split('=')[1]
USER_DN = settings.LDAP['default']['LDAP_ACCOUNT_BASE']
USER_OU = USER_DN.split(',')[0].split('=')[1]

test_ldif = [
    "dn: " + GROUP_DN,
    "objectClass: organizationalUnit",
    "ou: " + GROUP_OU,
    "",
    "dn: " + USER_DN,
    "objectClass: organizationalUnit",
    "ou: " + USER_OU,
    "",
    'dn: uid=testuser1, ' + USER_DN,
    'cn: Test User',
    'objectClass: person',
    'objectClass: shadowAccount',
    'objectClass: organizationalPerson',
    'objectClass: posixAccount',
    'objectClass: inetOrgPerson',
    'objectClass: eduPerson',
    'objectClass: auEduPerson',
    'objectClass: top',
    'objectClass: schacContactLocation',
    'objectClass: pwdPolicy',
    'userPassword:: kklk',
    'o: Example Org',
    'sn: User',
    'mail: t.user@example.com',
    'givenName: Test',
    'eduPersonAssurance: 1',
    'schacCountryOfResidence: AU',
    'uid: testuser1',
    'eduPersonAffiliation: Affiliate',
    'auEduPersonSharedToken: sdsd9894nk4',
    'uidNumber: 10000',
    'gidNumber: 10001',
    'homeDirectory: /tmp',
    'pwdAttribute: userPassword',
    '',
    'dn: uid=testuser2, ' + USER_DN,
    'cn: Test User2',
    'objectClass: person',
    'objectClass: shadowAccount',
    'objectClass: organizationalPerson',
    'objectClass: posixAccount',
    'objectClass: inetOrgPerson',
    'objectClass: eduPerson',
    'objectClass: auEduPerson',
    'objectClass: top',
    'objectClass: schacContactLocation',
    'objectClass: pwdPolicy',
    'userPassword:: gfgf',
    'o: Example Org2',
    'sn: User2',
    'mail: t.user2@example.com',
    'givenName: Test',
    'eduPersonAssurance: 1',
    'schacCountryOfResidence: AU',
    'uid: testuser2',
    'eduPersonAffiliation: Affiliate',
    'auEduPersonSharedToken: sdsd9fsdfdsfsd894nk4',
    'uidNumber: 10001',
    'gidNumber: 10001',
    'homeDirectory: /tmp',
    'pwdAttribute: userPassword',
    '',
    'dn: uid=testuser3, ' + USER_DN,
    'cn: Test User3',
    'objectClass: person',
    'objectClass: shadowAccount',
    'objectClass: organizationalPerson',
    'objectClass: posixAccount',
    'objectClass: inetOrgPerson',
    'objectClass: eduPerson',
    'objectClass: auEduPerson',
    'objectClass: top',
    'objectClass: schacContactLocation',
    'objectClass: pwdPolicy',
    'userPassword:: asdf',
    'o: Example Org3',
    'sn: User3',
    'mail: t.user3@example.com',
    'givenName: Test',
    'eduPersonAssurance: 1',
    'schacCountryOfResidence: AU',
    'uid: testuser3',
    'eduPersonAffiliation: Affiliate',
    'auEduPersonSharedToken: sdsd9894n34gfk4',
    'uidNumber: 10002',
    'gidNumber: 10001',
    'homeDirectory: /tmp',
    'pwdAttribute: userPassword',
    '',
    'dn: cn=systems, ' + GROUP_DN,
    'objectClass: top',
    'objectClass: posixGroup',
    'gidNumber: 10001',
    'cn: systems',
    'description: Systems Services',
    'memberUid: testuser1',
    '',
    'dn: cn=empty, ' + GROUP_DN,
    'objectClass: top',
    'objectClass: posixGroup',
    'gidNumber: 10002',
    'cn: empty',
    'description: Empty Group',
    '',
    'dn: cn=full,' + GROUP_DN,
    'objectClass: top',
    'objectClass: posixGroup',
    'gidNumber: 10003',
    'cn: full',
    'description: Full Group',
    'memberUid: testuser1',
    'memberUid: testuser2',
    'memberUid: testuser3',
    '',
]
