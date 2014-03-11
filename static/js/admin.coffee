jQuery ->
	$("#add_new_admin_user_button").click ->
		window.location.href = '/admin/admin_user/'
		return
		
	$("#add_new_admin_permission_button").click ->
		window.location.href = '/admin/admin_perm/'
		return
		
	return