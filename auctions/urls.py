from auctions.views import category
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="create"),
    path("listing/<int:lot_id>", views.listing_page, name="listing"),

    path("categories", views.categories, name="categories"),
    
    path("category/<str:lot_category>", views.category, name="category"),

    path("watchlist", views.watchlist, name="watchlist"),
    path("comments/<int:lot_id>", views.comments_add, name="comments"),
    path("watchlist_add/<int:lot_id>", views.watchlist_add, name="watchlist_add"),
    path("closebid/<int:lot_id>", views.close_bid, name="closebid"),
    
    
]
