#!/bin/sh

exit_rc=0
periname=epilog
peridir=/etc/flux/system/${periname}.d

# This script may be run in test with 'sudo flux run-prolog'
test $FLUX_JOB_USERID && userid=$(id -n -u $FLUX_JOB_USERID 2>/dev/null)
echo Running $periname for ${FLUX_JOB_ID:-unknown}/${userid:-unknown}

for file in ${peridir}/*; do
    test -e $file || continue
    name=$(basename $file)
    echo running $name >&2
    $file
    rc=$?
    test $rc -ne 0 && echo "$name exit $rc" >&2
    test $rc -gt $exit_rc && exit_rc=$rc
done

exit $exit_rc
