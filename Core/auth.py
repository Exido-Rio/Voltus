from jose import JWTError, jwt
from datetime import datetime, timedelta
from web3.auto import w3
from web3 import Web3
from eth_account.messages import encode_defunct

# Algorithm
# Experation time (how long a user can be login after provide credntial one time)

# Load RSA keys
with open('private_key.pem', 'r') as f:
    private_key = f.read()

with open('public_key.pem', 'r') as f:
    public_key = f.read()

ALGORITHM = "ES384" # most secure for the time being lol 
ACCESS_TOKEN_EXPIRE_MINUTES = 10

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    endcoded_jwt = jwt.encode(to_encode, private_key, algorithm=ALGORITHM)

    return endcoded_jwt


def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])

        id: str = payload.get("user_id") # what we wanna get such user id public wallet address
        verified : int =  payload.get("verified") 
        if id is None:
            raise Exception("Data not found")
        # token_data = schema.ToeknData(id=id) # need to define the type of the needed info that is fetch into the token 
        return {"user_id":id,"verified":verified}
    
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
    except JWTError:
        raise Exception("Unknown jwt Error")
    


def verify_access_nonce(nonce:str) -> True :
    try:
        payload = jwt.decode(nonce, public_key, algorithms=[ALGORITHM])
        

        return True
    
    except Exception as e :
        print(e)
        return False 
    

def verify_signature(message, signature, signer_address):
    # Hash the message
    message_hash = message = encode_defunct(text=message)
    
    # Recover the address from the signature
    recovered_address  = (w3.eth.account.recover_message(message, signature=signature)).lower()

    print(signer_address)
    print(recovered_address)
    # Check if the recovered address matches the signer address
    return recovered_address == signer_address

