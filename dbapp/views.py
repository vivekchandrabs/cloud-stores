
#imports from django
from django.shortcuts import render,redirect,HttpResponse,Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.utils import timezone    
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from dbapp.render import Render
from django.template.loader import get_template
from django.template import Context

#imports from the db_app
from dbapp.models import UserDetail,Store,Item,OrderShop,Order_Item,Cart
import dbapp.money_divider  as j

l=list()

less_items=list()


def home(request):
	# returns the home of the app
	return render(request,"home.html")

def about(request):
	# returns the about page of the app
	return render(request,"aboutus.html")

def signup(request):
	'''
	:method:POST

	:Required:
		username
		password
		email
		user_type
		address
		phone

	:Not very important:
		invitecode
		store_id

	Returns following:
		1: returns signup page for :method = GET
		2: redirect to the signin page after user is created :method=POST

	'''
	
	if request.method == "POST":
		username = request.POST.get('username', None)
		password = request.POST.get('password', None)
		email = request.POST.get("email")
		user_type=request.POST.get("user_type")
		user_type=int(user_type)
		print(user_type)
		invitecode=request.POST.get('invitecode')
		address=request.POST.get("address")
		phone=request.POST.get("phone")
		
		try:
			# if the username is already take by someone.
			user = User.objects.get(username=username)
			return render(request,'signup.html',
								{'show':'username already taken'})
			
		except:			
			# if the user is of type shop keeper
			if user_type == 2:
				storeid=request.POST.get('storeid')
				store=Store.objects.get(pk=storeid)
				code=store.invitecode

				if invitecode == code:
					user = User.objects.create_user(username, email, password)
					no_of_stores=0
					
					profile=UserDetail(user=user,user_type=user_type,
										address=address,
										no_of_stores=no_of_stores,
										storeid=storeid,
										phone_no=phone)
					profile.save()

					cart=Cart(shopkeeper=user)
					cart.save()

					return redirect('/signin/') 

				else:
					return render(request,'signup.html',
									{'notice':"wrong invite code"})
				
			# if user is of the type owner
			elif user_type ==1:
				user = User.objects.create_user(username, email, password)
				no_of_stores=0
				storeid=0
				profile=UserDetail(user=user,
									user_type=user_type,
									no_of_stores=no_of_stores,
									storeid=storeid,
									address=address,
									phone_no=phone)
				profile.save()
				return redirect('/signin/') 

	try:		
		# returns all the store to names and the id to the signup page		
		store=Store.objects.all()
		return render(request, "signup.html",{'store':store})
	except:
		return render(request, "signup.html",{'store':''})

def signin(request):
	'''
	:method:POST
	:Required:
		username
		password

	returns following:
		1: signin page for method = GET
		2: redirects to the dashboard if its a owner
		3: redirects to the store page if its a shopkeeper
	'''
	user = request.user

	# checks if the user is already logedin.
	if user.is_authenticated:
		username=request.user.username

		if user.userdetail.user_type == 1:
			# redirects to the dashboard if user is of type owner
			url = '/' + username + '/owner/'
			return redirect(url)

		else:
			# redirects to the checkout page if the user of type shopkeeper
			storeid = user.userdetail.storeid
			storeid = str(storeid)
			url='/shop/'+storeid+'/checkout/'
			return redirect(url)	

	if request.method == "POST":
		username = request.POST['username']
		password = request.POST['password']

		user = authenticate(request, username=username, 
			password=password)

		if user is None:
			return render (request,'signin.html',
							{'caution':"User Name or Password Might be Wrong"})

		if user is not None:

			# redirects to the dashboard
			if user.userdetail.user_type == 1:
				login(request, user)
				username=request.user.username
				username=str(username)				
				url='/'+username+'/owner/'
				return redirect(url)

			# redirects to the checkout page
			elif user.userdetail.user_type == 2 and user.username==username:
				login(request, user)
				username=request.user.username
				storeid=user.userdetail.storeid
				storeid=str(storeid)
				url='/shop/'+storeid+'/checkout/'
				return redirect(url)

	return render(request, "signin.html")

@login_required
def Take_Text(request,user_name):

	if request.method=='POST':
		Text=request.POST.get('text')
		user=request.user
		user=User.objects.get(username=user)
		Take=Userdb(Text=Text,User=user)
		return HttpResponse('success')
	return render(request,'base.html')

@login_required
def owner(request,owner):
	'''
	:method:GET
	:params str:owner
	retuns owner.html with all the stores and the username of the owner
	'''
	user=request.user
	user=UserDetail.objects.get(user=user)
	storeofuser=Store.objects.filter(owner=user)

	return render(request,'owner.html',{'user_name':owner,'show':storeofuser})
	
@login_required
def addstore(request,owner):
	'''
	:params str:owner
	
	Performs:
		Creates a new store

	:Required:
		storename
		invitecode

	Returns:
		1: owner.html - after creating the store
		2: addstores.html - before creating the store

	'''

	owner=request.user.username
	if request.method=="POST":

		name=request.POST.get('storename')
		invitecode=request.POST.get('invitecode')

		user=request.user
		user.userdetail.no_of_stores+=1
		user.userdetail.save()
		user=UserDetail.objects.get(user=user)

		store=Store(name=name,owner=user,invitecode=invitecode)
		store.save()
		
		storeofuser=Store.objects.filter(owner=user)
		

		return render(request,'owner.html',
										{'user_name':owner,'show':storeofuser})
	
	return render(request,'addstore.html',{'user_name':owner})

@login_required
def additem(request,storeid):
	'''
	:params pk: storeid

	Performs:
		Adds the item to the store.

	:Required:
		name
		barcode
		quantity
		price

	Returns:
		additem.html for both GET and POST method
	'''
	owner=(request.user.username)
	user=request.user
	user=UserDetail.objects.get(user=user)
	user_type=user.user_type

	if request.method=="POST":
		name=request.POST.get('name')
		barcode=request.POST.get('barcode')
		quantity=request.POST.get('quantity')
		price=request.POST.get('price')

		store=Store.objects.get(pk=storeid)

		item=Item(name=name,barcode=barcode,
					quantity=quantity,price=price,store=store)
		item.save()

		store=Store.objects.get(pk=storeid)
		items=Item.objects.filter(store=store)

		return render(request,'additem.html',
										{'show':'',
										'user_name':owner,
										 "storeid":storeid,
										 "showitem":items,
										 "user_type":user_type
										 })
	
	return render(request,'additem.html',
							{'show':'','user_name':owner, 
							"storeid":storeid,"user_type":user_type})

@login_required
def viewitem(request,storeid):
	'''
	:params pk:storeid

	Performs:
		Get all the items from the database.

	Returns viewitems.html
	'''

	owner=request.user.username
	user=request.user
	
	try:
		store=Store.objects.get(pk=storeid)
		items=Item.objects.filter(store=store)

		user=request.user
		user=UserDetail.objects.get(user=user)
		user_type=user.user_type

		return render(request,'viewitems.html', 
								{'showitem':items,
								'store':store,
								'storeid':storeid,
								'user_type':user_type,
								'user_name':owner,
								"user_type":user_type})
	except:
		return HttpResponse('no items in this store')

@login_required
def chooseshop(request,storeid):
	'''
	:params pk: storeid

	Performs:
		Filters all the distributors for the particular stores.

	Returns the chooseshop.html with all the distributors for it.
	'''
	storeid=str(storeid)
	user=request.user.username
	store=Store.objects.get(pk=storeid)

	try:
		shop=OrderShop.objects.filter(store=store)

		return render(request,"chooseshop.html",
								{'show':shop,'storeid':storeid,'user_name':user})
	except:
		return render(request,"chooseshop.html",
								{'show':'','storeid':storeid,"user_name":user})

@login_required
def choosestore(request,owner):
	'''
	:params str: owner

	Performs:
		Filters the stores related to the owner
		
	Returns the choosestore.html with all the stores.
	'''
	user=request.user
	user=UserDetail.objects.get(user=user)	
	storeofuser=Store.objects.filter(owner=user)

	return render(request,'choosestore.html',{'user_name':owner,"show":storeofuser})

@login_required
def orderitems(request,storeid,shopid):
	'''
	:params pk:storeid, pk:shopid

	Required:
		itemname
		quantity

	Performs:
		* Takes in all the required data
		* Gets the distributor instance through the store instance from storeid
		* Gets the distributor email address
		* Sends an email to the Distributor 

	Returns order.html with the order item.
		
	'''
	owner=request.user.username

	if request.method=='POST':		
		itemname=request.POST.get('itemname')
		quantity=request.POST.get('quantity')
		
		ordershop=OrderShop.objects.get(pk=shopid)
		shop=Order_Item(
					order_shop=ordershop,
					storeid=storeid,
					quantity=quantity,
					itemname=itemname)
		shop.save()

		name_shop=ordershop.name_shop
		address=ordershop.address
		email=ordershop.email
		shopkeeper=ordershop.shopkeeper_name
		phone=ordershop.phone_no
		storesname=ordershop.store.name

		# message for the email
		message="Purchase order\nstore name: "+storesname+"\nshopkeeper name: "+shopkeeper+"\nphone:"+phone+"\n address:"+address+"\nitemname: "+itemname+"\nquantity: "+quantity+"\n  Thank you"
		
		msg = EmailMessage("Purchase Order", message, to=[email])
		msg.send()

		message="successfully ordered "+message
		return render(request,'orderitems.html',
								{'storeid':storeid,
									'shopid':shopid,
									"user_name":owner,
									"show":ordershop,
									"itemname":itemname,
									"quantity":quantity})

	return render(request,'orderitems.html',
									{'storeid':storeid,
									'shopid':shopid,
									"user_name":owner})

@login_required
def addshop(request,storeid):
	'''
	:params: storeid

	Required:
		email
		storename
		shopkeeper
		phone
		address

	Performs:
		Creates a store by taking in all the requirements 

	Returns addshop.html 
	'''
	owner=request.user.username
	if request.method=='POST':
		email=request.POST.get('email')
		storename=request.POST.get('storename')
		shopkeeper=request.POST.get('shopkeeper')
		phone=request.POST.get('phone')
		phone=int(phone)
		address=request.POST.get('address')

		store=Store.objects.get(pk=storeid)
		shop=OrderShop(store=store,
						name_shop=storename,
						address=address,
						email=email,
						shopkeeper_name=shopkeeper,
						phone_no=phone)
		shop.save()

		storeid=str(storeid)

		url='/'+storeid+'/chooseshop/'
		return redirect(url)

	return render(request,'addshop.html',{'storeid':storeid,"user_name":owner})

@login_required
def deleteshop(request,owner):
	'''
	:params str: owner

	Performs:
		Filters all the stores of the particular owner

	Returns delete.html
	'''
	username=request.user.username
	user=request.user
	user=UserDetail.objects.get(user=user)

	try:
		storeofuser=Store.objects.filter(owner=user)
		return render(request,"delete.html",{"user_name":username,"show":storeofuser})

	except:
		return render(request,"delete.html",{"user_name":username,"show":''})

	
@login_required
def deletestores(request,storeid):
	'''
	:params pk: storeid

	Performs:
		Deletes the shop with the storeid

	redirects to the delete shop page.
	'''
	deletestore=Store.objects.get(pk=storeid)
	deletestore.delete()
	print("deleted")
	username=request.user.username
	url="/"+username+"/delete/"
	return redirect(url)

@login_required
def delete_item_from_cart(request,store_id, item_id):
	'''
	:params: pk:store_id, pk: item_id

	Performs:
		Takes the storeid and itemid, deletes the item from the cart.

	Redirects the checkout page
	'''
	user = request.user
	cart = Cart.objects.get(shopkeeper=user)
	items = cart.items

	for item in items:
		if item[0] == int(item_id):
			items.remove(item)
	cart.save()

	return redirect(f"/shop/{store_id}/checkout")

@login_required
def checkout(request,storeid):
	'''
	:params: storeid

	Performs:
		Takes the storeid and emails the customer with the bill

	redirect
	'''
	store=Store.objects.get(pk=storeid)
	user=request.user

	cart=Cart.objects.get(shopkeeper=user)
	email=request.POST.get('email')

	#render the template here and email
	storeitems=Item.objects.get(store=store)

	for i in cart.items:#this is the arraylist of arrayfield
		itemid=i[0]
		item=Item.objects.get(pk=itemid)
		item.quantity=item.quantity-i[1]
		item.save()

		msg = EmailMessage("Purchase Order", message, to=[email])
		msg.send()


@login_required
def customer(request,storeid):
	'''
	:params pk: storeid

	:Required:
		itemname
		quantity

	Performs:
		* Adds the item to the cart
		* If the item is less then quantity sends a message.

	Redirects to the customer checkout page.
	'''
	store=Store.objects.get(pk=storeid)
	user=request.user
	shopkeeper = UserDetail.objects.get(storeid=storeid,user=user, user_type=2)
	message=''

	if request.user != shopkeeper.user:
		return redirect("/")	
	
	if request.method=="POST":
		itemid=int(request.POST.get("itemname"))
		quantity=int(request.POST.get("quantity"))
		
		cart=Cart.objects.get(shopkeeper=user)

		item_quantity=Item.objects.get(store=store,id=itemid)
		q=int(item_quantity.quantity)-quantity

		if q<0 :
			message="ONLY "+str(item_quantity.quantity)+" units of "+item_quantity.name+" left"

		else:
			cart.items.append([itemid, quantity])
			cart.save()
			message=''

	cart=Cart.objects.get(shopkeeper=user)
	citems = cart.items

	if citems is not None:
		cart={Item.objects.get(store=store, id=citem[0]):[citem[1],Item.objects.get(store=store,id=citem[0]).price] for citem in citems}
		sum=0

		for i,v in cart.items():
			sum+=v[1]*v[0]

	items = Item.objects.filter(store=store)

	return render(request,"customer.html",
							{'items':items,
							'storeid':storeid,
							 "cart":cart,
							 'message':message,
							 'total_price':sum})

def signout(request):
	user = request.user
	logout(request)
	return redirect('/signin/')

def checkoutcust(request, storeid):
	'''
	:params: storeid

	Required: 
		money
		email

	Perform:
		If the item is less then 7 send the email to the owner of the store.
		Emails the bill to the customer 

	Redirects to custome checkout page.
	'''

	store=Store.objects.get(pk=storeid)
	money=int(request.POST.get('money'))
	email = request.POST.get('email')

	ocart = Cart.objects.get(shopkeeper=request.user)
	citems = ocart.items

	cart={Item.objects.get(store=store, 
							id=citem[0]):[citem[1]] for citem in citems}

	total = 0
	del less_items[:]

	for item, details in cart.items():
		item.quantity=item.quantity-details[0]
		item.save()

		x = details[0]*item.price
		details.append(x)
		cart[item] = details
		total += x

		if (item.quantity) < 7:
			less_items.append(item)
			#write the email to be sent to the owner code here
			message=get_template('email/notice.html').render(
													{'less_items':less_items})
			storeowner_email=store.owner.user.email
			
			msg = EmailMessage(
				f"Product Notification {store.name}",
										 message, 
										 to=[storeowner_email])
			msg.content_subtype = "html"
			msg.send()

	change=int(abs(total-money))
	mo=j.money1()
	mo.refill()
	mo.fill(change)
	mo.go()

	new_para=mo.printing()
	
	message = get_template('email/bill.html').render(
					{'cart':cart, 'total':total, 'store':store, 'email':email})

	msg = EmailMessage(f"Cash Bill from {store.name}", message, to=[email])
	msg.content_subtype = "html"
	msg.send()

	ocart.items = []
	ocart.save()

	items=Item.objects.filter(store=storeid)
	return render(request,"customer.html",
							{'items':items,'show':new_para,"storeid":storeid})
