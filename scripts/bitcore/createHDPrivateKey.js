var bitcore = require("bitcore");
var Mnemonic = require('bitcore-mnemonic');

var code = new Mnemonic();

console.log(code.toString());

var xpriv1 = code.toHDPrivateKey();
var hdPrivateKey = new bitcore.HDPrivateKey(code.toString());
var hdPublicKey = hdPrivateKey.hdPublicKey;

var address = new bitcore.Address(hdPublicKey.publicKey, bitcore.Networks.testnet);
console.log(address.toString());
var address = new bitcore.Address(hdPublicKey.publicKey, bitcore.Networks.testnet);
console.log(address.toString());
