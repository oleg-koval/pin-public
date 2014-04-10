from api.utils import api_response


class BaseAPI(object):
	"""
		Base class for API handler
	"""
	def GET(self):
		"""
			Wrong HTTP method for API handling
		"""
		status = 405
		error_code = "Method Not Allowed"
		data = {}
		response = api_response(data, status=status, error_code=error_code)
		return response

	def POST(self):
		"""
			Handler for API call. Must be overriden
		"""
		raise NotImplemented
