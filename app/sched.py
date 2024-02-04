from flask_production import TaskScheduler


class SS_Scheduler(TaskScheduler):

	def __init__(self):
		super().__init__(persist_states=False)
		self._sched_mapping = {}


	def add_job(self, sched_id, every, at, tz, func, enabled=False, on_complete_cb=None):
		if sched_id in self._sched_mapping:
			raise Exception("Job already scheduled")

		j = self.every(every).at(at).tz(tz).do_parallel(func)
		if not enabled:
			j.disable()
		if on_complete_cb:
			j.register_callback(on_complete_cb, cb_type='oncomplete')

		self._sched_mapping[sched_id] = j


	def get_job(self, sched_id):
		return self._sched_mapping.get(sched_id)


	def delete_job(self, sched_id):
		j = self.get_job(sched_id)
		if j:
			self.jobs.remove(j)
			del self._sched_mapping[sched_id]

