import os
import sys
import subprocess
import glob
from distutils.spawn import find_executable as which

import splunk.entity as entity

class SplunkScript(object):
	PYTHONPATH = None
	SPLUNK_HOME = os.environ.get('SPLUNK_HOME')

	sessionKey = None
	config = None
	appHome = os.path.join(SPLUNK_HOME, 'etc', 'apps', 'code42')

	def __init__(self):
		# Path to the system Python executable on your Splunk server.
		PYTHONPATH = which("python3")

		if os.name == 'nt':
			# Try to find Python3 from it's default install location.
			possiblePaths = glob.glob("C:\Python3*")

			for possiblePath in possiblePaths:
				possiblePython = "%s\python.exe" % possiblePath
				if os.path.exists(possiblePython):
					PYTHONPATH = possiblePython
					break

		if not PYTHONPATH:
			sys.stderr.write("Python3 is not installed. Reverting to (potentially unstable) default Python.\n")

			# We can't use `which("python")` because it will pick up on Splunk's embedded Python.
			PYTHONPATH = "/usr/bin/python"

		self.PYTHONPATH = PYTHONPATH

	def getSessionKey(self):
		if not self.sessionKey:
			self.sessionKey = sys.stdin.readline().strip()

		if len(self.sessionKey) == 0:
			sys.stderr.write("Did not receive a session key from splunkd. " +
							"Please enable passAuth in inputs.conf for this " +
							"script\n")
			exit(2)

		return self.sessionKey

	def getConfig(self):
		if not self.config:
			sessionKey = self.getSessionKey()

			try:
				# list all credentials
				passwordEntities = entity.getEntities(['admin', 'passwords'], namespace='code42', owner='nobody', sessionKey=sessionKey)
				configConsoleEntities = entity.getEntities(['code42', 'config', 'console'], namespace='code42', owner='nobody', sessionKey=sessionKey)  
			except Exception as e:
				raise Exception("Could not get code42 credentials from splunk. Error: %s" % (str(e)))

			config = {}

			for i, c in passwordEntities.items():
				config['username'] = c['username']
				config['password'] = c['clear_password']

			for i, c in configConsoleEntities.items():
				config['hostname'] = c['hostname']
				config['port'] = c['port']
			
			self.config = config

		return self.config

	def python(self, arguments, **kwargs):
		include_console = kwargs.get('include_console', True)

		arguments.insert(0, self.PYTHONPATH)

		if include_console:
			arguments.extend([	'-s', self.config['hostname'],
								'-port', self.config['port'],
								'-u', self.config['username'],
								'-p', self.config['password']])

		if 'PYTHONPATH' in os.environ:
			# Cross-Platform Python Path
			del os.environ['PYTHONPATH']
		if 'LD_LIBRARY_PATH' in os.environ:
			# Linux (non-Unix) Library Path
			del os.environ['LD_LIBRARY_PATH']
		if 'DYLD_LIBRARY_PATH' in os.environ:
			# Unix (non-Linux) Library Path
			del os.environ['DYLD_LIBRARY_PATH']

		if not 'STDOUT' in os.environ or os.environ['STDOUT'] != 'true':
			FNULL = open(os.devnull, 'w')
			return subprocess.call(arguments, stdout=FNULL, stderr=sys.stderr)
		else:
			return subprocess.call(arguments)

	def main(self):
		return

	def run(self):
		self.getConfig()

		self.main()