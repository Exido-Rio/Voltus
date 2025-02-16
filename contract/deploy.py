from solcx import compile_standard,install_solc
import json
from web3 import Web3

#install_solc("0.8.0")

with open("./Locker.sol","r") as r :
    file = r.read()


comple_sol = compile_standard(
    {
 "language" : "Solidity",
    "sources" : {"Locker.sol": {"content":file}},
    "settings" : {
        "outputSelection" : {
            "*" : {
                "*" : ["abi","metadata","evm.bytecode","evm.sourceMap"]}
        },
    },
    
}
,solc_version="0.8.0" 
   
)

with open("compiled_code.json", "w") as file:
    json.dump(comple_sol, file)

#get bytecode 

bytecode = comple_sol["contracts"]["Locker.sol"]["Locker"]["evm"][
    "bytecode"
]["object"]

# get abi
abi = json.loads(
    comple_sol["contracts"]["Locker.sol"]["Locker"]["metadata"]
)["output"]["abi"]


with open("abi.json", "w") as file:
    json.dump(abi, file)


w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
chain_id = 1337 

my_address = "your_wallet_address"
priv_key="private_key"

my_contract = w3.eth.contract(abi=abi,bytecode=bytecode)

# getting noce 
nonce = w3.eth.get_transaction_count(my_address)

transaction = my_contract.constructor().build_transaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce,
    }
)


# Sign the transaction
signed_txn = w3.eth.account.sign_transaction(transaction, private_key=priv_key)
print("Deploying Contract!")

# Send it!
tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
# Wait for the transaction to be mined, and get the transaction receipt
print("Waiting for transaction to finish...")
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Done! Contract deployed to {tx_receipt.contractAddress}")
