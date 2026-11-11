#!/usr/bin/env bash
rc=0
grep -vE '^\s*#|^\s*$' site.yml | grep -q 'hosts:' && echo "- ✅ site.yml has plays" || { echo "- ❌ site.yml has no plays yet"; rc=1; }
grep -q 'group_by' site.yml && echo "- ✅ site.yml groups hosts by operating system (group_by)" || { echo "- ❌ site.yml does not use group_by"; rc=1; }
grep -q 'rescue:' site.yml && echo "- ✅ site.yml has a block with a rescue" || { echo "- ❌ site.yml has no rescue"; rc=1; }
grep -vE '^\s*#|^\s*$' group_vars/all.yml | grep -q 'fleet_users' && echo "- ✅ group_vars/all.yml defines fleet_users" || { echo "- ❌ group_vars/all.yml does not define fleet_users"; rc=1; }
git ls-files | grep -q '^keys/' && { echo "- ❌ keys/ is committed"; rc=1; } || echo "- ✅ no SSH key committed"
grep -qE '^ALL CHECKS PASSED \(' SUBMISSION.md && echo "- ✅ SUBMISSION.md shows ALL CHECKS PASSED" || { echo "- ❌ paste the verify.sh output ('ALL CHECKS PASSED') into SUBMISSION.md"; rc=1; }
exit $rc
