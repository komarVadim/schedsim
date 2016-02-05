import unittest

import schedulers
import simulator


def normalize(output):
    return sorted((float(t), jobid) for t, jobid in output)


class TestScheduler(unittest.TestCase):
    def setUp(self):
        if not hasattr(self, 'scheduler'):
            self.skipTest(reason="abstract TestScheduler class")

    def run_jobs(self, jobs, error=simulator.identity):
        return list(simulator.simulator(jobs, self.scheduler, error))

    def run_and_assertEqual(self, jobs, expected):
        self.assertEqual(normalize(self.run_jobs(jobs)), normalize(expected))

    def run_with_estimations(self, jobs, estimations):
        f = simulator.fixed_estimations(estimations)
        result = self.run_jobs(jobs, error=f)
        return list(result)

        # def test_empty(self):
        #     self.assertEqual(self.run_jobs([]), [])
        #
        # def test_one(self):
        #     result = self.run_jobs([("job1", 0, 10)])
        #     self.assertEqual(result, [(10, "job1")])


# class TestFIFO(TestScheduler):
#     scheduler = schedulers.FIFO
#
#     # def test_two(self):
#     #     self.run_and_assertEqual([('job1', 0, 10), ('job2', 0, 10)],
#     #                              [(10, 'job1'), (20, 'job2')])
#
#     def test_two_delayed(self):
#         self.run_and_assertEqual([('job1', 0, 10), ('job2', 5, 10), ('job3', 8, 10)],
#                                  [(10, 'job1'), (20, 'job2')])
#
# class TestLIFO(TestScheduler):
#     scheduler = schedulers.LIFO
#
#     # for small jobs order like for FIFO
#     def test_like_FIFO(self):
#         self.run_and_assertEqual([('job1', 0, 1), ('job2', 3, 1), ('job3', 12, 1),('job4', 7, 1)],
#                                  [(1, 'job1'), (4,'job2'), (8, 'job4'),(13, 'job3')])
#
#     def test_two_delayed(self):
#         self.run_and_assertEqual([('job1', 0, 10), ('job2', 5, 10)],
#                                  [(10, 'job1'), (20, 'job2')])
#
#     def test_delayed_reordered(self):
#         self.run_and_assertEqual([('job1', 0, 10), ('job2', 5, 10), ('job3', 6, 10),],
#                                  [(10, 'job1'), (20, 'job3'), (30, 'job2')])


# class TestPS(TestScheduler):
#     scheduler = schedulers.PS
#
#     def test_two(self):
#         self.run_and_assertEqual([('job1', 0, 10), ('job2', 0, 10)],
#                                  [(20, 'job1'), (20, 'job2')])
#
#     def test_two_delayed(self):
#         self.run_and_assertEqual([('job1', 0, 10), ('job2', 5, 10)],
#                                  [(15, 'job1'), (20, 'job2')])
#
#
class TestSRPT(TestScheduler):
    scheduler = schedulers.SRPT

    def test_two(self):
        self.run_and_assertEqual([('job1', 0, 20), ('job2', 0, 10)],
                                 [(10, 'job2'), (30, 'job1')])

    def test_two_delayed(self):
        self.run_and_assertEqual([('job1', 0, 20), ('job2', 5, 5)],
                                 [(10, 'job2'), (25, 'job1')])

    def test_starvation(self):
        self.run_and_assertEqual([('job1', 0, 15),
                                  ('job2', 0, 10),
                                  ('job3', 5, 10),
                                  ('job4', 15, 10)],
                                 [(10, 'job2'),
                                  (20, 'job3'),
                                  (30, 'job4'),
                                  (45, 'job1')])


class TestSRPTplusLIFO(TestScheduler):
    scheduler = schedulers.SRPTplusLIFO

    def test_one(self):
        self.run_and_assertEqual([('job2', 2, 1),
                                  ('job3', 6, 2),
                                  ('job4', 7, 5),
                                  ('job5', 8, 3),
                                  ('job6', 10, 4)],
                                 [(3.0, 'job1'),
                                  (5.0, 'job3'),
                                  (8.0, 'job4'),
                                  (12.0, 'job5'),
                                  (16.0, 'job6'),
                                  (20.0, 'job2')])


# #
#
# class TestFSP(TestScheduler):
#     scheduler = schedulers.FSP
#
#     def test_two(self):
#         self.run_and_assertEqual([('job1', 0, 20), ('job2', 0, 10)],
#                                  [(10, 'job2'), (30, 'job1')])
#
#     def test_two_delayed(self):
#         self.run_and_assertEqual([('job1', 0, 20), ('job2', 5, 10)],
#                                  [(15, 'job2'), (30, 'job1')])
#
#     def test_starvation(self):
#         self.run_and_assertEqual([('job1', 0, 15),
#                                   ('job2', 0, 10),
#                                   ('job3', 10, 10),
#                                   ('job4', 20, 10)],
#                                  [(10, 'job2'),
#                                   (25, 'job1'),
#                                   (35, 'job3'),
#                                   (45, 'job4')])
#
#     def test_error(self):
#         jobs = [('job1', 0, 10), ('job2', 0, 10)]
#         result = self.run_with_estimations(jobs, [15, 20])
#         self.assertEqual(result, [(10, 'job1'), (20, 'job2')])
#
#
# class TestLAS(TestScheduler):
#     scheduler = schedulers.LAS
#
#     def test_two(self):
#         self.run_and_assertEqual([('job1', 0, 20), ('job2', 0, 10)],
#                                  [(20, 'job2'), (30, 'job1')])
#
#     def test_two_delayed(self):
#         self.run_and_assertEqual([('job1', 0, 20), ('job2', 5, 10)],
#                                  [(20, 'job2'), (30, 'job1')])
#
#     # def test_starvation(self):
#         # self.run_and_assertEqual([('job1', 0, 15),
#         #                           ('job2', 0, 10),
#         #                           ('job3', 10, 10),
#         #                           ('job4', 20, 10)],
#         #                          [(40, 'job2'),
#         #                           (40, 'job3'),
#         #                           (40, 'job4'),
#         #                           (45, 'job1')])
#
#     def test_longrunning(self):
#         self.run_and_assertEqual([('job1', 0, 100),
#                                   ('job2', 20, 10)],
#                                  [(30, 'job2'),
#                                   (110, 'job1')])
#
#
if __name__ == '__main__':
    unittest.main(verbosity=1)
