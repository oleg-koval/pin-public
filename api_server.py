#!/usr/bin/env python
import web
import logging

import api.views.base
import api.views.notifications
import api.views.authentication
import api.views.images


class redirect:
	""" 
		Find and redirect to existed controller with '/' or without it 
	"""
	def GET(self, path):
		web.seeother('/' + path)

urls = (
	"/(.*)/", 'redirect', # Handle urls with slash and without it
	"/query/notification", api.views.notifications.Notification, # API handler for notifications
	"/auth", api.views.authentication.Auth, # API to authenticate users
	"/image/upload", api.views.images.ImageUpload, # API to upload images
)
web.config.debug = True
app = web.application(urls, globals(), autoreload=True)

if __name__ == "__main__":
	app.run()
