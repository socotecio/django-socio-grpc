
import logging


def get_view_logger(view_name):
	"""
	Customized Logger
	"""
	logger = logging.getLogger(view_name)
	logger.setLevel(logging.INFO)
	handler = TimedRotatingFileHandler(os.path.join(BASE_DIR, 'log/' + view_name + '.log'),
	                                   when='midnight', backupCount=20, encoding="utf8")
	formatter = logging.Formatter('%(asctime)s [%(levelname)s] : %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	return logger