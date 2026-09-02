from django.shortcuts import render, redirect
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
import secrets
from datetime import datetime
from .auth import create_access_token, verify_access_token, verify_signature, verify_access_nonce
from .models import Signer, IssuedCertificate
from .contract_api import add_Data, get_Data, update_Data
from web3 import Web3
from django.conf import settings


def signer_required(function):
    def wrapper(request, *args, **kwargs):
        con = request.COOKIES.get('auth')
        if not con:
            return redirect("/")
        if cache.get(f"blacklist_{con}"):
            return redirect("/")
        try:
            token = verify_access_token(con)
        except Exception as e:
            return redirect("/")

        return function(request, *args, signer=token, **kwargs)

    wrapper.__doc__ = function.__doc__
    wrapper.__name__ = function.__name__
    return wrapper


def home(request):
    if request.method == 'POST':
        msg = request.POST.get("message", "")
        sig = request.POST.get("signature", "")
        addr = request.POST.get("walletaddress", "")

        if verify_access_nonce(msg) and verify_signature(msg, sig, addr):
            signer_obj, created = Signer.objects.get_or_create(
                public_addr=addr,
                defaults={'verified': 1, 'applied_verification': 1}
            )
            # Ensure existing signers are also marked verified by default
            if signer_obj.verified == 0:
                signer_obj.verified = 1
                signer_obj.save()

            user_data = {"user_id": addr, "verified": 1}
            res = redirect("/locker")
            res.set_cookie('auth', create_access_token(user_data), max_age=600)
            return res
        else:
            messages.error(request, "Signature verification failed. Please try again.")
            return redirect("/")

    authenticated, verified = False, False
    con = request.COOKIES.get('auth')
    if con and not cache.get(f"blacklist_{con}"):
        try:
            token = verify_access_token(con)
            authenticated = True
            verified = True if token.get("verified", 1) == 1 else False
        except Exception:
            pass

    nonce = create_access_token({"nonce": f"Sign this to login to Voltus: {secrets.token_hex(16)}"})
    return render(request, "index.html", {
        "message": nonce,
        "authenticated": authenticated,
        "verified": verified
    })


@signer_required
def addToLocker(request, signer):
    results = []
    if request.method == "POST":
        hashes_str = request.POST.get("hashes", "")
        names_str = request.POST.get("names", "")
        
        hashes = [h.strip() for h in hashes_str.split(",") if h.strip()]
        names = [n.strip() for n in names_str.split(",") if n.strip()]

        signer_obj = Signer.objects.filter(public_addr=signer["user_id"]).first()
        validator_name = signer_obj.Company_Name if (signer_obj and signer_obj.Company_Name) else "Verified Issuer"

        for h, name in zip(hashes, names):
            # 1. Pre-check local DB for existing record
            existing_local = IssuedCertificate.objects.filter(file_hash__iexact=h).first()
            if existing_local:
                results.append({
                    "name": name,
                    "hash": h,
                    "error": f"Certificate already anchored on-chain for recipient '{existing_local.recipient_name}'.",
                    "already_exists": True,
                    "success": False
                })
                continue

            # 2. Pre-check smart contract directly
            on_chain_data = get_Data(bytes(h, "utf-8"))
            if on_chain_data and isinstance(on_chain_data, (list, tuple)) and len(on_chain_data) >= 5 and on_chain_data[0]:
                results.append({
                    "name": name,
                    "hash": h,
                    "error": f"Certificate already anchored on-chain for recipient '{on_chain_data[0]}'.",
                    "already_exists": True,
                    "success": False
                })
                continue

            # 3. Submit transaction to smart contract
            try:
                receipt = add_Data(
                    bytes(h, "utf-8"),
                    name,
                    Web3.to_checksum_address(signer["user_id"]),
                    validator_name
                )
                tx_hash = receipt.transactionHash.hex() if hasattr(receipt, 'transactionHash') else "Submitted"
                
                # Save into local DB for fast history query & zero RPC overhead
                IssuedCertificate.objects.create(
                    signer_address=signer["user_id"],
                    recipient_name=name,
                    file_name=name,
                    file_hash=h,
                    tx_hash=tx_hash,
                    validator_name=validator_name,
                    is_valid=True
                )
                
                results.append({"name": name, "hash": h, "tx_hash": tx_hash, "success": True})
            except Exception as e:
                err_str = str(e)
                if "Record Already Exists" in err_str or "already exists" in err_str.lower():
                    clean_err = "Certificate digest is already registered in Locker.sol smart contract."
                    already_exists = True
                else:
                    clean_err = f"Blockchain error: {err_str}"
                    already_exists = False

                results.append({
                    "name": name,
                    "hash": h,
                    "error": clean_err,
                    "already_exists": already_exists,
                    "success": False
                })

        if any(r["success"] for r in results):
            messages.success(request, f"Successfully anchored {sum(1 for r in results if r['success'])} certificate(s) to the Ethereum Blockchain!")
        elif any(r.get("already_exists") for r in results):
            messages.warning(request, "One or more certificates were already registered on the blockchain.")
        else:
            messages.error(request, "Failed to anchor certificates to blockchain.")

    return render(request, "hash.html", {"results": results, "user_address": signer["user_id"]})


@signer_required
def transaction_history(request, signer):
    # Query local DB indexed by signer address (zero RPC overhead)
    certificates = IssuedCertificate.objects.filter(
        signer_address__iexact=signer["user_id"]
    ).order_by('-created_at')
    
    return render(request, "history.html", {
        "certificates": certificates,
        "user_address": signer["user_id"]
    })


@signer_required
def revoke_certificate(request, signer):
    if request.method == "POST":
        cert_id = request.POST.get("cert_id", "").strip()

        # IDOR Guard: Ensure certificate belongs to authenticated signer
        cert = IssuedCertificate.objects.filter(
            id=cert_id,
            signer_address__iexact=signer["user_id"]
        ).first()

        if not cert:
            messages.error(request, "Permission Denied: You can only invalidate certificates issued by your account.")
            return redirect("/history")

        try:
            # Execute updateData on smart contract (valid = False)
            update_Data(
                bytes(cert.file_hash, "utf-8"),
                cert.recipient_name,
                cert.validator_name if cert.validator_name else "Verified Issuer",
                Web3.to_checksum_address(signer["user_id"]),
                False
            )
            # Synchronize local DB state
            cert.is_valid = False
            cert.save()
            messages.success(request, f"Certificate for '{cert.recipient_name}' was successfully REVOKED on-chain!")
        except Exception as e:
            messages.error(request, f"Failed to update on-chain status: {str(e)}")

    return redirect("/history")


@signer_required
def apply_for_verification(request, signer):
    signer_obj, _ = Signer.objects.get_or_create(public_addr=signer["user_id"], defaults={'verified': 1})
    
    if request.method == "POST":
        company = request.POST.get("company_name", "")
        position = request.POST.get("position", "")
        info = request.POST.get("info", "")
        
        signer_obj.Company_Name = company
        signer_obj.position = position
        signer_obj.info = info
        signer_obj.verified = 1
        signer_obj.applied_verification = 1
        signer_obj.save()
        
        messages.success(request, "Organization details updated successfully!")

    return render(request, "request_varification.html", {
        "signer": signer_obj,
        "user_id": signer["user_id"]
    })


def verify(request):
    formatted_op = None
    not_found = False

    if request.method == "POST":
        file_hash = request.POST.get("hash", "").strip()
        if file_hash:
            op = get_Data(bytes(file_hash, "utf-8"))
            if op and isinstance(op, (list, tuple)) and len(op) >= 5 and op[0]:
                raw_time = op[4]
                formatted_date = datetime.fromtimestamp(raw_time).strftime("%B %d, %Y - %H:%M:%S UTC") if raw_time else "N/A"
                
                # Cross check local DB if record exists for extra verification
                local_rec = IssuedCertificate.objects.filter(file_hash__iexact=file_hash).first()
                is_valid = op[1] if op[1] is not None else True
                if local_rec and not local_rec.is_valid:
                    is_valid = False

                formatted_op = {
                    "recipient_name": op[0],
                    "valid": is_valid,
                    "validator_addr": op[2],
                    "validator_name": op[3] if op[3] else "Verified Issuer",
                    "timestamp": formatted_date,
                    "file_hash": file_hash
                }
            else:
                not_found = True

    return render(request, "verify.html", {"op": formatted_op, "not_found": not_found})


def docs(request):
    return render(request, "docs.html")


@signer_required
def logout(request, signer):
    con = request.COOKIES.get('auth')
    if con:
        cache.set(f"blacklist_{con}", True, timeout=600)
    res = redirect("/")
    res.delete_cookie('auth')
    return res