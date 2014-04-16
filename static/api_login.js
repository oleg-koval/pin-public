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
            // window.location = '/next/page';
        });
    });
});
