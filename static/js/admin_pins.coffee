jQuery ->
	$('#search_button').on 'click', (event) ->
		event.preventDefault()
		search_data =
			'pin_url': $('#pin_url').val(),
			'username': $('#username').val(),
			'name': $('#name').val(),
			'email': $('#email').val()
		$.ajax
			data: search_data,
			url: '/admin/pins/search/set_search_criteria',
			success: ->	
				$.pagination_grid.g.load()
				return
		return
	
	$('.datagrid').on 'click', 'tr', (event) ->
		event.preventDefault()
		event.stopPropagation()
		pinid = $(this).attr('pinid')
		window.location.href = '/admin/pin/' + pinid
		return
		
		
	$('#delete_pin_button').on 'click', (event) ->
		event.preventDefault()
		event.stopPropagation()
		pinid = $(this).attr('pinid')
		$.ajax
			method: 'delete',
			success: ->
				window.location.href = '/admin/pins/search'
				return
		return
	
	return