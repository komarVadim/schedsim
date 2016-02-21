from __future__ import division

from bisect import insort
from collections import deque, OrderedDict
from functools import reduce
from heapq import heapify, heappop, heappush
from math import ceil

from blist import blist, sorteddict, sortedlist

def intceil(x):  # superfluous in Python 3, ceil is sufficient
    return int(ceil(x))

class Scheduler:
    def next_internal_event(self):
        return None


class PS(Scheduler):
    def __init__(self):
        self.running = set()

    def enqueue(self, t, jobid, size):
        self.running.add(jobid)

    def dequeue(self, t, jobid):
        try:
            self.running.remove(jobid)
        except KeyError:
            raise ValueError("dequeuing missing job")

    def schedule(self, t):
        running = self.running
        if running:
            share = 1 / len(running)
            return {jobid: share for jobid in running}
        else:
            return {}

class GPS(Scheduler):
    def __init__(self):
        self.running = {}

    def enqueue(self, t, jobid, size, priority=1):
        self.running[jobid] = priority

    def dequeue(self, t, jobid):
        try:
            del self.running[jobid]
        except KeyError:
            raise ValueError("dequeuing missing job")

    def schedule(self, t):
        running = self.running
        if running:
            share = 1 / sum(running.values())
            return {jobid: weight * share for jobid, weight in running.items()}
        else:
            return {}

class FIFO(Scheduler):
    def __init__(self):
        self.jobs = deque()

    def enqueue(self, t, jobid, size):
        self.jobs.append(jobid)

    def dequeue(self, t, jobid):
        try:
            self.jobs.remove(jobid)
        except ValueError:
            raise ValueError("dequeuing missing job")

    def schedule(self, t):
        jobs = self.jobs
        if jobs:
            return {jobs[0]: 1}
        else:
            return {}


class LIFO(Scheduler):
    def __init__(self):
        self.jobs = []

    def enqueue(self, t, jobid, size):
        if len(self.jobs) < 2:
            self.jobs.append(jobid)
        else:
            self.jobs.insert(1, jobid)

    def dequeue(self, t, jobid):
        try:
            self.jobs.remove(jobid)

        except ValueError:
            raise ValueError("dequeuing missing job")

    def schedule(self, t):
        jobs = self.jobs
        if jobs:
            return {jobs[0]: 1}
        else:
            return {}



class SRPT(Scheduler):
    def __init__(self):
        self.jobs = []
        self.last_t = 0

    def update(self, t):
        delta = t - self.last_t
        if delta == 0:
            return
        jobs = self.jobs
        if jobs:
            jobs[0][0] -= delta
        self.last_t = t

    def enqueue(self, t, jobid, job_size):
        self.update(t)
        heappush(self.jobs, [job_size, jobid])

    def dequeue(self, t, jobid):
        jobs = self.jobs
        self.update(t)
        # common case: we dequeue the running job
        if jobid == jobs[0][1]:
            heappop(jobs)
            return
        # we still care if we dequeue a job not running (O(n)) --
        # could be made more efficient, but still O(n) because of the
        # search, by exploiting heap properties (i.e., local heappop)
        try:
            idx = next(i for i, v in jobs if v[1] == jobid)
        except StopIteration:
            raise ValueError("dequeuing missing job")
        jobs[idx], jobs[-1] = jobs[-1], jobs[idx]
        jobs.pop()
        heapify(jobs)



    def schedule(self, t):
        self.update(t)
        jobs = self.jobs
        if jobs:
            return {jobs[0][1]: 1}
        else:
            return {}

class LIFO_SR(Scheduler):
    def __init__(self):
        self.jobs = []
        self.last_t = 0

    def update(self, t):
        delta = t - self.last_t
        if delta == 0:
            return
        jobs = self.jobs
        if jobs:
            jobs[0][0] -= delta
        self.last_t = t

    def enqueue(self, t, jobid, job_size):
        self.update(t)
        jobs = self.jobs
        if jobs and job_size < jobs[0][0]:
            jobs.insert(0, [job_size, jobid])
        else:
            jobs.insert(1, [job_size, jobid])

        # print("enqueue | jobs: " + str(self.jobs) + "   last_t:  " + str(self.last_t))

    def dequeue(self, t, jobid):
        jobs = self.jobs
        self.update(t)
        # common case: we dequeue the running job
        if jobid == jobs[0][1]:
            # print("dequeue | jobs: " + str(self.jobs) + "   last_t:  " + str(self.last_t))
            jobs.pop(0)
            return
        # we still care if we dequeue a job not running (O(n)) --
        # could be made more efficient, but still O(n) because of the
        # search, by exploiting heap properties (i.e., local heappop)
        # try:
        #     idx = next(i for i, v in jobs if v[1] == jobid)
        # except StopIteration:
        #     raise ValueError("dequeuing missing job")
        # jobs[idx], jobs[-1] = jobs[-1], jobs[idx]
        # jobs.pop()
        # heapify(jobs)

    def schedule(self, t):
        self.update(t)
        jobs = self.jobs
        if jobs:
            return {jobs[0][1]: 1}
        else:
            return {}

class SRPT_plus_PS(Scheduler):

    def __init__(self, eps=1e-6):
        self.jobs = []
        self.last_t = 0
        self.late = set()
        self.eps = eps

    def update(self, t):
        delta = t - self.last_t
        jobs = self.jobs
        delta /= 1 + len(self.late)  # key difference with SRPT #1
        if jobs:
            jobs[0][0] -= delta
        while jobs and jobs[0][0] < self.eps:
            _, jobid = heappop(jobs)
            self.late.add(jobid)
        self.last_t = t

    def next_internal_event(self):
        jobs = self.jobs
        if not jobs:
            return None
        return jobs[0][0] * (1 + len(self.late))

    def schedule(self, t):
        self.update(t)
        jobs = self.jobs
        late = self.late
        scheduled = late.copy()  # key difference with SRPT #2
        if jobs:
            scheduled.add(jobs[0][1])
        if not scheduled:
            return {}
        share = 1 / len(scheduled)
        return {jobid: share for jobid in scheduled}

    def enqueue(self, t, jobid, job_size):
        self.update(t)
        heappush(self.jobs, [job_size, jobid])

    def dequeue(self, t, jobid):
        self.update(t)
        late = self.late
        if jobid in late:
            late.remove(jobid)
            return
        # common case: we dequeue the running job
        jobs = self.jobs
        if jobid == jobs[0][1]:
            heappop(jobs)
            return
        # we still care if we dequeue a job not running (O(n)) --
        # could be made more efficient, but still O(n) because of the
        # search, by exploiting heap properties (i.e., local heappop)
        try:
            idx = next(i for i, v in jobs if v[1] == jobid)
        except StopIteration:
            raise ValueError("dequeuing missing job")
        jobs[idx], jobs[-1] = jobs[-1], jobs[idx]
        jobs.pop()
        heapify(jobs)



class FSP(Scheduler):

    def __init__(self, eps=1e-6):

        # [remaining, jobid] queue for the *virtual* scheduler
        self.queue = blist()

        # Jobs that should have finished in the virtual time,
        # but didn't in the real (happens only in case of estimation
        # errors)
        # Keys are jobids (ordered by the time they became late), values are
        # not significant.
        self.late = OrderedDict()

        # last time we run the schedule function
        self.last_t = 0

        # Jobs that are running in the real time
        self.running = set()

        # Jobs that have less than eps work to do are considered done
        # (deals with floating point imprecision)
        self.eps = eps

    def enqueue(self, t, jobid, size):
        self.update(t)  # needed to age only existing jobs in the virtual queue
        insort(self.queue, [size, jobid])
        self.running.add(jobid)

    def dequeue(self, t, jobid):
        # the job remains in the virtual scheduler!
        self.running.remove(jobid)

        late = self.late
        if jobid in late:
            late.pop(jobid)

    def update(self, t):

        delta = t - self.last_t

        queue = self.queue

        if queue:
            running = self.running
            late = self.late
            eps = self.eps
            fair_share = delta / len(queue)
            fair_plus_eps = fair_share + eps

            # jobs in queue[:idx] are done in the virtual scheduler
            idx = 0
            for vrem, jobid in queue:
                if vrem > fair_plus_eps:
                    break
                idx += 1
                if jobid in running:
                    late[jobid] = True
            if idx:
                del queue[:idx]

            if fair_share > 0:
                for vrem_jobid in queue:
                    vrem_jobid[0] -= fair_share

        self.last_t = t

    def schedule(self, t):

        self.update(t)

        late = self.late
        if late:
            return {next(iter(late)): 1}

        running = self.running
        if not running:
            return {}

        jobid = next(jobid for _, jobid in self.queue if jobid in running)
        return {jobid: 1}

    def next_internal_event(self):

        queue = self.queue

        if not queue:
            return None

        return queue[0][0] * len(queue)


class FSP_plus_PS(FSP):

    def __init__(self, *args, **kwargs):

        FSP.__init__(self, *args, **kwargs)
        self.late = dict(self.late)  # we don't need the order anymore!

    def schedule(self, t):

        self.update(t)

        late = self.late
        if late:
            share = 1 / len(late)
            return {jobid: share for jobid in late}

        running = self.running
        if not running:
            return {}

        jobid = next(jobid for _, jobid in self.queue if jobid in running)
        return {jobid: 1}


class FSPE_PS_DC(FSP_plus_PS):

    def schedule(self, t):

        self.update(t)
        queue = self.queue
        running = self.running
        scheduled = set(self.late)
        try:
            scheduled.add(next(jobid for _, jobid in self.queue
                               if jobid in running))
        except StopIteration:
            pass
        if scheduled:
            share = 1 / len(scheduled)
            return {jobid: share for jobid in scheduled}
        else:
            return {}


class LAS(Scheduler):

    def __init__(self, eps=1e-6):

        # job attained service is represented as (real attained service // eps)
        # (not perfectly precise but avoids problems with floats)
        self.eps = eps

        # sorted dictionary for {attained: {jobid}}
        self.queue = sorteddict()

        # {jobid: attained} dictionary
        self.attained = {}

        # result of the last time the schedule() method was called
        # grouped by {attained: [service, {jobid}]}
        self.scheduled = {}
        # This is the entry point for doing XXX + LAS schedulers:
        # it's sufficient to touch here

        # last time when the schedule was changed
        self.last_t = 0

    def enqueue(self, t, jobid, size):

        self.queue.setdefault(0, set()).add(jobid)
        self.attained[jobid] = 0

    def dequeue(self, t, jobid):

        att = self.attained.pop(jobid)
        q = self.queue[att]
        if len(q) == 1:
            del self.queue[att]
        else:
            q.remove(jobid)

    def update(self, t):

        delta = intceil((t - self.last_t) / self.eps)
        queue = self.queue
        attained = self.attained
        set_att = set(attained)

        for att, sub_schedule in self.scheduled.items():

            jobids = reduce(set.union, (jobids for _, jobids in sub_schedule))

            # remove jobs from queue

            try:
                q_att = queue[att]
            except KeyError:
                pass  # all jobids have terminated
            else:
                q_att -= jobids
                if not q_att:
                    del queue[att]

            # recompute attained values, re-put in queue,
            # and update values in attained

            for service, jobids in sub_schedule:

                jobids &= set_att  # exclude completed jobs
                if not jobids:
                    continue
                new_att = att + intceil(service * delta)

                # let's coalesce pieces of work differing only by eps, to avoid
                # rounding errors
                attvals = [new_att, new_att - 1, new_att + 1]
                try:
                    new_att = next(v for v in attvals if v in queue)
                except StopIteration:
                    pass

                queue.setdefault(new_att, set()).update(jobids)
                for jobid in jobids:
                    attained[jobid] = new_att
        self.last_t = t

    def schedule(self, t):

        self.update(t)

        try:
            attained, jobids = self.queue.items()[0]
        except IndexError:
            service = 0
            jobids = set()
            self.scheduled = {}
        else:
            service = 1 / len(jobids)
            self.scheduled = {attained: [(service, jobids.copy())]}

        return {jobid: service for jobid in jobids}

    def next_internal_event(self):

        queue = self.queue

        if len(queue) >= 2:
            qitems = queue.items()
            running_attained, running_jobs = qitems[0]
            waiting_attained, _ = qitems[1]
            diff = waiting_attained - running_attained
            return diff * len(running_jobs) * self.eps
        else:
            return None


class SRPT_plus_LAS(Scheduler):

    def __init__(self, eps=1e-6):

        # job that should have finished, but didn't
        # (because of estimation errors)
        self.late = set()

        # [remaining, jobid] heap for the SRPT scheduler
        self.queue = sortedlist()

        # last time we run the update function
        self.last_t = 0

        # Jobs that have less than eps work to do are considered done
        # (deals with floating point imprecision)
        self.eps = eps

        # {jobid: att} where att is jobid's attained service
        self.attained = {}

        # queue for late jobs, sorted by attained service
        self.late_queue = sorteddict()

        # last result of calling the schedule function
        self.scheduled = {}

    def enqueue(self, t, jobid, size):

        size_int = intceil(size / self.eps)
        self.queue.add([size_int, jobid])
        self.attained[jobid] = 0

    def dequeue(self, t, jobid):

        att = self.attained.pop(jobid)
        late = self.late
        if jobid in late:
            late_queue = self.late_queue
            late.remove(jobid)
            latt = late_queue[att]
            if len(latt) == 1:
                del late_queue[att]
            else:
                latt.remove(jobid)
        else:
            queue = self.queue
            for i, (_, jid) in enumerate(queue):
                if jid == jobid:
                    del queue[i]
                    break

    def update(self, t):

        attained = self.attained
        eps = self.eps
        late = self.late
        late_queue = self.late_queue
        queue = self.queue
        scheduled = self.scheduled

        delta = intceil((t - self.last_t) / eps)

        # Real attained service

        def qinsert(jobid, att):
            # coalesce pieces of work differing only by eps to avoid rounding
            # errors -- return the chosen attained work value
            attvals = [att, att - 1, att + 1]
            try:
                att = next(v for v in attvals if v in late_queue)
            except StopIteration:
                late_queue[att] = {jobid}
            else:
                late_queue[att].add(jobid)
            return att

        for jobid, service in scheduled.items():
            try:
                old_att = self.attained[jobid]
            except KeyError: # dequeued job
                continue
            work = intceil(delta * service)
            new_att = old_att + work
            if jobid in self.late:
                l_old = late_queue[old_att]
                l_old.remove(jobid)
                if not l_old:
                    del late_queue[old_att]
                new_att = qinsert(jobid, new_att)
            else:
                idx, rem = next((i, r) for i, (r, jid)
                                in enumerate(queue)
                                if jid == jobid)
                new_rem = rem - work
                if new_rem <= 0:
                    del queue[idx]
                    late.add(jobid)
                    new_att = qinsert(jobid, new_att)
                else:
                    if idx == 0:
                        queue[0][0] = new_rem
                    else:
                        del queue[idx]
                        queue.add([new_rem, jobid])
            attained[jobid] = new_att

        self.last_t = t

    def schedule(self, t):

        self.update(t)

        queue = self.queue
        late_queue = self.late_queue

        jobs = {queue[0][1]} if queue else set()
        if late_queue:
            jobs.update(next(iter(late_queue.values())))

        if jobs:
            service = 1 / len(jobs)
            res = {jobid: service for jobid in jobs}
        else:
            res = {}

        self.scheduled = res
        return res

    def next_internal_event(self):

        queue = self.queue

        if queue:
            return queue[0][0] * (len(self.late) + 1) * self.eps


class FSP_plus_LAS(Scheduler):

    def __init__(self, eps=1e-6):

        # [remaining, jobid] queue for the *virtual* scheduler
        self.queue = blist()

        # Jobs that should have finished in the virtual time,
        # but didn't in the real (happens only in case of estimation
        # errors)
        self.late = set()

        # last time we run the schedule function
        self.last_t = 0

        # Jobs that are running in the real time
        self.running = set()

        # Jobs that have less than eps work to do are considered done
        # (deals with floating point imprecision)
        self.eps = eps

        # queue for late jobs, sorted by attained service
        self.late_queue = sorteddict()

        # {jobid: att} where att is jobid's attained service
        self.attained = {}

        # last result of calling the schedule function
        self.scheduled = {}

    def enqueue(self, t, jobid, size):

        self.update(t)  # needed to age only existing jobs in the virtual queue
        insort(self.queue, [intceil(size / self.eps), jobid])
        self.running.add(jobid)
        self.attained[jobid] = 0

    def dequeue(self, t, jobid):

        late = self.late

        self.running.remove(jobid)
        if jobid in late:
            late_queue = self.late_queue
            late.remove(jobid)
            att = self.attained[jobid]
            latt = late_queue[att]
            if len(latt) == 1:
                del late_queue[att]
            else:
                latt.remove(jobid)

    def update(self, t):

        attained = self.attained
        eps = self.eps
        late = self.late
        late_queue = self.late_queue
        queue = self.queue

        delta = intceil((t - self.last_t) / eps)

        # Real attained service

        def qinsert(jobid, att):
            # coalesce pieces of work differing only by eps to avoid rounding
            # errors -- return the chosen attained work value
            attvals = [att, att - 1, att + 1]
            try:
                att = next(v for v in attvals if v in late_queue)
            except StopIteration:
                late_queue[att] = {jobid}
            else:
                late_queue[att].add(jobid)
            return att

        if delta:
            for jobid, service in self.scheduled.items():
                if jobid in self.late:
                    old_att = self.attained[jobid]
                    l_old = late_queue[old_att]
                    l_old.remove(jobid)
                    if not l_old:
                        del late_queue[old_att]
                    new_att = old_att + intceil(delta * service)
                    new_att = qinsert(jobid, new_att)
                    attained[jobid] = new_att
                else:
                    attained[jobid] += intceil(delta * service)

        # Virtual scheduler

        if queue:
            running = self.running
            fair_share = intceil(delta / len(queue))
            fair_plus_eps = fair_share + 1

            # jobs in queue[:idx] are done in the virtual scheduler
            idx = 0
            for vrem, jobid in queue:
                if vrem > fair_plus_eps:
                    break
                idx += 1
                if jobid in running:
                    late.add(jobid)
                    attained[jobid] = qinsert(jobid, attained[jobid])

            if idx:
                del queue[:idx]

            if fair_share > 0:
                for vrem_jobid in queue:
                    vrem_jobid[0] -= fair_share

        self.last_t = t

    def schedule(self, t):

        self.update(t)

        late_queue = self.late_queue
        running = self.running

        if late_queue:
            jobs = next(iter(late_queue.values()))
            service = 1 / len(jobs)
            res = {jobid: service for jobid in jobs}
        elif not running:
            res = {}
        else:
            jobid = next(jobid for _, jobid in self.queue if jobid in running)
            res = {jobid: 1}
        self.scheduled = res

        return res

    def next_internal_event(self):

        eps = self.eps
        late_queue = self.late_queue
        queue = self.queue

        res = None

        if queue:
            # time at which a job becomes late
            res = queue[0][0] * len(queue) * eps
        if len(late_queue) >= 2:
            # time at which scheduled late jobs reach the service of
            # others
            qitems = late_queue.items()
            running_attained, running_jobs = qitems[0]
            waiting_attained, _ = qitems[1]
            diff = waiting_attained - running_attained
            delta = diff * len(running_jobs) * eps
            if not res or res > delta:
                res = delta
        return res


class PSBS(Scheduler):

    def __init__(self, eps=1e-6):
        # heap of (gtime, jobid, weight) for the virtual time
        self.queue = []

        # heap of (gtime, jobid, weight) for jobs that are in the virtual
        # time, done in the real time and were at the head of
        # self.queue
        self.early = []

        # time allotted to the "ghost job"
        self.gtime = 0

        # {jobid: weight} for jobs that are finished in the virtual
        # time, but not in the real (happens only in case of
        # estimation errors)
        self.late = {}

        # last time we run the update method
        self.last_t = 0

        # Jobs that are running in the real time
        self.running = set()

        # Jobs that have less than eps work to do in virtual time are
        # considered done (deals with floating point imprecision)
        self.eps = eps

        # equivalent to sum(late.values())
        self.late_w = 0

        # equivalent to sum(w for _, _, w in queue + early)
        self.virtual_w = 0

    def enqueue(self, t, jobid, size, w=1):

        if w <= 0:
            raise ValueError("w needs to be positive")

        self.update(t) # we need to age only existing jobs in the virtual queue
        heappush(self.queue, (self.gtime + size / w, jobid, w))
        self.virtual_w += w
        self.running.add(jobid)

    def dequeue(self, t, jobid):
        # job remains in the virtual time!
        self.running.remove(jobid)
        late = self.late
        if jobid in self.late:
            self.late_w -= late[jobid]
            del late[jobid]

    def update(self, t):

        delta = t - self.last_t

        virtual_w = self.virtual_w

        if self.virtual_w > 0:
            queue = self.queue
            early = self.early
            running = self.running
            late = self.late

            fair_share = delta / virtual_w

            self.gtime = gtime = self.gtime + fair_share
            gtime_plus_eps = gtime + self.eps

            # deal with jobs that are done in the virtual scheduler
            while queue and queue[0][0] < gtime_plus_eps:
                _, jobid, w = heappop(queue)
                self.virtual_w -= w
                if jobid in running:
                    late[jobid] = w
                    self.late_w += w
            while early and early[0][0] < gtime_plus_eps:
                _, _, w = heappop(early)
                self.virtual_w -= w

            # reset to avoid precision erros due to floating point
            if not queue and not early:
                self.virtual_w = 0
            else:
                assert self.virtual_w > 0

        self.last_t = t

    def schedule(self, t):

        self.update(t)

        late = self.late
        if late:
            late_w = self.late_w
            return {jobid: w / late_w for jobid, w in late.items()}

        running = self.running
        if not running:
            return {}

        queue = self.queue
        early = self.early
        while queue[0][1] not in running:
            heappush(early, heappop(queue))
        return {queue[0][1]: 1}

    def next_internal_event(self):

        virtual_w = self.virtual_w
        if virtual_w == 0:
            return None

        queue = self.queue
        early = self.early
        if queue:
            if early:
                v = min(queue[0][0], early[0][0])
            else:
                v = queue[0][0]
        else:
            v = early[0][0]

        return (v - self.gtime) * self.virtual_w

WFQE_GPS = PSBS

class FSPE_PS(WFQE_GPS):
    def enqueue(self, t, jobid, size, w=None):
        super(FSPE_PS, self).enqueue(t, jobid, size, 1)

class WSRPTE_GPS(Scheduler):

    def __init__(self, eps=1e-6):
        self.jobs = []
        self.last_t = 0
        self.late = {}
        self.late_w = 0
        self.eps = eps

    def update(self, t):
        delta = t - self.last_t
        jobs = self.jobs
        if jobs:
            rpt_over_w, w, _ = jobs[0]
            work = delta / (w + self.late_w)
            jobs[0][0] -= work / w
            while jobs and jobs[0][0] < self.eps:
                _, w, jobid = heappop(jobs)
                self.late[jobid] = w
                self.late_w += w
        self.last_t = t

    def next_internal_event(self):
        jobs = self.jobs
        if not jobs:
            return None
        rpt_over_w, w, _ = jobs[0]
        return rpt_over_w * w * w / (w + self.late_w) # = rpt * w / (w + late_w)

    def schedule(self, t):
        self.update(t)
        jobs = self.jobs
        tot_w = self.late_w
        if jobs:
            _, w, jobid = jobs[0]
            tot_w += w
            schedule = {jobid: w / tot_w}
        else:
            schedule = {}
        for jobid, w in self.late.items():
            schedule[jobid] = w / tot_w
        return schedule

    def enqueue(self, t, jobid, job_size, w=1):
        self.update(t)
        heappush(self.jobs, [job_size / w, w, jobid])

    def dequeue(self, t, jobid):
        self.update(t)
        late = self.late
        if jobid in late:
            del late[jobid]
            return
        # common case: we dequeue the running job
        jobs = self.jobs
        if jobid == jobs[0][2]:
            heappop(jobs)
            return
        # we still care if we dequeue a job not running (O(n)) --
        # could be made more efficient, but still O(n) because of the
        # search, by exploiting heap properties (i.e., local heappop)
        try:
            idx = next(i for i, v in jobs if v[2] == jobid)
        except StopIteration:
            raise ValueError("dequeuing missing job")
        jobs[idx], jobs[-1] = jobs[-1], jobs[idx]
        jobs.pop()
        heapify(jobs)
