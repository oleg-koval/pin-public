jQuery ->
	$("#add_new_admin_user_button").click ->
		window.location.href = '/admin/admin_user_add_new/'
		return
		
	$("#add_new_admin_permission_button").click ->
		window.location.href = '/admin/admin_perms_add_new/'
		return
		
	return