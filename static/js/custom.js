jQuery(function ($) {
    $(document).ready(function () {
        if ($("#mainPage").length !== 0) {

            //$('#pin-box-wrapper').css({ 'display': 'none' });
            setTimeout(function () {
                var arrPin = [], pinsCount = 0, pinWidth = [], pinPostArr = [];

                $('#pin-buf .pin').each(function () {
                    arrPin.push($(this));
                    pinWidth.push($(this).find('img:first-child').width());
                    if (pinWidth[pinsCount] == 0) {
                        arrPin[pinsCount].find('> a').css({ 'overflow': 'hidden', 'display': 'block', 'width': '200px' });
                    };
                    pinsCount++;
                });


                for (var i = 0; i < pinsCount; i++) {
                    $("#firstRow").append('<div class="pinRollItem">' + arrPin[i].html() + '</div>');
                };
                for (var i = 0; i < pinsCount; i++) {
                    $("#secondRow").append('<div class="pinRollItem">' + arrPin[i].html() + '</div>');
                };
                for (var i = 0; i < pinsCount; i++) {
                    $("#thirdRow").append('<div class="pinRollItem">' + arrPin[i].html() + '</div>');
                };
                for (var i = 0; i < pinsCount; i++) {
                    $("#fourthRow").append('<div class="pinRollItem">' + arrPin[i].html() + '</div>');
                };

                var rollRowCount = 0, posItemLeft = 0;
                $('#firstRow .pinRollItem').each(function () {
                    $(this).css({ 'left': posItemLeft + 'px' });
                    posItemLeft = posItemLeft + $(this).width() + 20;
                    rollRowCount++;
                });

                rollRowCount = 0; posItemLeft = 0;
                $('#secondRow .pinRollItem').each(function () {
                    $(this).css({ 'right': posItemLeft + 'px' });
                    posItemLeft = posItemLeft + $(this).width() + 20;
                    rollRowCount++;
                });

                rollRowCount = 0; posItemLeft = 0;
                $('#thirdRow .pinRollItem').each(function () {
                    $(this).css({ 'left': posItemLeft + 'px' });
                    posItemLeft = posItemLeft + $(this).width() + 20;
                    rollRowCount++;
                });

                rollRowCount = 0; posItemLeft = 0;
                $('#fourthRow .pinRollItem').each(function () {
                    $(this).css({ 'right': posItemLeft + 'px' });
                    posItemLeft = posItemLeft + $(this).width() + 20;
                    rollRowCount++;
                });
            }, 2000);
            $('#firstRow').animate({ left: ($('#firstRow').position().left - $('#firstRow').width()) + 'px' }, 50000);
            $('#secondRow').animate({ left: ($('#secondRow').position().left + $('#secondRow').width()) + 'px' }, 80000);
            $('#thirdRow').animate({ left: ($('#thirdRow').position().left - $('#thirdRow').width()) + 'px' }, 60000);
            $('#fourthRow').animate({ left: ($('#fourthRow').position().left + $('#fourthRow').width()) + 'px' }, 50000);
        };

        if ($("#inSess").length !== 0) {
            $("#mainPage").css({ 'display': 'none' });
            $("#mainForm").css({ 'display': 'none' });
            $('#pin-box-wrapper').css({ 'display': 'block' });
        };

        if ($("#menu1").length !== 0) {
            var menuCat = [], menuCatCount = 0, mcPoint = 0;
            $('#menu1 a').each(function () {
                menuCat.push($(this));
                menuCatCount++;
            });
            mcPoint = Math.round(menuCatCount / 3);

            for (var i = 0; i < menuCatCount; i++) {
                if (i < mcPoint) {
                    menuCat[i].addClass('mcFirstRow');
                } else {
                    if (i < mcPoint * 2) {
                        menuCat[i].addClass('mcSecondRow');
                    } else {
                        menuCat[i].addClass('mcThirdRow');
                    };
                };

            };
            $("#menu1 .mcFirstRow").wrapAll("<div class='inlineB mcBlock'></div>");
            $("#menu1 .mcSecondRow").wrapAll("<div class='inlineB mcBlock'></div>");
            $("#menu1 .mcThirdRow").wrapAll("<div class='inlineB mcBlock'></div>");
        };

    });


    $("#signShow").click(function () {
        $("#mainForm .signForm form").slideToggle("slow", function () {
            // Animation complete.
        });
        $("#signFb").slideToggle("slow", function () {
            // Animation complete.
        });
        if ($("#signShow p").html() == "Signup") {
            $("#signShow p").html("Social signup");
        } else {
            $("#signShow p").html("Signup");
        };

    });



    var $body = $("body");

    $(document).on({
        ajaxStart: function () { $body.addClass("loading"); },
        ajaxStop: function () { $body.removeClass("loading"); }
    });

});