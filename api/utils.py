import web
import json


def api_response(data, status=200, error_code="", notifications={}):
	"""
		Function preparation API response
	"""
	response = {
		"status": status,
		"error_code": error_code,
		"t_id": "",
		"s_version_id": "1.0",
		"csid_from_client": "",
		"csid_from_server": "",
		"notifications": notifications,
		"data": data
	}
	web.header('Content-Type', 'application/json')
	return json.dumps(response)


def save_api_request(request_data):
	"""
		Save data from API request
	"""
	pass
