jQuery ->
	$("#add_new_admin_user_button").click ->
		window.location.href = '/admin/admin_user/'
		return
		
	$("#add_new_admin_permission_button").click ->
		window.location.href = '/admin/admin_perm/'
		return
		
	$("#admin_permission_list").on 'click', '.delete', ->
		$.permsid = $(this).attr('permsid')
		$.permsname = $(this).attr('permsname')
		$("#delete_confirmation_dialog_id").html($.permsid)
		$("#delete_confirmation_dialog_name").html($.permsname)
		$("#delete_confirmation_dialog").dialog('open')
		return
		
	$('#delete_confirmation_dialog').dialog
		autoOpen: false
		modal: true
		buttons:
			'Cancel': ->
				$(this).dialog('close')
				return
			'Confirm delete': ->
				$.confirm_dialog = $(this)
				url = "/admin/admin_perm/" + $.permsid + "/"
				$.ajax url,
						type: 'DELETE'
						dataType: 'json'
						success: (data) ->
							$("#perm" + $.permsid).remove()
							$.confirm_dialog.dialog('close')
							return
				return
		
	return