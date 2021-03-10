from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    pass

# Auction listings
class AuctionListings(models.Model):
    auctioner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,)
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=64)
    initialBid = models.FloatField(max_length=6)
    image = models.ImageField(upload_to='auctions/static/auctions', default='/static/auctions/default_image.jpg', null=True)
    category = models.CharField(max_length=64)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} initial bid: {self.initialBid}, category: {self.category}, auctioner: {self.auctioner}"

# Bids
class Bids(models.Model):
    holder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bidHolder")
    lot = models.ForeignKey(AuctionListings, on_delete=models.CASCADE, related_name="bidLot")
    bid = models.FloatField(max_length=6)

    def __str__(self):
        return f" {self.holder}: {self.lot}, bid: {self.bid}"

# Comments
class Comments(models.Model):
    listing = models.ForeignKey(AuctionListings, on_delete=models.CASCADE, related_name="listingComment")
    userComment = models.ForeignKey(User, on_delete=models.CASCADE, related_name="usercomment")
    comments = models.TextField(max_length=64)
    timePosted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.userComment} {self.listing}, {self.comments}"

# Watchlist
class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lotList = models.ManyToManyField(AuctionListings, blank=True)

    def __str__(self):
       return f"{self.user}'s WatchList: {self.lotList}"

