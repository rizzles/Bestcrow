var $ = require('jquery');
var _ = require('underscore');
var Backbone = require('backbone');
var LocalStorage = require('backbone.localstorage');

$("input").on("click", function() {
	this.select();
});

// Navigation side menu
var NavModel = Backbone.Model.extend({
	defaults: {
		active: 0,
		completed: 0,
	}
});

var NavView = Backbone.View.extend({
	tagName: 'div',
	className: 'flex-nav',
	events: {
		//'click a': 'addActive',
	},
	addActive: function(e) {
		$(".flex-nav a").removeClass("active");
		$(e.target).addClass('active');
	},
	navTemplate: _.template($("#navTemplate").html()),
	initialize: function() {
		this.collection = escrowsCollection;
		this.listenTo(this.collection, 'add', this.update);
		this.listenTo(this.collection, 'change', this.update);
		this.listenTo(this.collection, 'destroy', this.update);
		this.render();
	},
	render: function() {
		var active = 0;
		var completed = 0
		this.collection.each(function(EscrowModel) {
			if (EscrowModel.get('status') === 'active') {
				active++;
			} else if (EscrowModel.get('status') === 'completed') {
				completed++;
			}
		});
		this.model.set('active', active);
		this.model.set('completed', completed);
		this.$el.html(this.navTemplate(this.model.toJSON()));
		$("#flex-nav-container").html(this.el);
		return this;
	},
	update: function() {
		var target = $(".active");
		var num = $(".flex-nav a").index(target);
		var active = 0;
		var completed = 0;
		this.collection.each(function(EscrowModel) {
			if (EscrowModel.get('status') === 'active') {
				active++;
			} else if (EscrowModel.get('status') === 'completed') {
				completed++;
			}
		});
		this.model.set('active', active);
		this.model.set('completed', completed);
		this.$el.html(this.navTemplate(this.model.toJSON()));
		$(".flex-nav a").eq(num).addClass("active");
	},
	setActive: function(num) {
		$(".flex-nav a").removeClass("active");
		$(".flex-nav a").eq(num).addClass("active");
	}
});




// Index main view
var IndexModel = Backbone.Model.extend({
	defaults: {
	}
});

var IndexView = Backbone.View.extend({
	tagName: 'div',
	className: 'flex-getstarted',
	getJoinHash: function(value, form) {
		var link = value;
		var buyerseller = null;
		var str = link.search("/join/");
		if (str > 0) {
			link = link.substring(str+6, str.length);
		}

		str = link.search("seller/");
		if (str > 0) {
			buyerSeller = "seller";
		} else {
			buyerSeller = "buyer";
		};

		router.navigate('join/'+buyerSeller+"/"+link, {trigger: true});
	},
	events: {
		"submit": function(e) {
			e.preventDefault(); 
			e.stopPropagation();
			var form = $("form")
			var value = $("input").val();
			this.getJoinHash(value, form);
		}
	},
	indexTemplate: _.template($("#indexTemplate").html()),
	initialize: function() {
		this.render();
	},
	render: function() {
		this.$el.html(this.indexTemplate());
		$(".flex-main").html(this.el);	
	}
});



// BuyerSeller
var BuyerSellerModel = Backbone.Model.extend({
	defaults: {
	}
});

var BuyerSellerView = Backbone.View.extend({
	tagName: 'div',
	className: 'flex-getstarted',
	events: {
		'click .secondary': 'buyer',
		'click .primary': 'seller'
	},
	buyerSellerTemplate: _.template($("#buyerSellerTemplate").html()),
	initialize: function() {
		this.render();
	},
	render: function() {
		this.$el.html(this.buyerSellerTemplate());
		$(".flex-main").html(this.el);
	},
	buyer: function() {
		var subKey = settingsCollection.getSubKey();
		var mnemonic = settingsCollection.getMnemonic();
		var pubKey = bitcoin.generatePublicHDKey(mnemonic, subKey);
		var escrowModel = new EscrowModel({'pubKey':pubKey, 'buyerSeller':'buyer', 'subKey':subKey});
		// makes PUT request to server
		escrowModel.save({}, {
            success: function(model, response) {
                console.log('success! ' + JSON.stringify(response));
                escrowModel.set('hash', response.escrowhash);
                escrowModel.set('joinhash', response.joinhash);
                escrowModel.set('id', response.escrowhash);
                escrowsCollection.create(escrowModel);
                router.navigate('escrow/'+escrowModel.get('id'), {trigger: true})
            },
            error: function(model, response) {
                console.log('error! ' + JSON.stringify(response))
            }
        });
	},
	seller: function() {
		var subKey = settingsCollection.getSubKey();
		var mnemonic = settingsCollection.getMnemonic();
		var pubKey = bitcoin.generatePublicHDKey(mnemonic, subKey);
		var escrowModel = new EscrowModel({'pubKey':pubKey,'buyerSeller':'seller', 'subKey':subKey});
		// makes PUT request to server
		escrowModel.save({}, {
            success: function(model, response) {
                console.log('success! ' + JSON.stringify(response));
                escrowModel.set('hash', response.escrowhash);
                escrowModel.set('joinhash', response.joinhash);
                escrowModel.set('id', response.escrowhash);
                escrowsCollection.create(escrowModel);
                router.navigate('escrow/'+escrowModel.get('id'), {trigger: true})
            },
            error: function(model, response) {
                console.log('error! ' + JSON.stringify(response))
            }
        });
	}
});


// Join from link the buyer sent you
var JoinModel = Backbone.Model.extend({
	urlRoot: "http://localhost/api/join",
	defaults: {
		joinHash: null,
		buyerSeller: null
	}
});

var JoinView = Backbone.View.extend({
	tagName: 'div',
	className: 'flex-content',
	events: {

	},
	initialize: function() {
		this.render();
	},
	render: function(joinHash, buyerSeller) {
		console.log("JOIN VIEW");
		console.log(this.model.urlRoot);
		var subKey = settingsCollection.getSubKey();
		var mnemonic = settingsCollection.getMnemonic();
		this.model.set('pubKey', bitcoin.generatePublicHDKey(mnemonic, subKey));

		var escrowModel = new EscrowModel({'pubKey':this.model.get('pubKey'),'buyerSeller':this.model.get('buyerSeller'), 'subKey':subKey, 'joinhash':this.model.get('joinHash')});

		this.model.save({}, {
			success: function(model, response) {
				console.log('success!! ' + JSON.stringify(response));
				escrowModel.set('hash', response.escrowhash);
				escrowModel.set('id', response.escrowhash);
				escrowModel.set('multisigaddress', response.multisigaddress);
				escrowsCollection.create(escrowModel);
				router.navigate('escrow/'+escrowModel.get('id'), {trigger: true})
			},
            error: function(model, response) {
                console.log('error! ' + JSON.stringify(response))
            }
		})
	}
});

var BackupModel = Backbone.Model.extend({
	defaults: {
		mnemonic:null
	}
});

var BackupView = Backbone.View.extend({
	tagName: 'div',
	model: BackupModel,
	backupTemplate: _.template($("#backupTemplate").html()),
	initialize: function() {
		this.render();
	},
	render: function() {
		this.$el.html(this.backupTemplate(this.model.toJSON()));
		$(".flex-main").html(this.el);
	}
});

var RecoverModel = Backbone.Model.extend({
	defaults: {
	}
});

var RecoverView = Backbone.View.extend({
	tagName: 'div',
	events: {
		'submit': 'startRecovery',
	},
	model: RecoverModel,
	recoverTemplate: _.template($("#recoverTemplate").html()),
	initialize: function() {
		this.render();
	},
	render: function() {
		this.$el.html(this.recoverTemplate());
		$(".flex-main").html(this.el);
	},
	startRecovery: function(e) {
		e.preventDefault(); 
		e.stopPropagation();
		console.log("starting to recover");
	}
});



// Settings
var SettingsModel = Backbone.Model.extend({
	defaults: {
		mnemonic: null,
		subKey: 0
	},
});

var SettingsView = Backbone.View.extend({
	tagName: 'div',
	model: SettingsModel,
	initialize: function() {
	}
});

var SettingsCollection = Backbone.Collection.extend({
	model: SettingsModel,
	localStorage: new LocalStorage("betasettings4"),
	checkSettings: function() {
		var settingsModel = this.at(0);
		if (typeof settingsModel != 'undefined') {
			console.log(settingsModel.get('mnemonic'));
			console.log(settingsModel.get('subKey'));
		} else {
			var settingsModel = new SettingsModel();
			var mnemonic = bitcoin.getMnemonicString();
			settingsModel.set('mnemonic', mnemonic.toString());
			settingsModel.set('subKey', 0);
			this.add(settingsModel);
			settingsModel.save();
		}
	},
	getMnemonic: function() {
		var settingsModel = this.at(0);
		return settingsModel.get('mnemonic');
	},
	getSubKey: function() {
		console.log("updating subkey");
		var settingsModel = this.at(0);
		var subKey = settingsModel.get('subKey')
		settingsModel.set('subKey',subKey+1);
		settingsModel.save();
		return subKey;
	}
});

// Escrow
var EscrowModel = Backbone.Model.extend({
	urlRoot: function() {
		return 'http://localhost/api/'+this.get('buyerSeller');
	},
	//localStorage: new LocalStorage("beta4"),
	defaults: {
		pubKey: null,
		subKey: null,
		hash: null,
		buyerSeller: null,
		status: 'active',
		joinhash: null,
		multisigaddress: null,
		sellerpayoutaddress: null,
		buyerpayoutaddress: null,
		balance: null,
		unconfirmed: null,
		buyerstartedescrow: null,
		sellerstartedescrow: null,
	},
	newURLRoot: function() {
		return "fuck"+this.get('buyerSeller');
	},
	validate: function(attrs, options) {
		if (!attrs.pubKey) {
			alert("no pub key");
		}
	}
});

var EscrowView = Backbone.View.extend({
	tagName: 'div',
	className: 'flex-content',
	model: EscrowModel,
	events: {
		"click .release" : "complete",
		"click .dispute" : "complete"
	},
	escrowTemplate: _.template($("#escrowTemplate").html()),
	initialize: function() {
		this.collection = escrowsCollection;
		this.render();
	},
	render: function() {
		var _this = this
		this.model.newURLRoot();
		//this.model.urlRoot = this.model.urlRoot+"/"+this.model.get('buyerSeller');
		this.model.fetch({ ajaxSync: true,
			success: function(model, response) {
				console.log('success! ' + JSON.stringify(response));
				_this.model.set('joinhash', response.joinurlhash);
				_this.model.set('multisigaddress', response.multisigaddress);
				_this.model.set('buyerpayoutaddress', response.buyerpayoutaddress);
				_this.model.set('sellerpayoutaddress', response.sellerpayoutaddress);
				_this.model.set('balance', response.balance);
				_this.model.set('unconfirmed', response.unconfirmed);
				_this.model.set('buyerstartedescrow', response.buyerstartedescrow);
				_this.model.set('sellerstartedescrow', response.sellerstartedescrow);				
				_this.$el.html(_this.escrowTemplate(_this.model.toJSON()));
				$(".flex-main").html(_this.el);
			},
            error: function(model, response) {
                console.log('error! ' + JSON.stringify(response))
            }
		});
	},
	complete: function(e) {
		e.preventDefault();
		e.stopPropagation();
		this.model.set('status', 'completed');
		this.model.save();
		router.navigate('completeescrows', {trigger: true})
	}
});

var ActiveEscrowView = Backbone.View.extend({
	tagName: 'div',
	className: 'flex-table-row',
	model: EscrowModel,
	events: {
		//"click" : "update",
	},
	activeEscrowTemplate: _.template($('#activeEscrowTemplate').html()),
	render: function() {
		this.$el.html(this.activeEscrowTemplate(this.model.toJSON()));
		return this;
	},
	update: function() {
		this.model.set('status', 'completed');
		this.model.save();
		this.remove();
	}
});

var CompletedEscrowView = Backbone.View.extend({
	tagName: 'div',
	className: 'flex-table-row',
	model: EscrowModel,
	events: {
		"click .last" : "clear",
	},
	completedEscrowTemplate: _.template($('#completedEscrowTemplate').html()),
	render: function() {
		this.$el.html(this.completedEscrowTemplate(this.model.toJSON()));
		return this;
	},
	clear: function() {
		var _this = this;
		this.$el.addClass('hide');
		setTimeout(function() {_this.model.destroy();_this.remove()}, 200);
	},
});

var EscrowsCollection = Backbone.Collection.extend({
	model: EscrowModel,
	urlRoot: 'http://localhost/api',
	localStorage: new LocalStorage("beta4"),
});

var ActiveEscrowsView = Backbone.View.extend({
	tagName: 'div',
	className: 'flex-table',
	initialize: function() {
		this.collection = escrowsCollection;
	},
	activeEscrowsTableTemplate: _.template($('#activeEscrowsTemplate').html()),
	render: function() {
		var _this = this;
		this.$el.html(this.activeEscrowsTableTemplate());
		this.collection.each(function(EscrowModel) {
			if (EscrowModel.get('status') === 'active') {
				var activeEscrowView = new ActiveEscrowView({model: EscrowModel});
				activeEscrowView.render();
				_this.$el.append(activeEscrowView.el);
			}
		});
		$(".flex-main").html(this.el);	
		return this;
	}
});

var CompletedEscrowsView = Backbone.View.extend({
	tagName: 'div',
	className: 'flex-table',
	initialize: function() {
		this.collection = escrowsCollection;
	},
	completedEscrowsTableTemplate: _.template($('#completedEscrowsTemplate').html()),
	render: function() {
		var _this = this;
		this.$el.html(this.completedEscrowsTableTemplate());
		this.collection.each(function(EscrowModel) {
			if (EscrowModel.get('status') === 'completed') {
				var completedEscrowView = new CompletedEscrowView({model: EscrowModel});
				completedEscrowView.render();
				_this.$el.append(completedEscrowView.el);
			}
		});
		$(".flex-main").html(this.el);
		return this
	}
});



var Router = Backbone.Router.extend({ 
  	routes: {
    	"": "index",
    	"buyerseller": "buyerseller",
    	"join/:buyerSeller/:hash": "join",
    	"activeescrows": "activeescrows",
    	"completeescrows": "completeescrows",
    	"backup": "backup",
    	"recover": "recover",
    	"escrow/:hash": "escrow",
  	},
  	index: function() {
  		console.log("index");
  		navView.setActive(1);
  		var indexView = new IndexView();
  	},
  	backup: function() {
  		navView.setActive(4);
  		var backupModel = new BackupModel({'mnemonic':settingsCollection.getMnemonic()});
  		var backupView = new BackupView({'model':backupModel});
  	},
 	recover: function() {
 		navView.setActive(5);
  		console.log("recover");
  		var recoverView = new RecoverView();
  	},
  	buyerseller: function() {
  		console.log("buyerseller");  		
  		var buyerSellerView = new BuyerSellerView();
  	},
  	join: function(buyerSeller, joinHash) {
  		var joinModel = new JoinModel({joinHash:joinHash, buyerSeller: buyerSeller});
  		var joinView = new JoinView({'model':joinModel});
  	},
  	activeescrows: function() {
  		console.log("active"); 
  		navView.setActive(2);  		
  		activeEscrowsView.render();
  	},
  	completeescrows: function() {
  		console.log("complete");
  		navView.setActive(3);   		  		
  		completedEscrowsView.render();
  	},
  	escrow: function(escrowHash) {
  		console.log("Escrow Hash "+escrowHash);
		navView.setActive(2);
  		var escrowModel = escrowsCollection.get(escrowHash);
  		var escrowView = new EscrowView({'model':escrowModel});
  	}
});

var escrowsCollection = new EscrowsCollection();
escrowsCollection.fetch();

var navModel = new NavModel();
var navView = new NavView({model:navModel});
var activeEscrowsView = new ActiveEscrowsView();
var completedEscrowsView = new CompletedEscrowsView();

//var settingsModel = new SettingsModel();
//var settingsView = new SettingsView({model:settingsModel});
var settingsCollection = new SettingsCollection();
settingsCollection.fetch();
settingsCollection.checkSettings();

var router = new Router();
Backbone.history.start();

/*
var form = document.getElementById("joinform");
form.addEventListener("submit", function (event) {
	event.preventDefault();			

	var link = document.getElementById("joinlink").value;
	var str = link.search("/join/");

	if (str > 0) {
		link = link.substring(str+6, str.length);
	}

	console.log("LINK "+link);

	var hiddenField = document.createElement("input");
	hiddenField.setAttribute("type", "hidden");
		hiddenField.setAttribute("name", 'link');
	hiddenField.setAttribute("value", link);
	form.appendChild(hiddenField);

	form.submit();
});


function convertStringToArrayBufferView(str)
{
    var bytes = new Uint8Array(str.length);
    for (var iii = 0; iii < str.length; iii++) 
    {
        bytes[iii] = str.charCodeAt(iii);
    }

    return bytes;
}



var data = "QNimate";
var keys = window.localStorage.getItem('keys');
keys = JSON.parse(keys);
console.log(keys.pubAddress);

var promise = crypto.subtle.digest({name: "SHA-256"}, convertStringToArrayBufferView(data));
*/