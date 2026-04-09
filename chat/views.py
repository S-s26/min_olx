from django.shortcuts import render ,redirect,get_object_or_404
from chat.models import chatroom,message
from product.models import product
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def chat_list(request):
    print("chat list")
    user=request.user
    conversations=chatroom.objects.filter(buyer=user) | chatroom.objects.filter(seller=user)
    print("chat list  cc",conversations)
    return render(request,'chat_list.html',{'chatroom':conversations})



@login_required
def start_chat(request,p_id):
    print("start chat",p_id)
    product_d = get_object_or_404(product, id=p_id)
    seller=product_d.seller
    print("start chat  ss",seller)
    buyer=request.user
    if buyer==seller:
        return redirect('home')
    print("start chat  bb",buyer)
    conversation,created=chatroom.objects.get_or_create(product=product_d,buyer=buyer,seller=seller)
    print("start chat  cc",conversation)
    return redirect('chat_detail',chatroom_id=conversation.id)



@login_required
def chat_details(request,chatroom_id):
    print("chat details",chatroom_id)
    conversation=get_object_or_404(chatroom,id=chatroom_id)
    if request.method=="POST":
        print("ajex posted")
        text=request.POST.get('text')
        print("this is text",text)
        if text:
            #this is method1 to save the data in data base 
            # message.objects.create(room=conversation,sender=request.user,message=text)
            #this is method 2 to save the data in database
            messages=message(room=conversation,sender=request.user,message=text)
            messages.save()
            print("this is text")
        # return redirect('chat_detail', chatroom_id=chatroom_id)
    return render(request,'chat_details.html',{'conversation':conversation,'messages':conversation.message.all})


 
