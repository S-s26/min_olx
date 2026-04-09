from django.shortcuts import render,redirect,get_object_or_404,HttpResponse

from product.forms import ProductForm, ProductImageFormSet
from product.models import ProductImage,product
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        formset = ProductImageFormSet(request.POST, request.FILES, queryset=ProductImage.objects.none())
        
        if form.is_valid() and formset.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()

            for img_form in formset.cleaned_data:
                if img_form:
                    ProductImage.objects.create(product=product, image=img_form['image'])

            return redirect('home')  # Or wherever you want
    else:
        form = ProductForm()
        formset = ProductImageFormSet(queryset=ProductImage.objects.none())

    return render(request, 'add_product.html', {'form': form, 'formset': formset})





def product_detail(request, id):
    product_de = get_object_or_404(product, id=id)
    print(product_de.seller.username," this is detalies")
    return render(request, 'product_detail.html', {'product': product_de})


@login_required
def my_products(request):
    products = product.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'my_products.html', {'products': products})

def delete_product(request,id):
    product_d=product.objects.filter(id=id)
# HttpResponse('<script> alert("are you sure you want to delete")</script>')
    product_d.delete()
    return redirect("my_products")
