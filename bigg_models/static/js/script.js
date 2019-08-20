/* global $ */

$(document).ready(function() {
  // Go to a new GitHub issue page and fill out some key info.
  $('#comment-link').click(function() {
    var url = ('https://github.com/SBRG/bigg_models/issues/new?body=' +
               encodeURIComponent('# Description of the issue\n\n\n\n# Page\n' +
                                  window.location.href + '\n# Browser\n' +
                                  window.navigator.userAgent))
    window.open(url, '_blank')
    return false;
  })

  // navbar position
  var navPos = $('.navbar').offset().top

  // fixed nav on scroll
  $(window).scroll(function() {
    var checkScrollPosition = $(this).scrollTop() >= navPos
    $('.navbar').css('position', checkScrollPosition ? 'fixed' : 'relative')
    $('body').css('padding-top', checkScrollPosition ? '72px' : '0px')
    $('#nav-title-background').css('visibility', checkScrollPosition ? 'hidden' : 'visible')
  })
})
