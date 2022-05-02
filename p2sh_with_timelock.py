#!/usr/bin/env python3

import bitcoin
import bitcoin.rpc
import sys
from bitcoin.core import b2x
from bitcoin.core.script import CScript,OP_CHECKLOCKTIMEVERIFY ,OP_DUP, OP_HASH160, OP_EQUALVERIFY,OP_CHECKSIG, OP_DROP
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress, CBitcoinAddress
from bitcoin.core import Hash160

# settning the network param to testnet
bitcoin.SelectParams('testnet')
def main(argv):
  
  
  # this script takes a p2pkh as input and a future time in block for when 
  # the fund may be spendt and then displays the p2sh address 
  # p2pkh address to send money to
  pubKey= argv[0]

  # will use OP_CLTV in order to make it unspendable on-chain too 
  # set a future where funds may be spent.
  # setting the timelock for when funds will be spendable

  timelock_cltv = argv[1]
  nLockTime = timelock_cltv
  
  # create redeem script
  redeem_script = CScript([nLockTime, OP_CHECKLOCKTIMEVERIFY,OP_DROP, OP_DUP, OP_HASH160, Hash160(pubKey), OP_EQUALVERIFY, OP_CHECKSIG])
  
  # Create locking script or scriptPubKey from redeem script
  txin_scriptPubKey = redeem_script.to_p2sh_scriptPubKey()
  print('scriptPubKey:',b2x(txin_scriptPubKey))
  #convert to P2SH to a base 58 and print it out
  txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
  print('Pay to:', str(txin_p2sh_address))


if __name__ == "__main__":
  if (len(sys.argv[1:]) == 2):
    pubKey = P2PKHBitcoinAddress.from_pubkey(sys.argv[1]).to_scriptPubKey()
    timestamp_in_blocks = int(sys.argv[2])
    main([pubKey, timestamp_in_blocks])
  elif(len(sys.argv[1:])==0):
    secret_key = CBitcoinSecret("Insert your privat key to generate from scratch")
    pubKey = secret_key.pub
    timelock = 481824 # Insert  timelock here
    address = P2PKHBitcoinAddress.from_pubkey(pubKey).to_scriptPubKey()
    main([pubKey,timelock])
  else:
    print('Too many arguments. Try with a P2PKH and timelock expressed in blocks')
