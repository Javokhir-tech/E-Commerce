from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.http import request
from django.shortcuts import render
from django.urls import reverse

from .models import User, AuctionListings, Bids, Comments, Watchlist
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def index(request):
    # to be able to view items by existing categories
    categories = AuctionListings.objects.raw("SELECT * FROM auctions_auctionlistings GROUP BY category")
    
    items = AuctionListings.objects.all()
    
    # return index page with active listings
    return render(request, "auctions/index.html", {
        "Lots": items,
        "categories": categories,
    })

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

# Form to input title name
class NewListingForm(forms.Form):
    title = forms.CharField(label="Title", max_length=50, widget=forms.TextInput(
        attrs={'class': 'form-control',
            'placeholder': 'Enter title of a lot.'}))

    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
            'placeholder': 'Type description of a lot.'}))
    
    bid = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 
        'placeholder': 'Enter an intial bid of lot.' }))
    
    image = forms.URLField(
        widget=forms.URLInput(attrs={'class': 'form-control',
            'placeholder': 'Enter a url of image.'}))

    category = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control',
            'placeholder': 'Enter a category.'}))


# User should login first
@login_required(login_url='login')
def create(request):
    # If method post
    if request.method == "POST":

        # Take the data that user submitted and save it in form
        form = NewListingForm(request.POST)

        if form.is_valid():
            # Who puts an auction lot on bid
            auctioner = request.user

            # Get form attributes
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            bid = form.cleaned_data["bid"]
            image = form.cleaned_data["image"]
            category = form.cleaned_data["category"]

            # Save form attributes in db
            lot = AuctionListings(title=title, description=description, initialBid=bid, image=image, category=category, auctioner=auctioner)

            lot.save()

            # Get back to index
            return HttpResponseRedirect(reverse("index"))
        else:
            # If form isn't valid get existing data on that page
            return render(request, "auctions/create.html", {
                "AuctionListingForm" : form
            })
    # Get page create
    return render(request, "auctions/create.html", {
        "AuctionListingForm": NewListingForm(),
    })


def listing_page(request, lot_id):
    user = request.user
    
    # Get chosen lot
    item = AuctionListings.objects.get(id=lot_id)
    
    # View comments
    userComment = Comments.objects.filter(listing=item)

    # Check if user login
    if user.is_authenticated:
        # Check if item in user's watchlist
        listing_in_watchlist = Watchlist.objects.filter(user=user, lotList=lot_id).exists()
    else:
        listing_in_watchlist = False
        

    # If lot bid doesn't exist, puts price of item as an initial bid
    bidInfoExists = Bids.objects.filter(lot=item).exists()


    # To get latest row
    bidInfo = Bids.objects.filter(lot=item).last()
    
    # Counts number of bids
    bidInfoAll = Bids.objects.filter(lot=item)
    numberOfBids = len(bidInfoAll)

    # Check by whom bid was placed
    if user.is_authenticated:
        lotOwnedByUser = AuctionListings.objects.filter(auctioner=user, id=lot_id).exists()
    else:
        lotOwnedByUser = False
    
    if request.method == "POST":
        # Get user's bid from submitted data
        usersBid = int(request.POST.get('usersBid', ''))

        # if no bids yet
        if bidInfo is None:
            bid = Bids(holder=user, lot=item, bid=usersBid)
            bid.save()
            messages.info(request, "Your bid is accepted!")
            return HttpResponseRedirect(reverse("index"))

        # if current user's bid on top
        if bidInfo.holder == user:
            messages.error(request, "Your bid is current active bid!")
            return HttpResponseRedirect(reverse("index"))
        
        # Checks if current user's bid bigger than active bid
        if bidInfo.bid < usersBid:
            bid = Bids(holder=user, lot=item, bid=usersBid)
            bid.save()
            messages.info(request, "Your bid is accepted!")
            return HttpResponseRedirect(reverse("index"))
        else:
            messages.error(request, "Your bid should be bigger than active bid!")
            return HttpResponseRedirect(reverse("index"))
                
    else:
        return render(request, "auctions/listing.html", {
            "Lot": item,
            "user": user,
            "bidInfo": bidInfo,
            "listing_in_watchlist": listing_in_watchlist,
            'bidInfoExists': bidInfoExists,
            'numberOfBids': numberOfBids,
            'lotOwnedByUser': lotOwnedByUser,
            'userComment': userComment,
        })

def close_bid(request, lot_id):
    # only auctioner can close bid
    # info related to lot from Bids table will be deleted
    # winner is who placed highest bid
    # should return who is winner

    item = AuctionListings.objects.get(id=lot_id)
    
    # To get latest row, (winner) and store them in var
    
    if Bids.objects.filter(lot=item).exists():
        winner = Bids.objects.filter(lot=item).last()
        winnersBid = winner.bid
        winnersName = winner.holder
        winnersListItem = winner.lot
    
    else:
        winner = False
        winnersBid = False
        winnersName = False
        winnersListItem = False
    
    # Then delete row
    bid = Bids.objects.filter(lot=item)
    bid.delete()
    
    # Delete item in Auction Listings
    item.delete()
        
    return render(request, "auctions/winner.html", {
        "winnersBid": winnersBid,
        "winnersName": winnersName,
        "winnersItem": winnersListItem,
        
    })


# Add comments
def comments_add(request, lot_id):
    
    user = request.user
    item = AuctionListings.objects.get(id=lot_id)
    
    userComment = Comments.objects.filter(listing=item)
    
    if request.method == "POST":

        # Get user's comment from submitted data
        usersComment = (request.POST.get('usersComment', ''))

        # Save user's comment
        Comment = Comments(userComment=user, comments=usersComment, listing=item)
        Comment.save()

        messages.info(request, "Your comment is added!")
        return HttpResponseRedirect(reverse("listing", args=(lot_id,)))
    #
    # else:
    #     return render(request, "auctions/comments.html", {
    #         "userComment": userComment
    #     })


@login_required(login_url='login')
# Watchlist view
def watchlist(request):
    user = request.user
    # Get user's watchlist if exists
    if Watchlist.objects.filter(user=user).exists():
        # Get items of user
        watchlist = Watchlist.objects.get(user=request.user)
        return render(request, "auctions/watchlist.html", {

            # Get all items in watchlist of user
            "user": user,
            "watchlist": watchlist.lotList.all()
        })
    else:
        messages.error(request, f"{request.user}'s' watchlist is empty!")
        return HttpResponseRedirect(reverse("index"))

def watchlist_add(request, lot_id):
    #   if Watchlist.objects.filter(user=request.user).exists():
    item = AuctionListings.objects.get(pk=lot_id)
    if request.method == "POST":

        # Check if the item already exists in that user watchlist
        if Watchlist.objects.filter(user=request.user, lotList=lot_id).exists():
            #
            remove = Watchlist.objects.get(user=request.user, lotList=lot_id)
            # removes one item of a user
            remove.lotList.remove(item)
            messages.add_message(request, messages.ERROR,
                                 "Successfully removed from your watchlist")
            return HttpResponseRedirect(reverse("index"))
        else:
            # Get the user watchlist or create it, if it doesn't exists
            watchlist, created = Watchlist.objects.get_or_create(
                user=request.user)
            # Add the item through the ManyToManyField (Watchlist => item)
            watchlist.lotList.add(item)
            messages.add_message(request, messages.SUCCESS,
                                 "Successfully added to your watchlist")
            return HttpResponseRedirect(reverse("watchlist"))
    return render(request, "auctions/watchlist.html")


# view to display all the active listings in that category
# categories list by clicking one category, user should see active list in that category
@login_required(login_url='login')
def category(request, lot_category):
    # user should visit all listing categories

    # retieving all the products that fall into this category
    Categories = AuctionListings.objects.filter(category=lot_category)
    
    empty = False
    if len(Categories) == 0:
        empty = True

    return render(request, "auctions/category.html", {
        "categ": lot_category,
        "empty": empty,
        "products": Categories
    })

def categories(request):
    # to be able to view items by existing categories
    categories = AuctionListings.objects.raw("SELECT * FROM auctions_auctionlistings GROUP BY category")
    
    return render(request, "auctions/categories.html", {
        "categories": categories,
    })
    
    
'''
def listing(request, NewListings_id):
    user = request.user
    listing = NewListings.objects.get(pk=NewListings_id)
    comments = Comments.objects.filter(listing=listing)
    watchlist = Watchlists.objects.filter(user=user)
    listing_in_watchlist = Watchlist.objects.filter(user=user, listing=listing).exists()
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "comments": comments,
        "user": user,
        "watchlist": watchlist,
        "listing_in_watchlist": listing_in_watchlist,
    })


<!--
{% if user.is_authenticated %}
{% for bid in bidInfo %}
    {{bid.holder}}
    <div class="form-group">
        <form action="{% url 'listing' Lot.id %}" method="POST">
            {% csrf_token %}
            <div class="col-7">
                <input type="number" placeholder="Enter your bid. (Current bid is ${{bid.bid}})" class="form-control" min='{{bid.bid}}'     name="usersBid">
            </div>
        </form>
    </div>
{% empty %}
    <form action="{% url 'listing' Lot.id %}" method="POST">
        {% csrf_token %}
        <input type="number" placeholder="Enter your bid. (Current bid is ${{Lot.initialBid}})" class="form-control"
        min='{{Lot.initialBid}}' name="usersBid">
    </form>
{% endfor %}
{% else %}
    <div>Register or login to be able to bid on the item.</div>
{% endif %}-->

def listing_page(request, lot_id):
    user = request.user
    
    # Get chosen lot
    item = AuctionListings.objects.get(id=lot_id)
    
    # Check if user login
    if user.is_authenticated:
        # Check if item in user's watchlist
        listing_in_watchlist = Watchlist.objects.filter(user=user, lotList=lot_id).exists()
        bids_in_bidlist = Bids.objects.filter(holder=user, lot=item).exists()
    else:
        listing_in_watchlist = False
        bids_in_bidlist = False

    # To get latest row
    bidInfo = Bids.objects.filter(lot=item).last()
    # if Bids.objects.filter(lot=item).exists():
    #     # Gets all bid holders list associated with item
    #     bidInfo = Bids.objects.filter(lot=item)
    # else:
    #     bidInfo = 0
    
    if request.method == "POST":
        # Get user's bid from submitted data
        usersBid = int(request.POST.get('usersBid', ''))

        # If user's bid exists
        if Bids.objects.filter(holder=user, lot=item).exists():
            bid = Bids.objects.get(holder=user, lot=item)
            
            # Check whether user already placed the same bid
            if Bids.objects.filter(holder=user, lot=item, bid=usersBid).exists():
                messages.error(request, "Your bid had already been accepted!")

                return HttpResponseRedirect(reverse("index"))
        
            # Else update user's bid
            else:
                #
                if usersBid > bid.bid:
                    #bid.bid = usersBid
                    bid.save()
                    messages.info(request, "Your bid is updated!")

                    return HttpResponseRedirect(reverse("index"))
                
                else:
                    return HttpResponseRedirect(reverse("index"))
                
        # Creates bid table of a user
        else:
            # Creates new table for a user
            bid = Bids(holder=user, lot=item, bid=usersBid)
            bid.save()
            messages.success(request, "Your bid is accepted!")
            return HttpResponseRedirect(reverse("index"))

    else:
        return render(request, "auctions/listing.html", {
            "Lot": item,
            "user": user,
            "bidInfo": bidInfo,
            "listing_in_watchlist": listing_in_watchlist,
            #"bids_in_bidlist": bids_in_bidlist,
        })


'''
