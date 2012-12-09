 $(document).ready(function(){	 
   $("#followme").click(function(){
                    var uid=$("#followme").attr("data-uid");
                    alert(uid);
                           $.ajax({url:"/personfollow",async:false,data:{followemail:uid}});                     
                           $("#unfollowme").attr("display","block"); 
                           $("#followme").attr("display","none"); 
                                                                                                                                                 });                                                                                                                                                                                                                            
                                                         } );
                            