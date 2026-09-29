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

from activity.models import UserActivity

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









from django.conf import settings
from django.contrib import messages

def _send_otp(request, email, otp, is_resend=False):
    # Check if we should fallback to screen (Demo Mode)
    # Get the appropriate API key depending on if it's a resend
    api_key = getattr(settings, 'BACKUP_API_KEY', '') if is_resend else getattr(settings, 'BREVO_API_KEY', '')
    
    if settings.DEBUG or not api_key:
        # Fallback to screen message
        messages.info(request, f"DEMO MODE: Your OTP is {otp}")
        print(f"Fallback OTP shown on screen: {otp}")
        return False
    else:
        # Try to send email
        try:
            send_mail(
                subject='Your OTP for Mini-oLx Signup',
                message=f'Your OTP is: {otp}',
                from_email='Mini-oLx <kyobatau6@gmail.com>',
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"bhai mail nahi ja raha hai error ye hai {e}")
            messages.warning(request, f"Email delivery failed. DEMO MODE OTP: {otp}")
            return False

def signup(request):
    if request.method == 'POST':
        if 'resend_otp' in request.POST:
            # Resend OTP logic
            form_data = request.session.get('form_data')
            if form_data:
                otp = str(random.randint(100000, 999999))
                request.session['otp'] = otp
                _send_otp(request, form_data['email'], otp, is_resend=True)
                form = customUserForm(form_data)
                return render(request, 'signup.html', {'form': form, 'otp_sent': True})
            return redirect('signup')

        elif 'otp' in request.POST:
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
                    UserActivity.record(
                        user, UserActivity.EVENT_SIGNUP,
                        title='Welcome to Mini-oLx!',
                        detail=f'Joined as {user.username}',
                    )
                    return redirect('home')
            else:
                return render(request, 'signup.html', {'form': form, 'otp_sent': True, 'otp_error': 'OTP does not match'})
        else:
            # First form submission
            form = customUserForm(request.POST)
            if form.is_valid():
                otp = str(random.randint(100000, 999999))
                request.session['otp'] = otp
                request.session['form_data'] = request.POST
                _send_otp(request, form.cleaned_data['email'], otp, is_resend=False)
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
            UserActivity.record(
                User, UserActivity.EVENT_LOGIN,
                title='Signed in',
            )
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
