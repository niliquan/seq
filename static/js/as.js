$(document).ready(function(){
	
$('#session').login();

$('input[holder],textarea[holder]').placeholder();

$('input.input-error,textarea.input-error').keyup(
      function(){
      	$('.text-error',
      	$(this).removeClass('input-error').parent()).remove();});

$('#msg-link').eventPopup({url:'http://x.segmentfault.com/event',});

$('ul.meta-tags li a, ul.show-pop-tag li a.tag, a.tag').tagPopup('http://segmentfault.com/api/tag','#main');

$('#search .input-search').
        searchAutoComplete({url:'http://x.segmentfault.com/autocomplete?site=0',insertAfter:'#search',
                            searchUrl:'http://segmentfault.com/search',
                            askUrl:'http://segmentfault.com/ask',
                            ask:'#top-nav a.btn-regular'});
                   
$('a.msg-close',$('#msg-bar').fadeIn().sticky()).
               click(function(){$(this).parent().parent().fadeOut(function(){$(this).parent().remove();});return false;});
               
$('#drop-link').click(
                function(){var p=$(this).parent();
                if(p.hasClass('current'))
                {p.removeClass('current');$('.dropdown-menu',p).addClass('hidden');}
                else
                {p.addClass('current');$('.dropdown-menu',p).removeClass('hidden');}
                return false;});
                
$(document.body).click(
                function(e){var p=$('#drop-link-wrap');
                           if(0==$(e.target).parents('#drop-link-wrap').length){p.removeClass('current');
                           $('.dropdown-menu',p).addClass('hidden');}});
                           
if($('#ask').length>0)
              {$('#top-nav a.btn-regular').addClass('btn-disabled').click(function(){return false;});}
              
$('.tip-pop').each(function()
             {var t=$(this),str=t.data('tip');
             if(!!!str){return;}
             t.removeAttr('title');
             var parts=str.split(':');
             $(this).tipsy({'html':true,'gravity':parts.shift(),'fallback':parts.join(':')});});
             
if(login){$('#main').highlightTag({url:'http://x.segmentfault.com/tag/following'
                                 ,selector:'#content article .meta-tags li a, #user-question article .meta-tags li a',
                                  className:'q-highlight'});
          var accountInfo=$('#my-account .info');
          if(accountInfo.length>0){
          	accountInfo.animate({backgroundColor:'#9a4444',color:'#fff'},
                                  'slow',function(){$(this).animate({backgroundColor:'#d9edf7',color:'#326aa8'},'slow');}
                                        );}}
                                        
 else if(0==$('.auth-login,.session-form,.session-finished').length){
 	           if(1!=$.cookie('sfln_viewed')){$.cookie('sfln_viewed',1,{path:'/'});$.cookie('sfln_available',1,{path:'/'});}
 	           else if(1==$.cookie('sfln_available')){
 	           	         $('.i-cancel',$('.login-notify').css('bottom',-60).removeClass('hidden').animate({'bottom':0})).
 	           	         click(function(){$.cookie('sfln_available',0,{path:'/'});$(this).parents('.login-notify').animate({'bottom':-60},function(){$(this).remove();});
 	           	              return false;});}}});
  var _gaq=_gaq||[];_
  gaq.push(['_setAccount','UA-918487-8']);_
  gaq.push(['_trackPageview']);
  
  (function(){var ga=document.createElement('script');
              ga.type='text/javascript';
              ga.async=true;
              ga.src=('https:'==document.location.protocol?'https://ssl':'http://www')+'.google-analytics.com/ga.js';
              var s=document.getElementsByTagName('script')[0];s.parentNode.insertBefore(ga,s);})();