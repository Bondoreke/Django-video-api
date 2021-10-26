from django.urls import path
from . import views


urlpatterns = [
	path('post-list/', views.PostListView.as_view()),
	path('post-create/', views.PostCreateView),
	path('post-delete/<slug:slug>/', views.PostDeleteView.as_view()),
	path('post-update/<slug:slug>/', views.PostUpdateView),
	path('hotweek/', views.hotWeekList),
	path('comment-create/<str:post_pk>/', views.CommentCreateView),
	path('comment-response-create/<str:comment_pk>/', views.CommentResponseCreateView),
	path('comment-edit/<str:comment_pk>/<str:comment_type>/', views.CommentEditView),
	path('comments/<slug:slug>/<str:order>', views.CommentList),
	path('comments-response/<str:pk>/', views.CommentResponseList),
	path('reaction/<str:pk>/<str:action>/<str:model_tyle>/', views.like_dislike),
]