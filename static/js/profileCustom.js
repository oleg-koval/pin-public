jQuery(function ($) {
    $(document).ready(function () {

        $(".userPic img").mouseenter(function () {
            $(".otherPics").css({'display':'block'});
        });
        $(".otherPics").mouseleave(function () {
            $(".otherPics").css({ 'display': 'none' });
        });
        $(".userPic").mouseleave(function () {
            $(".otherPics").css({ 'display': 'none' });
        });
    });
});