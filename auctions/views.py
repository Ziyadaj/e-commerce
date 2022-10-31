import datetime
import imp
from multiprocessing import context
from secrets import choice
from tkinter import Widget
from django import forms
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import User, Auction, Bid, Comment, Watchlist

class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['title', 'description', 'starting_bid', 'image', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'starting_bid': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
        image = forms.ImageField(required=False)
class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid_price']
        widgets = {
            'bid_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

def index(request):
    empty = False
    if len(Auction.objects.all()) == 0: # check if there are any items in the database
        empty = True
    return render(request, "auctions/index.html", {
        "items": Auction.objects.all(),
        "empty": empty
    })
@login_required(login_url='/login')
def listing(request, listing_id):

    #Gets details of a listing by id
    item = Auction.objects.get(id=listing_id)
    bids = Bid.objects.filter(auction=listing_id)
    comments = Comment.objects.filter(auction=listing_id)
    seller = Auction.objects.get(id=listing_id).user
    if item.category == '1':
        category = "Furniture"
    elif item.category == '2':
        category = "Clothes"
    elif item.category == '3':
        category = "Electronices"
    elif item.category == '4':
        category = "Books"
    elif item.category == '5':
        category = "Other"
    else:
        category = "No Category Listed"
    
    num_bids = len(bids)
    if request.method == "POST":
        form = BidForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['bid_price'] <= item.starting_bid: # check if bid is higher than starting bid
                messages.error(request, "Bid must be greater than starting bid")
                return render(request, "auctions/listing.html", {
                    "item": item,
                    "bids": bids,
                    "comments": comments,
                    "form": form,
                    "category": category
                })
            if len(bids) > 0:
                if form.cleaned_data['bid_price'] <= bids.order_by('-bid_price').first().bid_price: # check if bid is greater than the highest bid
                    messages.error(request, "Bid must be greater than current bid")
                    return render(request, "auctions/listing.html", {
                        "item": item,
                        "bids": bids,
                        "comments": comments,
                        "form": form,
                        "category": category
                    })
            bid = Bid.objects.create(bid_price=form.cleaned_data['bid_price'], user=request.user, auction=item)
            item.starting_bid = form.cleaned_data['bid_price']
            item.save()
            bid.save()
            return HttpResponseRedirect(reverse("listing", args=[listing_id]))
        else:
            print(form.errors.as_data())
    return render(request, "auctions/listing.html", {
        "item": item,
        "bids": bids,
        "HighestBid": bids.order_by('-bid_price').first().user if len(bids) > 0 else None,
        "num_bids": num_bids,
        "comments": comments,
        "seller": seller,
        "category": category
    })
@login_required(login_url='/login')
def winner(request, listing_id):
    item = Auction.objects.get(id=listing_id)
    bids = Bid.objects.filter(auction=listing_id)
    item.active = False
    item.save()
    if len(bids) > 0:
        winner = bids.order_by('-bid_price').first()
        return render(request, "auctions/winner.html", {
            "item": item,
            "winner": winner
        })
    else:
        return render(request, "auctions/winner.html", {
            "item": item,
            "winner": None
        })

@login_required(login_url='/login')
def createlisting(request):
    form = AuctionForm()
    context = {}
    if request.method == "POST":
        form = AuctionForm(request.POST, request.FILES)
        
        if form.is_valid():
            if (form.cleaned_data['title'].lower() in [i.title.lower() for i in Auction.objects.all()]):
                messages.error(request, "Title already exists")
                return render(request, "auctions/createlisting.html", {
                    "form": form,
                })
            
            form.save(commit=False)
            form.instance.user = request.user
            form.save()
            return HttpResponseRedirect(reverse("listing", args=[Auction.objects.last().id]))
        else:
            print(form.errors.as_data()) # here you print errors to terminal

    context['form'] = form
    return render(request, "auctions/createlisting.html", context)
    
def category(request, category):
    return render(request, "auctions/category.html", {
        "category": category,
        "auctions": Auction.objects.filter(category=category)
    })
@login_required
def watchlist(request):
    # show_watchlist = Watchlist.objects.filter(user = request.user)

    show_watchlist = Auction.objects.filter(item_watchlist__user = request.user)
    if show_watchlist:
        return render(request, "auctions/watchlist.html", {
            'items': show_watchlist
        })
    else:
        return render(request, "auctions/watchlist.html", {
            'empty': True
        })

@login_required
def add_watchlist(request, listing_id):
    query = Auction.objects.get(pk = listing_id)
    if Watchlist.objects.filter(user = request.user, item = query).exists():
        messages.error(request, "Item already in watchlist, watchlist deleted!")
        Watchlist.objects.filter(user = request.user, item = query).delete()
    else:
        Watchlist.objects.create(user = request.user, item = query) 
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))




def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
