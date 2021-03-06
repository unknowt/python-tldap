#!/bin/bash
DIR=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

RETURN=0
cd $DIR

if [ -n "$*" ]; then
    TESTS="$@"
else
    TESTS="tldap"
fi

# NOTE (RS) Disabled because there are far too many errors to fix.
echo ""
echo "FLAKE8"
echo "############################"
flake8 .
if [ ! $? -eq 0 ]
then
    RETURN=1
fi

echo ""
echo "TESTS - Python 2"
echo "############################"
python2 ./setup.py test
if [ ! $? -eq 0 ]
then
    RETURN=1
fi

echo ""
echo "TESTS - Python 3"
echo "############################"
python3 ./setup.py test
if [ ! $? -eq 0 ]
then
    RETURN=1
fi

exit $RETURN
