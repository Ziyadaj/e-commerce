from email.policy import default
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Auction(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField(auto_now_add=True)
    starting_bid = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='images/', default='images/default.png' , blank=True, null=True)
    category = models.CharField(max_length=255, default=None, blank=True, null=True)
    active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.title} ({self.starting_bid})"
class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    bid_price = models.DecimalField(max_digits=6, decimal_places=2)
    
    def __str__(self):
        return f"{self.user} ({self.bid_price})"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    comment = models.TextField()
    def __str__(self):
        return f"{self.user} ({self.comment})"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey('Auction', on_delete=models.CASCADE, related_name='item_watchlist') 
    def __str__(self):
        return f"{self.user}'s Watchlist"