# app/dbrouters.py
from grpc_framework.models import GeneralLog, SpecialLog
...
class MyDBRouter(object):
	
	route_app_labels = {'grpc_framework', }    # -- Here List the Table name or Meta App Name ---

	def db_for_read(self, model, **hints):
		""" reading SomeModel from otherdb """
		if model._meta.app_label in self.route_app_labels:
			return 'logger'
		return None

	def db_for_write(self, model, **hints):
		""" writing SomeModel to otherdb """
		if model._meta.app_label in self.route_app_labels:
			return 'logger'
		return None
	
	def allow_relation(self, obj1, obj2, **hints):
		"""
		Allow relations if a model in the grpc Framework apps is involved.
		"""
		if (
				obj1._meta.app_label in self.route_app_labels or
				obj2._meta.app_label in self.route_app_labels
				):
			return True
		return None	
	
	def allow_migrate(self, db, app_label, model_name=None, **hints):
		"""
		Make sure the logging database apps only appear in the 'grpc' database.
		"""
		if app_label in self.route_app_labels:
			return db == 'logger'
		return None	