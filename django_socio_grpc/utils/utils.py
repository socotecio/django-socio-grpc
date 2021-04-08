def getModelChoice(arrValue, application='', mode=''):
	"""
	Convert array to Model Choices List
	"""
	from collections import defaultdict

	ctrValue = 0
	returnList = defaultdict(list)
	
	for value in arrValue:
		if not mode:
			returnBlock = (value, arrValue[value])
		else:
			returnBlock = (value, value)
		returnList[application].append(returnBlock)
		ctrValue += 1
		
	if ctrValue > 0:
		return returnList.get(application)
	else:
		return returnList
	
def getAppList(mode='choice'):
	"""
	Get list of Django application List
	"""
	from django.apps import apps
	
	dicApp = {}
	ctrApp = 0
	
	for app in apps.get_app_configs():
		dicApp[app.name] = app.verbose_name
		ctrApp += 1
	if ctrApp > 0 and mode == "choice":
		dicApp = getModelChoice(dicApp)

	return dicApp
	
		
def getModelList(appName=''):
	"""
	Get list of Django Data Model List
	"""
	from django.apps import apps
	dicModel = {}
	
	if not appName:
		for app in apps.get_app_configs():
			for model in app.get_models():
				modelName = model.__name__
				dicModel[modelName] = app.name		
	else:
		appTables = apps.get_app_config(appName)
		if appTables:
			for model in appTables.models:
				modelName = model
				dicModel[modelName] = appName	
				
	dicModel = getModelChoice(diModel, mode='single')
	return dicModel



def getModel(currentModelName):
	"""
	Get Model from name
	"""
	from django.apps import apps
	from django.contrib.contenttypes.models import ContentType
	currentModel = None

	if currentModelName:

		#  ----------------------------------------------------------
		#  ---  search if this model exist on Django content type ---
		#  ----------------------------------------------------------
		currentModel =  ContentType.objects.filter(model=currentModelName)
		if not currentModel:
			currentModelName =  getConvDataModel(currentModelName)
			if currentModelName:
				currentModel =  ContentType.objects.filter(model=currentModelName)

		# -------------------------------
		# ---  This Model is valid    --- 
		# -------------------------------
		if currentModel:
			app_label =  currentModel[0].app_label
			currentModel = apps.get_model(app_label=app_label, model_name=currentModelName)    
	return currentModel


def ConvChoicesToDic(List, mode="value"):
	" ==== Extract dic data and build a String ==="

	dicValue = {}

	for eachVal  in List:
		(numValue, strValue) = eachVal
		if mode == "value":
			dicValue[numValue] = strValue
		else:
			dicValue[strValue] = numValue

	return dicValue


def getFromChoices(choice, value, mode="label", default=''):
	returnValue = value
	dicVal = ConvChoicesToDic(choice, mode=mode)
	if value:
		returnValue = getFromDic(value,  dicVal,  mode='key', default=default)        
	return returnValue


def getFromDic(searchVal,  myDic,  mode='key', default=''):

	if mode ==  'value':
		for key in  myDic:
			value =  myDic[key]
			if  value ==  searchVal:
				return key
	else:
		if searchVal in  myDic:
			return myDic[searchVal]
		else:
			return default

		
	
def getElapse(mode='start', startTime=''):
	"""
	Get elapse time
	"""
	import time

	if mode == 'start':
		return time.time()
	else:
		elapse_time = time.time() - startTime

	return round(elapse_time, 2)



def getFromCategory(categ,  order='sequence',  application=''):
	"""
	"""
	from collections import defaultdict
	from utils.models import  section,  category,  categoryValue

	recordList =  []
	defaultValue =  0


	#  -------------------------------------------
	#  --- Get section and Category  object  -----
	sectionObject =  section.objects.filter(section=application)
	if sectionObject:
		if categ:
			sectionObject =  category.objects.filter(name=categ)
			if sectionObject:
				recordList =  categoryValue.objects.filter(section=categ, is_default=False, is_active=True).order_by(order)
				# -----------------------------------------
				#  ---- check Default Value             ---
				recordListDefault =  categoryValue.objects.filter(section=categ, is_default=True, is_active=True)
				if recordListDefault:
					if recordListDefault[0].is_numeric:
						defaultValue =  recordListDefault[0].value_number
					else:
						defaultValue =  recordListDefault[0].value


	returnList = defaultdict(list)


	# -----------------------------------------
	# --- Loop on Values                    ---
	# -----------------------------------------
	if recordList:
		for eachValue in recordList:
			if eachValue.is_numeric:
				try:
					returnBlock = (int(eachValue.value_number), eachValue.value_original)
				except:
					pass
			else:
				returnBlock = (eachValue.value, eachValue.value_original)
			returnList[application].append(returnBlock)

		return defaultValue,  returnList.get(application)
	return defaultValue,  returnList


def getModelColumn(modelObject):
	"""
	extract Column List from a Data Model
	"""
	arrayCol = []
	
	colList =  modelObject._meta.get_fields(include_parents=False)   #  ---- get column list of the foreignkey Data Model ----
	for eachCol in colList:
		dicColInfo =  extractColData(eachCol)
		arrayCol.append(dicColInfo)
		
	return arrayCol
		
		

def extractColData(eachCol):
	"""
	extract main  characterostic of each column
	"""

	dicCol =  {}
	name      =  eachCol.name
	typeCol   =  eachCol.get_internal_type()
	readonly  =  ''

	# --------------------------------------------
	# ----  extractcolumn lenght if available  ---
	# --------------------------------------------
	try:
		length   =  eachCol.max_length
		if not lenght:
			length =  ''
	except:
		lenght =  ''

	# --------------------------------------------
	# ----  extract verbose Name if available  ---
	# --------------------------------------------
	try:
		verboseLabel =  eachCol.verbose_name
	except:
		verboseLabel =  ''

	# ----------------------------------------
	#  ---- store characteristic of column ---
	# ----------------------------------------
	dicCol['column']     =  eachCol
	dicCol['label']      =  verboseLabel
	dicCol['name']       =  name
	dicCol['length']     =  lenght
	dicCol['type']       =  typeCol

	return dicCol
		
	


