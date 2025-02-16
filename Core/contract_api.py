from django.conf import settings
from web3 import Web3


w3 = Web3(Web3.HTTPProvider(settings.INFRA_URL))
chain_id = settings.CHAIN_ID 


simple_storage = w3.eth.contract(address=Web3.to_checksum_address(settings.CONTRACT_ADRESS), abi=settings.ABI)


def add_Data(file_hash:bytes,recipent_name:str,address:str,validater_name:str,valid:bool=True):
    nonce = w3.eth.get_transaction_count(settings.PUBLIC_ADDRESS)
    greeting_transaction = simple_storage.functions.addData(file_hash,recipent_name,address,validater_name,valid).build_transaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": settings.PUBLIC_ADDRESS,
        "nonce":  nonce ,
    }
)
    signed_greeting_txn = w3.eth.account.sign_transaction(
    greeting_transaction, private_key=settings.PRIVATE_KEY
)
    tx_greeting_hash = w3.eth.send_raw_transaction(signed_greeting_txn.raw_transaction)
    print("Updating stored Value...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_greeting_hash)

    return tx_receipt


def get_Data(file_hash:bytes):
   return simple_storage.functions.getData(file_hash).call()


# when needed will implement update and delete one too 

