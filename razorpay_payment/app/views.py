from django.shortcuts import render
from django.conf import settings
from .models import *
import json
import razorpay
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
def home(req):
    return render(req,'index.html')

def order_payment(req):
    if req.method == "POST":
        name = req.POST.get("name")
        amount = req.POST.get("amount")
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID ,
                                       settings.RAZORPAY_KEY_SECRET )) 
        razorpay_order = client.order.create(
            {"amount":int(amount)*100,"currency": "INR", "payment_capture":"1"}
        )
        order_id= razorpay_order['id']
        order= Order.objects.create(
            name=name,amount=amount,provider_order_id=order_id
        )
        order.save()
        return render(
            req,
            "index.html",
            {
                "callback_url":"http://" + "127.0.0.1:8000" + "razorpay/callback",
                "razorpay_key" : settings.RAZORPAY_KEY_ID ,
                "order":order,
            },
        )
    return render(req,'index.html')

@csrf_exempt
def  callback(req):
    def verify_signature(response_data):
        client= razorpay.Client(auth=(settings.RAZORPAY_KEY_ID ,
                                      settings.RAZORPAY_KEY_SECRET))
        return client.utility.verify_payment_signature(response_data)
    
    if "razor_signature" in req.POST:
        payment_id = req.POST.get("razorpay_payment_id","")
        provider_order_id = req.POST.get("razorpay_order_id","")
        signature_id = req.POST.get("razorpay_signature","")
        order = Order.objects.get(provider_order_id=provider_order_id)
        order.payment_id
        order.signature_id = signature_id
        order.save()
        if not verify_signature(req.POST):
            order.status = PaymentStatus.SUCCESS
            order.save()
            return render(req,"callback.html", context={"status":order.status} )
        else:
            order.status = PaymentStatus.FAILURE
            order.save()
            return render(req,"callback.html", context={"status":order.status})
    else:
        payment_id = json.loads(req.POST.get("error[metadata]")).get("payment_id")
        provider_order_id = json.loads(req.POST.get("error[metadata]")).get("order_id")
        order = Order.objects.get(provider_order_id=provider_order_id)
        order.payment_id= payment_id
        order.status = PaymentStatus.FAILURE
        order.save()
        return render(req,"callback.html", context={"status":order.status})