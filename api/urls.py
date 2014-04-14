import web

from api.views import notifications


class redirect:
	# Find and redirect to existed controller with '/' or without it
	def GET(self, path):
		web.seeother('/' + path)


urls = (
	"/(.*)/", redirect, # Handle urls with slash and without it
	"/query/notification", notifications.Notification, # API handler for notifications
)
