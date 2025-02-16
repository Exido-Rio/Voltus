from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User, auth
#from django_redis import get_redis_connection
from django.core.cache import cache
from django.http import HttpResponse,JsonResponse
from django.contrib import messages
import secrets
from django.contrib.auth.decorators import login_required
from .auth import create_access_token,verify_access_token,verify_signature,verify_access_nonce
from .models import Signer
from .contract_api import add_Data,get_Data
from web3 import Web3
from django.conf import settings
import redis


REDIS_INSTANCE = redis.Redis(host=settings.REDIS_IP)

from django.core.cache import cache


BLACKLIST_TOKEN = [] # when using the redis cache can set exp time to 10min so, auto handle the jwt removal from the mem 



# same like login_required replica for our own purpose 
def signer_required(function):
    def wrapper(request, *args, **kwargs):
        con =  request.COOKIES.get('auth')
        if con in BLACKLIST_TOKEN:
            return redirect("/") 
        try :
            token = verify_access_token(con) # this will check jwt is truly signed 
        except Exception as e:
            return redirect("/") 

        # keyword args here will cause issue any function using them must accept this keyword argument 
        return function(request, *args, signer=token, **kwargs)

    wrapper.__doc__ = function.__doc__
    wrapper.__name__ = function.__name__
    return wrapper

# Create your views here.


def home(request):
    if request.method == 'POST':
        msg = request.POST["message"]
        sig = request.POST["signature"]
        addr = request.POST["walletaddress"]
        print(msg)
        if verify_access_nonce(msg) and  verify_signature(msg,sig,addr) :
            """Security hardning making the nonce signed by the user so, that someone can't use a presigned stolen nonce to takeover the account  """
            # verify access nonce verification fails 
            # lol if not exist create the new one 
            if not (Signer.objects.filter(public_addr=addr).exists()):
                new_signer = Signer.objects.create(public_addr=addr)
                new_signer.save()
            # generate a jwt for few minutes less than 10 
            print("verified")
            user_data = {"user_id":addr}
            # this check whether the user is verified to perform hashing transactions 
            if Signer.objects.get(public_addr=addr).verified:
                user_data.update({"verified":1})
            res =  redirect("/locker")
            res.set_cookie('auth', create_access_token(user_data), max_age=600)
            return res
            
        else :
            print("not verified")
            return redirect("/")
    
    authenticated,verified = False,False
    con =  request.COOKIES.get('auth')
    try :
        #print("cool",REDIS_INSTANCE.get(con))
        if con not in BLACKLIST_TOKEN:
            token = verify_access_token(con) # this will check jwt is truly signed 
            authenticated = True
            verified = True if token["verified"]== 1 else False
    except Exception as e:
        pass




    
    nonce = create_access_token({"nonce": f"Sign this to login : {secrets.token_hex(16)}"}) 
    print(nonce,authenticated,verified)
    return render(request,"index.html", {"message":nonce,"authenticated":authenticated,"verified":verified})



# droping the cheak for now 

@signer_required
def addToLocker(request,signer):
    
    if request.method == "POST" :
        hashes = request.POST["hashes"].split(",")
        names = request.POST["names"].split(",")
        Validator_name = Signer.objects.get(public_addr=signer["user_id"]).Company_Name


        for hash,name in zip(hashes,names):
            add_Data(bytes(hash,"utf-8"),name,Web3.to_checksum_address(signer["user_id"]),Validator_name)
           
        


        
    
    if signer["verified"]: # verfic f in jwt can be said to be leaking the info a bit 
        return render(request,"hash.html")
    
    return redirect("/apply")
    


@signer_required
def apply_for_verification(request,signer):
    if request.method == "POST":
        # we need to the application saved so admin can verify it manually 
        pass
        
    if Signer.objects.get(public_addr=signer["user_id"]).applied_verification:
        return render(request,"request_varification.html",{"msg":"Your application will be process soon be patient"})
    # need the logged in validation 
    return render(request,"request_varification.html")



@signer_required
def transaction_history(request):
    """This function will be will be able to show a user it's all past transaction which will be decided in two ways 
    1- Either we trigger the event once a transaction is process and then add it to our local db
    2- we crate a new storage contract per user and query it when user visits this side """
    pass


def verify(request):
    if request.method == "POST":
        hash = request.POST["hash"]
        op = get_Data(bytes(hash,"utf-8"))
        print(op,type(op))
        not_found = True
        if not(op[0]):
            op = False
        return render(request,"verify.html",{"op":op,"not_found":not_found})

    return render(request,"verify.html")


@signer_required
async def  logout(request,signer):
    con =  request.COOKIES.get('auth')
    # this won't work as for logging in we used custom jwt so, we can just blacklist that token 
    # for this we can utilize the redis cache 
    BLACKLIST_TOKEN.append(con)
    cache.set("new",str(con))
    print(cache.get("new"))
    # we won't use redis set because of it's much better to check cache for blacklisted keys than verifying them 
    await REDIS_INSTANCE.add(con,"0")
    print("from cache")
    print(REDIS_INSTANCE.get(con))
    return redirect("/")

# this sometime give issue with incorrect version