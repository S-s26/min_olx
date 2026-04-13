from django.shortcuts import render , redirect
from .forms import customUserForm
from django.contrib.auth import login,logout
from django.contrib.auth.forms import AuthenticationForm
from accounts.models import customUser





# this is only signup  code 
# def signup(request):
#     if (request.method=='POST'):
#         form= customUserForm(request.POST)
#         if form.is_valid():
#             user=form.save()
#             login(request,user)
#             return redirect('home')
#     else:
#         list_display={'username':'','first_name':'','last_name':'','email':'','phone':'','address':''}
#         form=customUserForm(initial=list_display)
#     return render(request,"signup.html",{'form':form})


# this is signup code with otp verification on email method 1 using another temlate

import random
from django.core.mail import send_mail

# def signup(request):
#     if (request.method=='POST'):
#         form= customUserForm(request.POST)
#         if form.is_valid():
#             request.session['user_data']=form.cleaned_data
#             otp = random.randint(100000, 999999)
#             print(otp)
#             request.session['otp'] = str(otp)

#             # Send OTP to email
#             send_mail(
#                 subject='Your OTP for Mini-Olex Signup',
#                 message=f'Your OTP is: {otp}',
#                 from_email='Mini olx <kyobatau6@gmail.com>',
#                 recipient_list=[form.cleaned_data['email']],
#                 fail_silently=False,

#             )
#             print("OTP sent to email:", form.cleaned_data['email'])


#             return redirect('verifyotp')  # Next step

#     else:
#          list_display={'username':'','first_name':'','last_name':'','email':'','phone':'','address':''}
#          form = customUserForm(initial=list_display)
#     return render(request, 'signup.html', {'form': form})

# def verify_otp(request):
#     if request.method == 'POST':
#         entered_otp = request.POST.get('otp')
#         print(request.session.get('otp'))
#         if entered_otp == request.session.get('otp'):
#             data = request.session.get('user_data')
#             user = customUser.objects.create_user(
#                 username=data['username'],
#                 first_name=data['first_name'],
#                 last_name=data['last_name'],
#                 email=data['email'],
#                 phone=data['phone'],
#                 address=data['address'],
#                 password=data['password1'],
                
#             )
#             login(request, user)
#             # Clean up session
#             del request.session['otp']
#             del request.session['user_data']
#             return redirect('home')
#         else:
#             return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})
#     return render(request, 'verify_otp.html')









# this is signup code with otp verification on email method 2  using same temlate
def signup(request):
    if request.method == 'POST':
        if 'otp' in request.POST:
            # OTP verification phase
            form_data = request.session.get('form_data')
            form = customUserForm(form_data)
            entered_otp = request.POST.get('otp')
            sent_otp = request.session.get('otp')
            print(sent_otp)

            if entered_otp == sent_otp:
                if form.is_valid():
                    user = form.save()
                    del request.session['otp']
                    del request.session['form_data']
                    login(request, user)
                    return redirect('home')
            else:
                return render(request, 'signup.html', {'form': form, 'otp_sent': True, 'otp_error': 'OTP does not match'})
        else:
            # First form submission
            form = customUserForm(request.POST)
            if form.is_valid():
                otp = str(random.randint(100000, 999999))
                send_mail(
                    subject='Your OTP for Mini-Olex Signup',
                    message=f'Your OTP is: {otp}',
                    from_email='Mini-Olex <kyobatau6@gmail.com>',
                    recipient_list=[form.cleaned_data['email']],
                    fail_silently=False,
                )
                request.session['otp'] = otp
                print("OTP sent to email:", otp)
                request.session['form_data'] = request.POST.dict()
                return render(request, 'signup.html', {'form': form, 'otp_sent': True})
    else:
         list_display={'username':'','first_name':'','last_name':'','email':'','phone':'','address':''}
         form = customUserForm(initial=list_display)
    return render(request, 'signup.html', {'form': form})






























#this is login code
def logins(request):
     if request.method == 'POST':
        data=request.POST
        form = AuthenticationForm(request, data)
        print(request.POST)
        if form.is_valid():
            User = form.get_user()
            login(request,User)
            return redirect('home')
        else:
            print(form.errors)
     else:
         initial_data = {'username':'', 'password':''}
         form = AuthenticationForm(initial=initial_data)
                    # return render(request, 'auth/login.html',{'form':form}) 

     return render(request,"login.html",{'form':form})


# this is logout 
def logout_user(request):
    logout(request)
    return redirect('login')


   

# Create your views here.
