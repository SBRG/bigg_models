$( document ).ready(function() {

	var navPos = $('.navbar').offset().top;

	$(window).scroll(function(){
		var checkScrollPosition = $(this).scrollTop() >= navPos;
		var setPos = checkScrollPosition ? 'fixed' : 'relative' ;
		$('.navbar').css({position: setPos});
	});
	
	$('.carousel').carousel({interval: 9000});
		
	$( "#showmodels" ).click(function () {
			
		if ( $( ".btn-group-vertical" ).is( ":hidden" ) ) {
			$( ".btn-group-vertical" ).slideDown( "slow" );
		} else {
			$( ".btn-group-vertical" ).hide();
		}
	});
	
	var models = new Bloodhound({
  datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
  queryTokenizer: Bloodhound.tokenizers.whitespace,
   prefetch: {
    // url points to a json file that contains an array of country names, see
    // https://github.com/twitter/typeahead.js/blob/gh-pages/data/countries.json
    url: 'http://localhost:8888/api/models',
    // the json file contains an array of strings, but the Bloodhound
    // suggestion engine expects JavaScript objects so this converts all of
    // those strings
    filter: function(list) {
      return $.map(list, function(model) { return { name: model }; });
   }
   }
   });
   models.initialize();
	$('#multiple-datasets .typeahead').typeahead(null, {
  name: 'models',
  displayKey: 'name',
  // `ttAdapter` wraps the suggestion engine in an adapter that
  // is compatible with the typeahead jQuery plugin
  source: models.ttAdapter()
});
});


			