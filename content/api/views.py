from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView, RetrieveAPIView, DestroyAPIView
from rest_framework import permissions
from rest_framework.pagination import PageNumberPagination
from datetime import datetime, timedelta

from content.models import Post, Comment, CommentResponse
from .serializers import PostSerializer, CommentSerializer, CommentResponseSerializer, PostCreateSerializer, PostUpdateSerializer


class PostDeleteView(DestroyAPIView):
	serializer_class = PostSerializer
	queryset = Post.objects.all()
	lookup_field = 'slug'


class PostListView(ListAPIView):
	serializer_class = PostSerializer
	queryset = Post.objects.all()


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def PostCreateView(request):

	data = request.data
	data['author'] = request.user.pk
	serializer = PostCreateSerializer(data=data)

	data = {}
	if serializer.is_valid():
		post = serializer.save()
		data['response'] = 'success'
		data['pk'] = post.pk
		data['title'] = post.title
		data['author'] = post.author.username
		data['description'] = post.description
		try:
			data['video_1080p'] = post.video_1080p.url
		except:
			data['video_1080p'] = ''
		try:
			data['video_720p'] = post.video_720p.url
		except:
			data['video_720p'] = ''
		try:
			data['video_480p'] = post.video_480p.url
		except:
			data['video_480p'] = ''
		try:
			data['video_360p'] = post.video_360p.url
		except:
			data['video_360p'] = ''
		data['video_240p'] = post.video_240p.url
		data['thumbnail'] = post.thumbnail.url
		data['horizontal'] = post.horizontal
		data['date_posted'] = post.date_posted
		data['likes'] = post.total_likes()
		data['dislikes'] = post.total_dislikes()
		return Response(data=data)
	return Response({'error': 'Validation error'})

@api_view(['PUT'])
@permission_classes((permissions.IsAuthenticated,))
def PostUpdateView(request, slug):
	try:
		post = Post.objects.filter(slug=slug).first()
	except Post.DoesNotExist:
		return Response({'error': 'Post does not exists'})
	if (request.user.pk != post.author.pk):
		return Response({'error': 'You do not have permission to do that'})
	print(post)
	serializer = PostUpdateSerializer(post, data=request.data, partial=True)
	if serializer.is_valid():
		serializer.save()
		data={}
		data['response'] = 'success'
		data['pk'] = post.pk
		data['title'] = post.title
		data['author'] = post.author.username
		data['description'] = post.description
		try:
			data['video_1080p'] = post.video_1080p.url
		except:
			data['video_1080p'] = ''
		try:
			data['video_720p'] = post.video_720p.url
		except:
			data['video_720p'] = ''
		try:
			data['video_480p'] = post.video_480p.url
		except:
			data['video_480p'] = ''
		try:
			data['video_360p'] = post.video_360p.url
		except:
			data['video_360p'] = ''
		data['video_240p'] = post.video_240p.url
		data['thumbnail'] = post.thumbnail.url
		data['horizontal'] = post.horizontal
		data['date_posted'] = post.date_posted
		data['likes'] = post.total_likes()
		data['dislikes'] = post.total_dislikes()
		return Response(data=data)
	return Response({'error': 'Validation error'})


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def hotWeekList(request):
	posts = Post.objects.filter(date_posted__date__gte=datetime.now()-timedelta(days=7)).order_by('-likes')
	print(posts)
	paginator = PageNumberPagination()
	paginator.page_size = 3
	paginated_posts = paginator.paginate_queryset(posts, request)

	serializer = PostSerializer(paginated_posts, many=True)
	return paginator.get_paginated_response(serializer.data)
	return Response(serializer.data)


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def CommentList(request, slug, order): # -likes | date_posted | -date_posted
	if not(order == '-likes' or order == 'date_posted' or order =='-date_posted'):
		return Response({'error': 'Wrong order kay word'})
	paginator = PageNumberPagination()
	paginator.page_size = 1
	try:
		post_comments = Comment.objects.filter(post__slug=slug).order_by(order)
	except Comment.DoesNotExist:
		return Response({'error': 'Post does not exist'})
	paginated_comments = paginator.paginate_queryset(post_comments, request)

	serializer = CommentSerializer(paginated_comments, many=True)
	return paginator.get_paginated_response(serializer.data)
	return Response(serializer.data)


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def CommentResponseList(request, pk):
	post_comments = CommentResponse.objects.filter(response_to=pk)

	serializer = CommentResponseSerializer(post_comments, many=True)
	return Response(serializer.data)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def like_dislike(request, pk, action, model_tyle):
	if model_tyle == 'comment':
		model_to_like = Comment.objects.filter(pk=pk).first()
	elif model_tyle == 'comment-response':
		model_to_like = CommentResponse.objects.filter(pk=pk).first()
	elif model_tyle == 'post':
		model_to_like = Post.objects.filter(pk=pk).first()
	else:
		return Response({'error': 'Wrong type'})
	if action == 'like':
		if (model_to_like):
			if model_to_like.likes.filter(id=request.user.id).exists():
				model_to_like.likes.remove(request.user)
				return Response({'success': f'{model_tyle} unliked'})
			else:
				model_to_like.dislikes.remove(request.user)
				model_to_like.likes.add(request.user)
				return Response({'success': f'{model_tyle} liked'})
		else:
			return Response({'error': 'Object does not exists in the database'})
	elif action == 'dislike':
		if (model_to_like):
			if model_to_like.dislikes.filter(id=request.user.id).exists():
				model_to_like.dislikes.remove(request.user)
				return Response({'success': f'{model_tyle} undisliked'})
			else:
				model_to_like.likes.remove(request.user)
				model_to_like.dislikes.add(request.user)
				return Response({'success': f'{model_tyle} disliked'})
		else:
			return Response({'error': 'Object does not exists in the database'})
	else:
		return Response({'error': 'Wrong action'})

	return Response({'error': 'Unknown error'})


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def CommentCreateView(request, post_pk):
	try:
		post = Post.objects.filter(pk=post_pk).first()
	except Post.DoesNotExist:
		return Response({'error': 'Post does not exists.'})
	content = request.data['content']
	if (len(content) < 1):
		return Response({'error': 'Comment is empty.'})
	if (len(content) > 10000):
		return Response({'error': 'More than 10 000 characters.'})
	comment = Comment(author = request.user, post=post, content=content)
	comment.save()
	data = {}

	data['response'] = 'success'
	data['pk'] = comment.pk
	data['author'] = comment.author.username
	data['content'] = comment.content
	data['date_posted'] = comment.date_posted
	data['likes'] = comment.total_likes()
	data['dislikes'] = comment.total_dislikes()
	return Response(data=data)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def CommentResponseCreateView(request, comment_pk):
	try:
		comment = Comment.objects.filter(pk=comment_pk).first()
	except Comment.DoesNotExist:
		return Response({'error': 'Comment does not exists.'})
	content = request.data['content']
	if (len(content) < 1):
		return Response({'error': 'Comment is empty.'})
	if (len(content) > 10000):
		return Response({'error': 'More than 10 000 characters.'})
	comment_response = CommentResponse(author = request.user, response_to=comment, content=content)
	comment_response.save()
	data = {}

	data['response'] = 'success'
	data['pk'] = comment_response.pk
	data['author'] = comment_response.author.username
	data['content'] = comment_response.content
	data['date_posted'] = comment_response.date_posted
	data['likes'] = comment_response.total_likes()
	data['dislikes'] = comment_response.total_dislikes()
	return Response(data=data)


@api_view(['PUT'])
@permission_classes((permissions.IsAuthenticated,))
def CommentEditView(request, comment_pk, comment_type):
	print(request.data)
	if (comment_type == 'comment'):
		comment = Comment.objects.filter(pk = comment_pk).first()
	elif (comment_type == 'response-comment'):
		comment = CommentResponse.objects.filter(pk=comment_pk).first()
	else:
			return Response({'error': 'Wrong comment type.'})
	if not(comment):
		return Response({'error': 'Comment does not exists.'})
	content = request.data['content']
	if (len(content) < 1):
		return Response({'error': 'Comment is empty.'})
	if (len(content) > 10000):
		return Response({'error': 'More than 10 000 characters.'})
	if (comment.author != request.user):
		return Response({'error': 'You do not have permission to do that.'})
	comment.content = content
	comment.edited = True
	comment.save()
	data = {}

	data['response'] = 'success'
	data['pk'] = comment.pk
	data['author'] = comment.author.username
	data['content'] = comment.content
	data['date_posted'] = comment.date_posted
	data['edited'] = comment.edited
	data['likes'] = comment.total_likes()
	data['dislikes'] = comment.total_dislikes()
	return Response(data=data)
