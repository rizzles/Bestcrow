var bitcore = require("bitcore");

//var privateKey = new bitcore.PrivateKey();
var privateKey = bitcore.PrivateKey.fromWIF('L4vvPJDpmkaPcrNYnWTWSAJZD2smiogiUQMUzH4qRB7umDVY3t5w');
var wif = privateKey.toWIF();
console.log('WIF: ' + wif);

var publicKey = privateKey.toPublicKey('testnet');
console.log('Public Key: '+publicKey);

var pubAddress = publicKey.toAddress('testnet');
console.log('Public Address: '+pubAddress);

if (bitcore.Address.isValid(pubAddress)) {
    console.log('Pub address is valid');
}

if (bitcore.Address.isValid(pubAddress), bitcore.Networks.testnet) {
    console.log('Pub address is valid on testnet');
}

if (bitcore.Address.isValid(pubAddress), bitcore.Networks.testnet, bitcore.Address.Pay2PubKeyHash) {
    console.log('Pub address is valid testnet PubKeyHash');
}

var address2 = privateKey.toAddress('testnet', 'script');
console.log("ADDRESS2: "+address2);



