from django.urls import reverse   # from django.urls
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, pre_save, pre_delete
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from django_mysql.models import ListCharField, ListTextField
from django.db.models import IntegerField, SmallIntegerField
from django.utils.translation import ugettext_lazy as _ 


class TimestampedModel(models.Model):
	"""
	A model baseclass adding 'created at' and 'last modified at'
	fields to models.
	"""
	created = models.DateTimeField(blank=True)
	modified = models.DateTimeField(blank=True)
	is_active = models.BooleanField(default=True)
	is_delete = models.BooleanField(default=False)

	class Meta:
		abstract = True
		app_label = 'account'

	def save(self, **kwargs):
		"""
		On save, update timestamps
		"""
		import datetime

		now = datetime.datetime.now()
		if not self.id:
			self.created = now
		self.modified = now
		super(TimestampedModel, self).save(**kwargs)


class grcpErrorCode(TimestampedModel):
	"""
    Official Google gRPC error code
	"""

	ERROR_TYPE = (
	    (1,       'Critical'),
	    (2,       'Warning'),
	)

	code     = models.IntegerField(default=0)
	status   = models.CharField(max_length=40, null=False, blank=False, db_index=True)
	reason   = models.CharField(max_length=250, null=False, blank=False, db_index=True, verbose_name='Reason Error', default='')
	notes    = models.TextField('gRPC Notes', null=True, blank=True)
	count    = models.BigIntegerField(default=0)
	category = models.IntegerField(default=1, choices=ERROR_TYPE, verbose_name="Error Type")
	
	class Meta:
		app_label = 'django_grpc_framework'   
		verbose_name = _('GRPC ERROR CODE')
		verbose_name_plural = _('GRPC ERRORS CODES')
	
	
	def __str__(self):
		return '%s (%s)' % (self.code,  self.status)
	

class grcpMicroServices(TimestampedModel):
	"""
    Official socotec Cross reference for available microservices
	"""
	
	SERVICE_TYPE = (
	    (1,       'SOCOTEC'),
	    (2,       'GOOGLE'),
	)
	RESULT_TYPE = (
	    (1,       'ARRAY'),
	    (2,       'SINGLE'),
	)

	service     = models.CharField(max_length=40, null=False, blank=False, db_index=True, verbose_name='Service Name')
	category    = models.IntegerField(default=1, choices=SERVICE_TYPE, verbose_name="Services Category")
	result      = models.IntegerField(default=1, choices=RESULT_TYPE,  verbose_name="Result Type")
	description = models.TextField('gRPC Notes', null=True, blank=True)
	count       = models.BigIntegerField(default=0, verbose_name='Count Access')
	error       = models.BigIntegerField(default=0, verbose_name='Count Errors')
	directory   = models.CharField(max_length=60, null=False, blank=False, db_index=True, verbose_name='Service Directory')
	isInput     = models.BooleanField(default=False, verbose_name="Input Required")
	
	class Meta:
		app_label = 'django_grpc_framework'   
		verbose_name = _('GRPC SERVICE REFERENCE')
		verbose_name_plural = _('GRPC SERVICES REFERENCES')
		
	def clean(self):
		self.directory=self.service		
	
	
	def __str__(self):
		return '%s' % (self.service)


class grcpDataBases(TimestampedModel):
	"""
    Official gRPC Socotec  Databases
	"""
	from utils.utils import getAppList, getModelList
	
	appChoices = getAppList()     # --  get Django application list ---
	#modelChoices = getModelList()   # --  get Django Data Model list ---

	django       = models.CharField(max_length=40, null=False, blank=False, db_index=True, default="", verbose_name="Django Application", choices=appChoices)
	database     = models.CharField(max_length=40, null=False, blank=False, db_index=True, default="",verbose_name="Table SQL")
	description  = models.TextField('gRPC Notes', null=True, blank=True)
	service      = models.ForeignKey(grcpMicroServices, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Socotec Microservice")    
	
	class Meta:
		app_label = 'django_grpc_framework'   
		verbose_name = _('GRPC DATABASE')
		verbose_name_plural = _('GRPC DATABASES')
	
	
	def __str__(self):
		return '%s' % (self.database)
	



class socioGrpcErrors(TimestampedModel):
	"""
    qRPC error during request
	"""
	
	import datetime
	from utils.utils import getFromCategory

	#(DEFAULT_CALL_TYPE, CALL_TYPE) = getFromCategory('CALL_TYPE',  application='GRPC')


	CALL_TYPE = (
	    (1,        'List'),
	    (2,        'Create'),
		(3,        'Retrieve'),
		(4,        'Update'),
		(5,        'Destroy'),
		(6,        'Custom'),
	)


	service      = models.ForeignKey(grcpMicroServices, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Socotec Microservice")    
	database     = models.ForeignKey(grcpDataBases, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Database Microservice")    
	error        = models.ForeignKey(grcpErrorCode, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Microservice Error")    
	reason       = models.CharField(max_length=250, null=False, blank=False, db_index=True, verbose_name='Reason Error', default='')
	method       = models.IntegerField(default=0, choices=CALL_TYPE)
	aborted      = models.BooleanField(default=False, verbose_name="Thread aborted ?")
	custom       = models.BooleanField(default=False, verbose_name="Customized Error")
	query        = models.TextField(default='', null=True, blank=True, verbose_name="Service Input")
	details      = models.TextField(default='', null=True, blank=True, verbose_name="Error Description")
	elapse       = models.FloatField(default=0.00, verbose_name='Elapse Time (sec)')
	
	class Meta:
		app_label = 'django_grpc_framework'   
		verbose_name = _('GRPC ERROR HANDLER')
		verbose_name_plural = _('GRPC ERRORS HANDLER')
	
	
	def __str__(self):
		return '%s (%s-%s)' % (self.method, self.error.code, self.error.status)
	


class grpcLogging(TimestampedModel):
	"""
    qRPC Logging
	"""
	
	import datetime
	
	CALL_TYPE = (
	    (1,        'List'),
	    (2,        'Create'),
		(3,        'Retrieve'),
		(4,        'Update'),
		(5,        'Destroy'),
	)


	LOG_LEVEL = (
	    (1,        'DEBUG'),
	    (2,        'INFO'),
		(3,        'WARNING'),
		(4,        'ERROR'),
		(5,        'CRITICAL'),
	)


	service      = models.ForeignKey(grcpMicroServices, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Microservice")    
	database     = models.ForeignKey(grcpDataBases, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Database")    
	method       = models.IntegerField(default=0, choices=CALL_TYPE)
	level        = models.IntegerField(default=0, choices=LOG_LEVEL, verbose_name="Level")
	port         = models.IntegerField(default=0, verbose_name="Port")
	error        = models.IntegerField(default=0, verbose_name="Error")
	reason       = models.CharField(max_length=250, null=False, blank=False, db_index=True, verbose_name='Reason', default='')
	query        = models.TextField(default='', null=True, blank=True)
	time         = models.DateTimeField(auto_now_add=True, blank=True, null=True)
	elapse       = models.FloatField(default=0.00, verbose_name='Elapse(sec)')
	result       = models.TextField(default='')
	message      = models.TextField(default='')
	CQRS         = models.BooleanField(default=False) 
	EventStore   = models.BooleanField(default=False) 
	
	class Meta:
		app_label = 'django_grpc_framework'   
		verbose_name = _('GRPC LOGGING HANDLER')
		verbose_name_plural = _('GRPC LOGGING HANDLER')
	
	
	def __str__(self):
		return '%s (%s)' % (self.method, self.service.service)
	


class grpcMethod(TimestampedModel):
	"""
    qRPC Method per Services and Database
	"""
	
	METHOD_TYPE = (
	    ('list',        'List'),
		('create',      'Create'),
		('retrieve',    'Retrieve'),
		('update',      'Update'),
		('destroy',     'Destroy'),
	)

	RESULT_TYPE = (
	    ('array',        'Array'),
		('get',          'Single'),
	)

	INPUT_TYPE = (
	    ('',        'N/A'),
		('arg',     'Args'),
	)


	service      = models.ForeignKey(grcpMicroServices, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Microservice")    
	database     = models.ForeignKey(grcpDataBases, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Database")    
	method       = models.CharField(max_length=40, null=False, blank=False, default='list', choices=METHOD_TYPE)
	result       = models.CharField(max_length=40, null=False, blank=False, default='array', choices=RESULT_TYPE)
	input        = models.CharField(max_length=40, null=False, blank=False, default='array', choices=INPUT_TYPE)
	is_update    = models.BooleanField(default=False, verbose_name='Updade')
	
	class Meta:
		app_label = 'django_grpc_framework'   
		verbose_name = _('GRPC SERVICE METHOD')
		verbose_name_plural = _('GRPC SERVICES METHODS')
	
	def __str__(self):
		return '%s (%s)' % (self.method, self.service.service)
	

class grcpProtoBuf(TimestampedModel):
	"""
    Official gRPC Protobuf and PBD2 GRPC definition for Socotecio Services
	"""

	protobuf     = models.CharField(max_length=50, null=False, blank=False, db_index=True, default="",verbose_name="Proto Name")
	file         = models.CharField(max_length=50, null=False, blank=False, db_index=True, default="",verbose_name="Proto File")
	service      = models.ForeignKey(grcpDataBases, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Microservice Database")    
	
	class Meta:
		app_label           = 'django_grpc_framework'   
		verbose_name        = _('GRPC PROTOBUF')
		verbose_name_plural = _('GRPC PROTOBUF')
	
	
	def __str__(self):
		return '%s' % (self.protobuf)
	


class grcpProtoBufFields(TimestampedModel):
	"""
    Official gRPC Protobuf Data Models fields definitions
	"""

	database       = models.ForeignKey(grcpDataBases, null=True, blank=True, on_delete=models.CASCADE,  verbose_name="Microservice Database")    
	protobuf       = models.ForeignKey(grcpProtoBuf, null=True, blank=True, on_delete=models.CASCADE,   verbose_name="Microservice Protobuf")    
	field          = models.CharField(max_length=50, null=False, blank=False, db_index=True, default="",verbose_name="Protobuf Field")
	is_query       = models.BooleanField(default=False, verbose_name="Query")
	is_update      = models.BooleanField(default=False, verbose_name="Update")
	field_sequence = models.IntegerField(default=1, verbose_name="Field Sequence")
	query_sequence = models.IntegerField(default=1, verbose_name="Query Sequence" )
	
	class Meta:
		app_label           = 'django_grpc_framework'   
		verbose_name        = _('GRPC PROTOBUF FIELD')
		verbose_name_plural = _('GRPC PROTOBUF FIELDS')
	
	
	def __str__(self):
		return '%s' % (self.field)
	
	

class sectionProfile(TimestampedModel):
	"""
	Major Section 
	"""
	section     = models.CharField(max_length=100, null=False, blank=False, db_index=True)
	is_active   = models.BooleanField(default=True)
	is_delete   = models.BooleanField(default=False)
	description = models.TextField('Section Description', null=True, blank=True)

	class Meta:
		app_label = 'cupid'
		verbose_name = _('CATEGORY SECTION')
		verbose_name_plural = _('CATEGORY SECTIONS')
		ordering =  ['section',  ]

	def __str__(self):
		return '%s' % (self.section)
	

class DBLogEntry(models.Model):
	time = models.DateTimeField(auto_now_add=True)
	level = models.CharField(max_length=10)
	message = models.TextField()

	class Meta:
		abstract = True
		app_label = 'django_grpc_framework'
		verbose_name = _('DJANGO SYSTEM LOG')
		verbose_name_plural = _('DJANGO SYSTEM LOGS')

class GeneralLog(DBLogEntry, TimestampedModel):
	pass

class SpecialLog(DBLogEntry, TimestampedModel):
	pass

	

	
	
	
