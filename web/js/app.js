//$(document).foundation();
var s;

var entityMap = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': '&quot;',
    "'": '&#39;',
    "/": '&#x2F;'
};

function escapeHtml(string) {
    return String(string).replace(/[&<>"'\/]/g, function (s) {
        return entityMap[s];
    });
}

$("input").on("click", function() {
	this.select();
});

function balance(address) {
    $.get("/balance/"+address, function(data) {
        data = JSON.parse(data);
        $(".balance").html(data.balance+" BTC");
        $(".unconfirmed").html(data.unconfirmed+" BTC");
    });
}

var Seller = {
	settings: {
		sellerurlhash: "",
		multisigaddress: "",
	},

	init: function(sellerurlhash, multisigaddress) {
		this.settings.sellerurlhash = sellerurlhash;		
		this.settings.multisigaddress = multisigaddress;		
		s = this.settings;		
		this.bindUIActions();
	},

	bindUIActions: function() {
        $(".leavecomment").on("click", function(e) {
            e.preventDefault();
            var c = $("input[name='comment']").val();
            if (!c) {
                $(".leavecomment").blur();
                return;
            }

            c = escapeHtml(c);
            $.post("/comment/{{escrow['sellerurlhash']}}", {"comment":c, "author":"seller"}, function(data) {
                console.log(data);
                $(".commentsbody").append('<div class="small-10 small-offset-2 medium-8 medium-offset-4 youcomment columns"><small>just now</small><p class="text">'+c+'</p></div>'); 
            }).fail(function(){
                console.log("Failed");
            }).done(function() {
                $("input[name='comment']").val('');
            });
        });

		$(".refresh").on("click", function() {
			$(".refresh").velocity({
				rotateZ: "360deg",
			}, {
				begin: function() {
                    $(".balance").html("--- BTC");
                    balance(s.multisigaddress);
                },
				complete: function() {
                    $(".refresh").velocity('stop').velocity({rotateZ:'0deg'});
                }
			});
		});

		$(".releasefunds").on("click", function(e) {
			e.preventDefault();
			$(".areyousure").velocity({
				opacity: 1,
				top: "0px"
			}, {
				display: "block"
			});
		});

		$(".areyousurecancel").on("click", function(e) {
			e.preventDefault();
			$(".areyousure").velocity({
				opacity: 0,
				top: "-280px"
			}, {
				display: "none"
			});
		});

	},
};

var Buyer = {
	settings: {
		buyerurlhash: "",
		multisigaddress: "",
	},

	init: function(buyerurlhash, multisigaddress) {
		this.settings.buyerurlhash = buyerurlhash;		
		this.settings.multisigaddress = multisigaddress;		
		s = this.settings;		
		this.bindUIActions();
	},

	bindUIActions: function() {
        $(".leavecomment").on("click", function(e) {
            e.preventDefault();
            $(".emptycomment").remove();
		    var c = $("input[name='comment']").val();
		    if (!c) {
		        $(".leavecomment").blur();
		        return;
		    }

		    c = escapeHtml(c);
		    $.post("/comment/"+s.buyerurlhash, {"comment":c, "author":"buyer"}, function(data) {
		        $(".commentsbody").append('<div class="small-10 small-offset-2 medium-8 medium-offset-4 youcomment columns"><small>just now</small><p class="text">'+c+'</p></div>'); 
		    }).fail(function(){
		        console.log("Failed");
		    }).done(function() {
		        $("input[name='comment']").val('');
		    });
        });

		$(".refresh").on("click", function() {
			$(".refresh").velocity({
				rotateZ: "360deg",
			}, {
                begin: function() {
                    $(".balance").html("--- BTC");
                    balance(s.multisigaddress);
                },
                complete: function() {
                    $(".refresh").velocity('stop').velocity({rotateZ:'0deg'});
                }
			});
		});

        $(".releasefunds").on("click", function(e) {
            e.preventDefault();
            $(".completed").addClass("flip10");
            setTimeout(function() {
                $(".completed").removeClass("flip10").addClass("flip90");
            }, 50);
            setTimeout(function() {
                $(".completed").removeClass("flip90"); 
                $(".completed .btcbg").hide();
                $(".areyousure").show();                    
            }, 150);
        });

        $(".areyousurecancel").on("click", function(e) { 
            e.preventDefault();
            $(".completed").addClass("flip10");
            setTimeout(function() {
                $(".completed").removeClass("flip10").addClass("flip90");
            }, 50);
            setTimeout(function() {
                $(".completed").removeClass("flip90"); 
                $(".completed .btcbg").show();
                $(".areyousure").hide();                    
            }, 150);
        });

        $(".opendispute").on("click", function(e) {
            e.preventDefault();
            $(".completed").addClass("flip10");
            setTimeout(function() {
                $(".completed").removeClass("flip10").addClass("flip90");
            }, 50);
            setTimeout(function() {
                $(".completed .btcbg").hide();                    
                $(".completed").removeClass("flip90"); 
                $(".dispute").show();                    
            }, 150);
        });   

        $(".disputecancel").on("click", function(e) { 
            e.preventDefault();
            $(".completed").addClass("flip10");
            setTimeout(function() {
                $(".completed").removeClass("flip10").addClass("flip90");
            }, 50);
            setTimeout(function() {
                $(".dispute").hide();                                        
                $(".completed .btcbg").show();                    
                $(".completed").removeClass("flip90"); 
            }, 150);
        });

		$("#fileupload").on("change", function() {
			var nfiles = this.files.length;
			$(".file-list").html("");
			for (var fileid = 0; fileid < nfiles; fileid++ ) {
				var filename = this.files[fileid].name;
				$(".file-list").append("<li>"+filename+"</li>");

			}
		});
	},

};
