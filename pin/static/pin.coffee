for i in [1..5]
    span = $('<span/>')
        .addClass('rating')
        .attr('data-rating', i)
        .html('<i class="fa fa-star"></i>')

    span.hover (->
        rating = $(this).attr('data-rating')
        for i in [0..rating]
            $('.rating').each ->
                $(this).removeClass 'selected'
                if parseInt($(this).attr('data-rating')) <= i
                    $(this).addClass 'selected'
    ), (->
        $('.rating').removeClass 'selected'
    )

    span.click ->
        rating = $(this).attr('data-rating')
        $.getJSON '/rate/' + window.pinId + '/' + rating, (data) ->
            if data.error?
                alert data.error
                return

            if not data.rating?
                alert 'rating not given'
                return

            $('#rating').text data.rating + '/5'
            $('#ratings').empty()

    $('#ratings').append(span)
