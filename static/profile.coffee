$('#file').change ->
  $('#form').submit()

  
$('#lolimage').click ->
  $('#form').attr('action', '/changeprofile')
  $('#file').click()


