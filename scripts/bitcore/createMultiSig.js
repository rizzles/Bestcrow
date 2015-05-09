var bitcore = require("bitcore");

//var privateKey = new bitcore.PrivateKey();
var privateKey1 = bitcore.PrivateKey.fromWIF('L4vvPJDpmkaPcrNYnWTWSAJZD2smiogiUQMUzH4qRB7umDVY3t5w');
var wif1 = privateKey1.toWIF();
console.log('WIF1: ' + wif1);
var publicKey1 = privateKey1.toPublicKey('testnet');
console.log('Public Key1: '+publicKey1);
var pubAddress1 = publicKey1.toAddress('testnet');
console.log('Public Address1: '+pubAddress1);

console.log('');
//var privateKey2 = new bitcore.PrivateKey();
var privateKey2 = bitcore.PrivateKey.fromWIF('L4TK5ht6G7P8xjFb5ZbkRLZ77KU9Kk5w4wrieX6kGJcQPg2zaodZ');
var wif2 = privateKey2.toWIF();
console.log('WIF2: ' + wif2);
var publicKey2 = privateKey2.toPublicKey('testnet');
console.log('Public Key2: '+publicKey2);
var pubAddress2 = publicKey2.toAddress('testnet');
console.log('Public Address2: '+pubAddress2);


console.log('');
//var privateKey3 = new bitcore.PrivateKey();
var privateKey3 = bitcore.PrivateKey.fromWIF('L16UfdyUP67xUqGb2x4KP5MSmxhsMXQWmLTNbDTG41DfoiSZ7k7h');
var wif3 = privateKey3.toWIF();
console.log('WIF3: ' + wif3);
var publicKey3 = privateKey3.toPublicKey('testnet');
console.log('Public Key3: '+publicKey3);
var pubAddress3 = publicKey3.toAddress('testnet');
console.log('Public Address3: '+pubAddress3);

console.log('');
var p2shAddress = new bitcore.Address([publicKey1, publicKey2, publicKey3], 2);
console.log('P2SH Address: '+p2shAddress.toString());

