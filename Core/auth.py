from jose import JWTError, jwt
from datetime import datetime, timedelta
from web3.auto import w3
from web3 import Web3
from eth_account.messages import encode_defunct
from pathlib import Path

# Algorithm
# Experation time (how long a user can be login after provide credntial one time)

# Load RSA keys — try Render secret files first, then project root
def _load_key(filename):
    for path in [Path(f"/etc/secrets/{filename}"), Path(filename)]:
        if path.exists():
            return path.read_text()
    raise RuntimeError(f"{filename} not found in /etc/secrets/ or project root")

private_key = _load_key('private_key.pem')
public_key = _load_key('public_key.pem')

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

        id: str = payload.get("user_id")
        verified: int = payload.get("verified", 1)
        if verified is None:
            verified = 1
        if id is None:
            raise Exception("Data not found")
        return {"user_id": id, "verified": verified}
    
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
    except JWTError:
        raise Exception("Unknown jwt Error")
    


def verify_access_nonce(nonce:str) -> bool:
    try:
        payload = jwt.decode(nonce, public_key, algorithms=[ALGORITHM])
        return True
    except Exception as e:
        print(e)
        return False 
    

def verify_signature(message, signature, signer_address):
    # Hash the message
    encoded_message = encode_defunct(text=message)
    
    # Recover the address from the signature
    recovered_address = (w3.eth.account.recover_message(encoded_message, signature=signature)).lower()

    print("Signer address:", signer_address)
    print("Recovered address:", recovered_address)
    # Check if the recovered address matches the signer address
    return recovered_address == signer_address.lower()

