#!/usr/bin/env python
import web
import logging

import api.views.base
import api.views.notifications
import api.views.authentication
import api.views.images
import api.views.profile


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
    # API to user profile: manage user products
    "/profile/mgl", api.views.profile.ManageGetList,

    # API to user profile: change user password
    "/profile/pwd", api.views.profile.ChangePassword,
)
web.config.debug = True
api_app = web.application(urls, globals(), autoreload=True)

if __name__ == "__main__":
    api_app.run()
