category_count = 0
$('.loldongs').click ->
        category_id = $(this).attr('categoryid')
        if $(this).hasClass('selected')
                remove_category_from_user(category_id, $(this))
        else
                add_category_to_user(category_id, $(this))

add_category_to_user = (category_id, button) ->
        $.ajax "/register/api/users/me/category/#{category_id}/",
                        type: 'PUT'
                        dataType: 'json'
        button.addClass 'selected'
        category_count += 1
        if category_count > 2
                $('#continue_button').removeAttr('disabled')

remove_category_from_user = (category_id, button) ->
        $.ajax "/register/api/users/me/category/#{category_id}/",
                        type: 'DELETE'
                        dataType: 'json'
        button.removeClass 'selected'
        category_count -= 1
        if category_count < 3
                $('#continue_button').attr('disabled', 'disabled')

$("#continue_button").click ->
        window.location.href = 'after-signup/2'