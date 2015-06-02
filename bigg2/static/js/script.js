$(document).ready(function() {
    // clickable table rows
    $(".clickable-row").click(function() {
	    window.document.location = $(this).attr("href");
    });
    
    // submit buttons
    $("#submit").click(function(event) {
	    event.preventDefault();
		var email = $.trim($("input[name='email']").val()),
		    comments = $.trim($("textarea[name='comments']").val()),
		    type = $.trim($("select[name='type']").val()),
            error = null;
        if (email == '' || email.indexOf('@') == -1) error = 'Please enter an email address.';
        else if (comments.length < 10) error = 'Please enter a descriptive comment.';
        if (error) {
	        $('#message-container').html(
                '<div class="alert alert-danger alert-dismissible" role="alert"> ' +
		            '<button type="button" class="close" data-dismiss="alert" aria-label="Close"> ' +
                    '<span aria-hidden="true">&times;</span></button>' +
                    error + '</div>');
            return;
        }
	    $.post("/submiterror", {email: email, comments: comments, type: type})
            .done(function(data) {
	            $('#message-container').html(
                    '<div class="alert alert-success alert-dismissible" role="alert"> ' +
		                '<button type="button" class="close" data-dismiss="alert" aria-label="Close"> ' +
                        '<span aria-hidden="true">&times;</span></button>' +
                        'Thank you for your submission. If you have any further ' +
                        'questions, please contact Zachary King (zaking@ucsd.edu).' +
                        '</div>');
            })
            .fail(function() {
	            $('#message-container').html(
                    '<div class="alert alert-danger alert-dismissible" role="alert"> ' +
		                '<button type="button" class="close" data-dismiss="alert" aria-label="Close"> ' +
                        '<span aria-hidden="true">&times;</span></button>' +
                        'The form could not be submitted. Please try again later.' +
                        '<div style="font-family: monospace">' +
                        '<br/>' +
                        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;FAIL&nbsp;WHALE!<br/>' +
                        '<br/>' +
                        'W&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;W&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;W&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br/>' +
                        'W&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;W&nbsp;&nbsp;W&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;W&nbsp;&nbsp;&nbsp;&nbsp;<br/>' +
                        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\'.&nbsp;&nbsp;W&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br/>' +
                        '&nbsp;&nbsp;.-""-._&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\\&nbsp;\\.--|&nbsp;&nbsp;<br/>' +
                        '&nbsp;/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"-..__)&nbsp;.-\'&nbsp;&nbsp;&nbsp;<br/>' +
                        '|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br/>' +
                        '\\\'-.__,&nbsp;&nbsp;&nbsp;.__.,\'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br/>' +
                        '&nbsp;`\'----\'._\\--\'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br/>' +
                        'VVVVVVVVVVVVVVVVVVVVV<br/>' +
                        '</div></div>');
	        });
    });
    
    // navbar position
    var navPos = $('.navbar').offset().top;

    // fixed nav on scroll
    $(window).scroll(function() {
	    var checkScrollPosition = $(this).scrollTop() >= navPos;
	    $('.navbar').css('position', checkScrollPosition ? 'fixed' : 'relative');
	    $('body').css('padding-top', checkScrollPosition ? '72px' : '0px');
	    $('#nav-title-background').css('visibility', checkScrollPosition ? 'hidden' : 'visible');
    });
});
