#!/usr/bin/env python
import web
import logging

import api.views.base
import api.views.notifications
import api.views.signup
import api.views.images
import api.views.profile
import api.views.social
import api.views.search
import api.views.categories


class redirect:
    """
    Find and redirect to existed controller with '/' or without it
    """
    def GET(self, path):
        web.seeother('/' + path)

urls = (
    "/(.*)/", 'redirect', # Handle urls with slash and without it
    "/query/notification", api.views.notifications.Notification, # API handler for notifications
    "/notification/add", api.views.notifications.CreateNotification,

    # API to user signup: authenticate user
    "/auth", api.views.signup.Auth,

    # API to user signup: register user
    "/signup/register", api.views.signup.Register,

    # API to user signup: confirmation user email
    "/signup/confirmuser", api.views.signup.Confirmuser,
    "/signup/resend_activation", api.views.signup.ResendActivation,

    # API to upload images
    "/image/upload", api.views.images.ImageUpload,
    "/image/query", api.views.images.ImageQuery,
    "/image/mp", api.views.images.ManageProperties,
    "/image/categorize", api.views.images.Categorize,
    "/image/query/category", api.views.images.QueryCategory,
    "/image/query/hashtags", api.views.images.QueryHashtags,
    "/image/query/get_by_hashtags", \
        api.views.images.QueryGetByHashtags,

    # API to user profile: manage user products
    "/profile/mgl", api.views.profile.ManageGetList,
    "/profile/userinfo/update", api.views.profile.UserInfoUpdate,
    "/profile/userinfo/get", api.views.profile.GetProfileInfo,
    "/profile/userinfo/info", api.views.profile.ProfileInfo,
    "/profile/userinfo/set_privacy", api.views.profile.SetPrivacy,
    "/profile/updateviews/(?P<profile>\w+)", api.views.profile.UpdateProfileViews,
    "/profile/userinfo/boards", api.views.profile.QueryBoards,
    "/profile/userinfo/pins", api.views.profile.QueryPins,
    "/profile/userinfo/upload_pic", api.views.profile.PicUpload,
    "/profile/userinfo/upload_bg", api.views.profile.BgUpload,

    # API to user profile: change user password
    "/profile/pwd", api.views.profile.ChangePassword,

    # API for social networks: posting on user page
    "/social/poup", api.views.social.PostingOnUserPage,
    "/social/query/(followed-by|following)", api.views.social.QueryFollows,
    "/social/message", api.views.social.SocialMessage,
    "/social/message_to_conversation", \
        api.views.social.SocialMessageToConversation,
    "/social/query/messages", \
        api.views.social.SocialQueryMessages,
    "/social/query/conversations", \
        api.views.social.SocialQueryConversations,

    # API for search: items and users
    "/search/items", api.views.search.SearchItems,
    "/search/people", api.views.search.SearchPeople,

    # API for categories: get categories list
    "/categories/get", api.views.categories.GetCategories
    )
web.config.debug = True
api_app = web.application(urls, globals(), autoreload=True)

if __name__ == "__main__":
    api_app.run()
