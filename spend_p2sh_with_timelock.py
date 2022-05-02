#!/usr/bin/env python3
import sys
import requests


import bitcoin
import bitcoin.rpc
import sys
from bitcoin.core import *
from bitcoin.core.script import *
from bitcoin.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress, CBitcoinAddress
from bitcoin.core import Hash160
import logging

# Accept a future time (expressed in block height) and a private key; 
# to recreate the redeem sctipt as above to unlock the P2PKH part
# Accept a P2PKH address to get the funds from (the one created by the first
# script - this could be recreated but we want to pass to double check it!)



# settning the network param to testnet
bitcoin.SelectParams('testnet')

def main(argv):

  # initialising proxy connection to localhost
  proxy_connection = bitcoin.rpc.Proxy()
  
  sec_key = argv[0]
  # secret key to spend funds 
  p2sh_seckey = CBitcoinSecret(sec_key)
  p2sh_to_spend_from = CBitcoinAddress(argv[1])
  # check if given public key is equal to 
  recipient_address = P2PKHBitcoinAddress(argv[2])
  absolute_timelock = argv[3]

  txin_redeemScript = CScript([absolute_timelock, OP_CHECKLOCKTIMEVERIFY,OP_DROP, OP_DUP, OP_HASH160, Hash160(p2sh_seckey.pub), OP_EQUALVERIFY, OP_CHECKSIG])
  
  txin_scriptPubKey = txin_redeemScript.to_p2sh_scriptPubKey()
  txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
  print('To scrippubkey:',str(txin_p2sh_address))


  # importing utxo from the spending address
  utxos = proxy_connection.listunspent(addrs=[p2sh_to_spend_from])
  if not utxos:
    sys.exit(f'Error: unspent transactions, please send funds to {p2sh_to_spend_from} or import address with bitcoin-cli importaddress "{p2sh_to_spend_from})')
  
  unspent = sorted(proxy_connection.listunspent(addrs=[p2sh_to_spend_from]), key=lambda x: hash(x['amount']))

  txins=[]
  
  amount = 0
  index = 0
  # generate tx in
  for utxo in utxos:
    utxo = utxos[index]
    txin = CMutableTxIn(utxo['outpoint'], nSequence=0xfffffffe)
    txins.append(txin)
    
    # calulating total value in 
    amount += int(utxo['amount'])
    index+=1
  

  # Getting tx rate per kb from api for testnet
  fee_rate = requests.get('https://api.blockcypher.com/v1/btc/test3').json()
  FEE_PER_BYTE = fee_rate['medium_fee_per_kb']/1000


  txout = CMutableTxOut(amount,recipient_address.to_scriptPubKey())
  tx = CMutableTransaction(txins, [txout],nLockTime=absolute_timelock)
  tx.vout[0].nValue = int(amount - len(tx.serialize()) * FEE_PER_BYTE)
  print('\n------------------------')
  print('raw unsigned transaction:',b2x(tx.serialize()))
  print('------------------------')
  

  # sign the txins induvidually
  # signing transaction with sig, pubkey and redeemscript
  i = 0
  for txin in txins:
    sighash = SignatureHash(txin_redeemScript, tx, i, SIGHASH_ALL)
    sig = p2sh_seckey.sign(sighash) + bytes([SIGHASH_ALL])
    txin.scriptSig = CScript([sig, p2sh_seckey.pub, txin_redeemScript])
    # Veifying the script
    VerifyScript(txin.scriptSig, txin_scriptPubKey, tx, i, (SCRIPT_VERIFY_P2SH,))
    i+=1


  print('------------------------')
  CheckTransaction(tx)
  print('Transaction id:',b2lx(tx.GetTxid()))
  print('------------------------')
  spend_txid = proxy_connection.sendrawtransaction(tx)
  print(b2x(tx.serialize()))
  print("txid: {}".format(b2lx(spend_txid)))
  
if __name__ == "__main__":
  # Insert your privatekey
  private_key = ""
  # insert your p2sh to spend from
  p2sh = ""
  # insert timelock
  absolute_timelock = None
  # insert recipient address
  p2pkh = ""

  

  main([private_key,p2sh,p2pkh, absolute_timelock])
