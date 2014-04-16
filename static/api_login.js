var ajax_login = function(auth_data){
    $.cookie("seriesid", auth_data.seriesid);
    $.cookie("logintoken", auth_data.logintoken);
    $.cookie("user_id", auth_data.user_id);
    window.location = '/';
};

$(document).ready(function(){
    $("#login").click(function(evnt){
        evnt.preventDefault();
        var url = "/api/auth";
        var data = {
            "email": $("#email").val(),
            "password": $("#pwd").val()
        };
        $.post(url, data, function(response){
            if (response.status == 200){
                var response_data = response.data;
                var seriesid = response.csid_from_server;
                var logintoken = response_data.token;
                var user_id = response_data.user_id;
                var auth_data = {
                    "seriesid": seriesid,
                    "logintoken": logintoken,
                    "user_id": user_id
                }
                ajax_login(auth_data);
            }
            else{
                if ($(".notice").length == 0){
                    $("form").prepend("<div class='notice'></div>").fadeIn();
                }
                $(".notice").text(response.error_code);
            }
        });
    });
});
