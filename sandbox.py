from __future__ import with_statement
from threading  import Thread, Event, RLock
from time       import sleep
from glob import g
import json

class LBSamplingEvent:
  	#
	def __init__(self):
		self.event =  Event()
		self.event.clear()
		self.result = None
  	#
	def set(self, sample):
		self.result = sample
		self.event.set()
  	#
	def get(self):
		self.event.wait()
		self.event.clear()
		return self.result
#...

class LBSandbox:
  	#
	def __init__(self):
		self.program = ''
		self.pid = 0 # the current running program
		self.running = {self.pid:False}
		self.event = LBSamplingEvent()
		self.rlock = RLock()
	#
	def fire_event(self, event_type, data=None):
		if self.running[self.pid]:
			if event_type == 'SAMPLE':
				self.event.set(data)
			elif event_type == 'SHUTDOWN':
				self.event.set(None) # unblock if waiting in get_sample()
				self.stop.program()
  	#
	def get_sample(self):
		return self.event.get()
  	#
	def run_program(self, program):
		#	Must lock this critical portion
		# to make sure that only one program runs at a given time
		with self.rlock:
			self.stop_program()
			self.program = program
			self.pid += 1
			self.running[self.pid] = False
			Thread(target=self.program_loop, args=(self.pid,)).start()
			self.wait_for_new_thread()
			print 'program %d confirmed' % self.pid
	#
	def wait_for_new_thread(self):
		while not self.running[self.pid]:
			sleep(0.1)
	#
	def program_loop(self, my_pid):
		bytecode = compile(self.program, '<string>', 'exec')
		self.running[my_pid] = True
		print 'program %d started' % my_pid
		#
		# main loop
		while self.running[my_pid] and g.alive:
			__sample__ = self.get_sample()
			if __sample__: exec(bytecode)
		#
		# garbage collection
		del self.running[my_pid]
		print 'program %d ended' % my_pid
  	#
	def stop_program(self):
		with self.rlock:
			self.running[self.pid] = False


#...

''' ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

	Global object Initialization

 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ '''
g.sandbox = LBSandbox()
