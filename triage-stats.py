# Report on people doing triage work in a project. This was originally
# implemented so nova-core could track this in our weekly meetings.

import sys
import datetime
from launchpadlib.launchpad import Launchpad


if len(sys.argv) != 2:
    print 'Usage:\n\t%s projectname' % sys.argv[0]
    sys.exit(1)

projectname = sys.argv[1]

sys.stderr.write('Logging in...\n')

cachedir = '/tmp/launchpadlib-cache'
launchpad = Launchpad.login_with('openstack-lp-scripts', 'production',
                                 cachedir, version='devel')

statuses = ['New', 'Incomplete', 'Confirmed', 'Triaged', 'In Progress',
            'Fix Committed']

sys.stderr.write('Retrieving project...\n')

proj = launchpad.projects[projectname]

sys.stderr.write('Considering bugs changed in the last two weeks...\n')
now = datetime.datetime.now()
since = datetime.datetime(now.year, now.month, now.day)
since -= datetime.timedelta(days=14)

triagers = {}

bugs = proj.searchTasks(modified_since=since)
for b in bugs:
    status_toucher = None
    importance_toucher = None

    sys.stderr.write('\n%s\n' % b.title)
    sys.stderr.write('Reported by: %s\n' % b.bug.owner.display_name)
    for activity in b.bug.activity:
        if activity.whatchanged.startswith('%s: ' % sys.argv[1]):
            justdate = datetime.datetime(activity.datechanged.year,
                                         activity.datechanged.month,
                                         activity.datechanged.day)
            age = datetime.datetime.now() - justdate
            sys.stderr.write('  %s :: %s -> %s :: %s on %04d%02d%02d '
                             '(%d days ago)\n'
                             % (activity.whatchanged,
                                activity.oldvalue,
                                activity.newvalue,
                                activity.person.display_name,
                                justdate.year, justdate.month, justdate.day,
                                age.days))

            if justdate > since:
                # We define a triage as changing the status from New, and
                # changing the importance from Undecided. You must do both to
                # earn a cookie.
                if ((activity.whatchanged == '%s: status' % sys.argv[1]) and
                    (activity.oldvalue == 'New')):
                    status_toucher = activity.person.display_name

                if ((activity.whatchanged ==
                     '%s: importance' % sys.argv[1]) and
                    (activity.oldvalue == 'Undecided')):
                    importance_toucher = activity.person.display_name

    if (status_toucher and importance_toucher and
        (status_toucher == importance_toucher)):
        sys.stderr.write('  *** %s triaged this ticket **\n' % status_toucher)
        triagers.setdefault(status_toucher, [])

        bug_info = '%s' % b.bug.id
        if status_toucher == b.bug.owner.display_name:
            bug_info += '*'
        triagers[status_toucher].append(bug_info)

sys.stderr.write('\n')
print 'Report (a * after the bug id indicates self triage):'
for triager in triagers:
    print '  %s: %d (%s)' % (triager, len(triagers[triager]),
                             ', '.join(triagers[triager]))
