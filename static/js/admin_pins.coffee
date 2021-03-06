jQuery ->
	$('#search_button').on 'click', (event) ->
		event.preventDefault()
		search_data =
			'pin_url': $('#pin_url').val(),
			'username': $('#username').val(),
			'name': $('#name').val(),
			'email': $('#email').val(),
			'category': $('#category').val()
		$.ajax
			data: search_data,
			url: '/admin/pins/search/set_search_criteria',
			success: ->	
				$.pagination_grid.g.load()
				return
		return
	
	$('.datagrid').on 'click', '.edit-pin', (event) ->
		event.preventDefault()
		event.stopPropagation()
		pinid = $(this).attr('pinid')
		window.location.href = '/admin/pin/' + pinid
		return
	
	
	$('#select_all_pins').on 'click', (event) ->
		$.pagination_grid.g.selectAll()
	
	
	$('#unselect_all_pins').on 'click', (event) ->
		$.pagination_grid.g.unSelectAll()
	
	
	$('#delete_selected_pins').on 'click', (event) ->
		if not confirm('Do you really want to delete these items?')
			return
		ids = ''
		for x in $.pagination_grid.g.getSelectedRows()
			if ids isnt ''
				ids += ','
			ids += $(x).attr('pinid')
		console.log(ids)
		$.ajax
			method: 'post',
			url: '/admin/pins/multiple_delete'
			data:
				'ids': ids,
			success: ->
				$.pagination_grid.g.load()
				return
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