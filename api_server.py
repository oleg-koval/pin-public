#!/usr/bin/env python
import web
import logging

import api.views.base
import api.views.notifications
import api.views.authentication
import api.views.profile


class redirect:
    """
        Find and redirect to existed controller with '/' or without it
    """
    def GET(self, path):
        web.seeother('/' + path)

urls = (
    # Handle urls with slash and without it
    "/(.*)/", 'redirect',

    # API handler for notifications
    "/query/notification", api.views.notifications.Notification,

    # API to authenticate users
    "/auth", api.views.authentication.Auth,

    # API to user profile: manage user products
    "/profile/mgl", api.views.profile.ManageGetList,
)
web.config.debug = True
app = web.application(urls, globals(), autoreload=True)

if __name__ == "__main__":
    app.run()
