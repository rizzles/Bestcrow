var bitcore = require("bitcore");
var http = require("http");

var privateKey = bitcore.PrivateKey.fromWIF('L4vvPJDpmkaPcrNYnWTWSAJZD2smiogiUQMUzH4qRB7umDVY3t5w');
var wif = privateKey.toWIF();
console.log('WIF: ' + wif);

var publicKey = privateKey.toPublicKey('testnet');
console.log('Public Key: '+publicKey);

var pubAddress = publicKey.toAddress('testnet');
console.log('Public Address: '+pubAddress);

var options = {
    host: "127.0.0.1",
    path: "/api/addr/"+pubAddress+"/utxo",
    port: 3001,
    method: "GET"
}

var req = http.get(options, function(res) {
    console.log('STATUS: '+res.statusCode);
    console.log('HEADERS: '+JSON.stringify(res.headers));
    
    bodyChunks = [];
    res.on('data', function(chunk) {
	bodyChunks.push(chunk);
    });

    res.on('end', function() {
	var body = Buffer.concat(bodyChunks);
	var obj = JSON.parse(body);
	console.log('BODY: '+body);
	console.log('UNSPENT OUTPUTS: '+body);
    });

    res.on('error', function(e) {
	console.log("ERROR: "+e.message);
    });
});

