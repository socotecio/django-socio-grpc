from logging import Handler
from django.utils import timezone
import json, datetime, random
from utils.utils import getFromChoices


def prepareLoggingClient(port='', service='', database='', method='', level='', elapse=0, error=0, reason=''):
	"""
	prepare Client Logging
	service      = models.ForeignKey('django_grpc_framework.grcpMicroServices', null=True, blank=True, on_delete=models.CASCADE, verbose_name="Socotec Microservice", related_name='grpc_microservice')    
	database     = models.ForeignKey('django_grpc_framework.grcpDataBases', null=True, blank=True, on_delete=models.CASCADE, verbose_name="Database Microservice", related_name="grpc_database")    
	method       = models.IntegerField(default=0, choices=CALL_TYPE)
	level        = models.IntegerField(default=0, choices=LOG_LEVEL, verbose_name="Log Level")
	query        = models.TextField(default='', null=True, blank=True)
	elapse       = models.FloatField(default=0.00, verbose_name='Elapse Time (sec)')
	result       = models.TextField(default='')
	CQRS         = models.BooleanField(default=False) 
	EventStore   = models.BooleanField(default=False) 
	
	"""
	
	dicLog = {}
	dicLog['port']     = port
	dicLog['service']  = service
	dicLog['elapse']   = elapse
	dicLog['database'] = database
	dicLog['method']   = method
	dicLog['reason']   = reason
	dicLog['error']    = error
	
	return dicLog
	

class DBHandler(Handler,object):
	"""
	This handler will add logs to a gRPC database model defined in settings.py
	If log message (pre-format) is a json string, it will try to apply the array onto the log event object
	Error Logging will go to separated databases    
	"""

	model_name = None
	expiry = None

	def __init__(self, model="", expiry=0):
		super(DBHandler,self).__init__()
		self.model_name = model
		self.expiry = int(expiry)

	def emit(self,record):
		from django_grpc_framework.models import socioGrpcErrors, grpcLogging
		from utils.utils import getModel
		from django.db.models import Q
		
		logTask    = ''
		gRPCMode   = ''
		
		# ------------------------------------------------------------
		# --- Model required to create a Log record (gRPC Client)  ---
		dicModel = {
			'service'  : ['grcpMicroServices', 'service'],
			'database' : ['grcpDataBases',     'database']
		}
		
		# ------------------------------------------------------------------
		# --- Logging should never crash                                 ---
		# --- big try block here to exit silently if exception occurred  ---
		# ------------------------------------------------------------------
		if 1 == 1:
			
			# --------------------------------------
			# --- instantiate the Logging model  ---
			try:
				model = self.get_model(self.model_name)
			except:
				from grpc_framework.models import GeneralLog as model
				
			# ----------------------------------------
			# ---  check which logging Model Used  ---
			if model.__name__ == 'grpcLogging':
				gRPCMode = 'client'
			elif model.__name__ == 'SpecialLog':
				gRPCMode = 'server'
				
			# ---------------------------------------------
			# ---  extracting Logging Data and Messages ---
			logText = self.format(record)
				
			# -------------------------------------
			# ---  Logging for gRPC Server      ---
			# -------------------------------------
			if gRPCMode == 'server':
				try:
					logTask = getattr(record, 'Task')
				except:
					pass
				log_entry = model(level=record.levelname, message=logText)
				
			# -------------------------------------
			# ---  Logging for gRPC Client      ---
			# -------------------------------------
			else:
				# --------------------------
				# -- extract  log data   ---
				levelLog = getFromChoices(grpcLogging.LOG_LEVEL, record.levelname, default=1)	
				dicColumn = {}
				dicColumn['level'] = levelLog
				dicColumn['message'] = logText
				
				# -------------------------------------------------------------
				# -- extract Col field from current Data Model and Log Data ---
				# -------------------------------------------------------------
				for field in model._meta.fields:
					try:
						# ---------------------------------------
						# --- extract Value for Logging Call ----
						logValue = getattr(record, field.name)
						
						# --------------------------------
						# --- check if Model required  ---
						if field.name in dicModel:
							currentModel = dicModel[field.name][0]
							column       = dicModel[field.name][1]
							modelInstance = getModel(currentModel)
							if modelInstance:
								kwargs =  {'{0}'.format(column): logValue}
								queryText = Q(**kwargs)
								logObject = modelInstance.objects.filter(queryText)
								if logObject:
									logValue = logObject[0]
								
						# --------------------------------------------
						# -- affect value to create the Log record ---
						dicColumn[field.name] = logValue
					except:
						pass
				log_entry = model(**dicColumn)

			# -----------------------------------------------------------
			# --- test if msg is json and apply to log record object  ---
			# -----------------------------------------------------------
			try:
				data = json.loads(record.msg)
				for key,value in data.items():
					if hasattr(log_entry,key):
						try:
							setattr(log_entry,key,value)
						except:
							pass
			except:
				pass

			log_entry.save()

			# ------------------------------------------------------
			# --- Avoid duplicate log record for same Events     ---
			# --- in 20% of time, check and delete expired logs  ---
			if self.expiry and random.randint(1,5) == 1:
				model.objects.filter(time__lt = timezone.now() - datetime.timedelta(seconds=self.expiry)).delete()
		else:
			pass

	def get_model(self, name):
		names = name.split('.')
		mod = __import__('.'.join(names[:-1]), fromlist=names[-1:])
		return getattr(mod, names[-1])