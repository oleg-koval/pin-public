$email = $('#email')
$username = $('#username')
$password = $('#password')

$emailInfo = $('<div/>').insertAfter($email).addClass('faded pad-bottom invis')
$usernameInfo = $('<div/>').insertAfter($username).addClass('faded pad-bottom').html('Your URL: <span class="link">http://mypinnings.com/USERNAME</span>')
$passwordInfo = $('<div/>').insertAfter($password).addClass('faded pad-bottom invis').text('Your password is encrypted. For example, (abc123 shows up as ny203cyaca2 in our database.)')


$email.blur ->
  e = $email.val()
  if not e
    $emailInfo.text('Please enter an email!')
  else
    $.get '/reg-checkemail', {e: e}, (data) ->
      if data == 'taken'
        $emailInfo.show()
        $emailInfo.html('<span class="red">This email is already registered. Want to <a href="/login">login</a> or <a href="/recover_password">recover your password</a></span>')
      else
        $emailInfo.hide()
        $emailInfo.html('')

timer = null
taken = false

lolfunc = ->
  $usernameInfo.show()

  u = $username.val()
  if not taken
    $usernameInfo.html('Your URL: <span class="link">http://mypinnings.com/' + u)
 
  if timer isnt null
    clearInterval timer
    timer = null

  if u
    timer = setInterval (->
      $.get '/reg-checkuser', {u: u}, (data) ->
        if data == 'taken'
          $usernameInfo.html('Sorry, that username is taken: <span class="link">http://mypinnings.com/' + u + '</span>')
          taken = true
        else
          taken = false
          $usernameInfo.html('Your URL: <span class="link">http://mypinnings.com/' + u + '</span>')
    ), 500

$username.on 'input', lolfunc
$username.blur lolfunc
