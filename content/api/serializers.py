import shutil
import os
import sys
import cv2
import uuid
from PIL import Image
from moviepy.editor import VideoFileClip, ImageSequenceClip
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from django.core.files import File as DjangoFile
CONTENT_SIZE_MAX_BYTES = 1024 * 1024 * 10
THUMBNAIL_SIZE_MAX_BYTES = 1024 * 1024 * 2
ACCEPTED_THUMBNAIL_FORMATS = ('.png', '.jpg', '.jpeg')
ACCEPTED_VIDEO_FORMATS = ('.mp4',)


from rest_framework import serializers
from content.models import Post, Comment, CommentResponse


class PostSerializer(serializers.ModelSerializer):
	likes = serializers.SerializerMethodField('likes_count')
	dislikes = serializers.SerializerMethodField('dislikes_count')
	#author = serializers.SerializerMethodField('get_author_name')

	class Meta:
		model = Post
		fields = ('pk', 'author', 'title', 'slug', 'description', 'video_1080p', 'video_720p',
				'video_480p', 'video_360p', 'video_240p', 'thumbnail', 'horizontal', 'date_posted', 'likes', 'dislikes')


	def likes_count(self, comment):
		likes = comment.total_likes()
		return likes

	def dislikes_count(self, comment):
		likes = comment.total_dislikes()
		return likes


class CommentSerializer(serializers.ModelSerializer):
	likes = serializers.SerializerMethodField('likes_count')
	dislikes = serializers.SerializerMethodField('dislikes_count')
	author = serializers.SerializerMethodField('get_author_name')

	class Meta:
		model = Comment
		fields = ('author', 'content', 'likes', 'dislikes', 'date_posted', 'edited', 'pk')

	def likes_count(self, comment):
		likes = comment.total_likes()
		return likes

	def dislikes_count(self, comment):
		likes = comment.total_dislikes()
		return likes

	def get_author_name(self, comment):
		username = comment.author.username
		return username


class CommentResponseSerializer(serializers.ModelSerializer):
	likes = serializers.SerializerMethodField('likes_count')
	dislikes = serializers.SerializerMethodField('dislikes_count')
	author = serializers.SerializerMethodField('get_author_name')

	class Meta:
		model = CommentResponse
		fields = ('author', 'content', 'likes', 'dislikes', 'date_posted', 'edited', 'pk')

	def likes_count(self, comment):
		likes = comment.total_likes()
		return likes

	def dislikes_count(self, comment):
		dislikes = comment.total_dislikes()
		return dislikes

	def get_author_name(self, comment):
		username = comment.author.username
		return username

class PostCreateSerializer(serializers.ModelSerializer):
	#author = serializers.SerializerMethodField('get_author_name')

	class Meta:
		model = Post
		fields = ('author', 'title', 'description', 'video_240p', 'thumbnail', 'date_posted')

	def save(self):
		try:
			content_file = self.validated_data['video_240p']
			title = self.validated_data['title']
			description = self.validated_data['description']
			author =  self.validated_data['author']
			thumbnail = self.validated_data['thumbnail']
			if len(title) < 2:
				raise serializers.ValidationError({'response': 'Title have to be longer than 2 characters'})

			if len(description) > 10000:
				raise serializers.ValidationError({'response': 'Description can not be longer than 10 000 characters.'})

			working_file_name = str(uuid.uuid4())
			processed_working_file_name = str(uuid.uuid4())
			working_dir = os.path.join(settings.TEMP, working_file_name)
			processed_working_dir = os.path.join(working_dir, processed_working_file_name)
			os.makedirs(working_dir, exist_ok=True)
			os.makedirs(processed_working_dir, exist_ok=True)
			url = os.path.join(working_dir, str(content_file))
			print('ACCEPT FORMAT: ', url.lower().endswith(('.png', '.jpg', '.jpeg')))#ACCEPTED FORMATS
			print(thumbnail)
			storage = FileSystemStorage(location=url)

			with storage.open('', 'wb+') as destination:
				for chunk in content_file.chunks():
					destination.write(chunk)
				destination.close()
			#CHECKING THE SIZE ###
			content_file_size = os.path.getsize(url)

			if not(url.lower().endswith(ACCEPTED_VIDEO_FORMATS)):
				shutil.rmtree(working_dir)
				raise serializers.ValidationError({'response': f'Thumbnail image format incorrect - try: {ACCEPTED_VIDEO_FORMATS}'})

			if content_file_size > CONTENT_SIZE_MAX_BYTES:
				shutil.rmtree(working_dir)
				raise serializers.ValidationError({'response': 'File is too big'})
			### DIMENCIONS
			video = cv2.VideoCapture(url)

			height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
			width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
			### VERTICAL OR HORIZONTAL + THININ'
			if height > width:
				horizontal = False
				print('vertical')
			else:
				horizontal = True
				print('horizontal')
			bigger = max(height, width)
			smaller = min(height, width)
			#TOO WIDE OR HIGH
			if bigger > 2560:
				shutil.rmtree(working_dir)
				raise serializers.ValidationError({'response': 'Video height or width is bigger than 2560 pixels'})
			if smaller < 360:
				shutil.rmtree(working_dir)
				raise serializers.ValidationError({'response': 'Video height or width is smaller than 360 pixels'})
			#THIN
			if (bigger/smaller) > 2.5:
				shutil.rmtree(working_dir)
				raise serializers.ValidationError({'response': 'Video is too thin'})
			### DURATION
			print(video.get(cv2.CAP_PROP_FRAME_WIDTH))
			print(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

			fps_count = video.get(cv2.CAP_PROP_FPS)
			frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
			duration = int(frame_count/fps_count)
			print(fps_count)
			print(frame_count)
			print(duration)
			video.release()
			if duration < 2: #2s
				shutil.rmtree(working_dir)
				raise serializers.ValidationError({'response': 'Video is too short - 2 seconds minimum'})
			if duration > 901: #15 min
				shutil.rmtree(working_dir)
				raise serializers.ValidationError({'response': 'Video is too long - 15 minutes maximum'})

			###-vvv THUMBNAIL vvv-###

			if (thumbnail == None):
				new_name = str(content_file)
				new_thumbnail_name = new_name.split('.', 1)[0]
				thumbnail_dir = os.path.join(processed_working_dir, 'thumbnail.jpg')
			else:
				thumbnail_dir = os.path.join(processed_working_dir, str(thumbnail))
				storage = FileSystemStorage(location=thumbnail_dir)

				with storage.open('', 'wb+') as destination:
					for chunk in thumbnail.chunks():
						destination.write(chunk)
					destination.close()

				thumbnail_img = cv2.imread(thumbnail_dir)
				dims = thumbnail_img.shape
				thumbnail_height, thumbnail_width = dims[0], dims[1]
				new_name = str(thumbnail)
				new_thumbnail_name = new_name.split('.', 1)[0]

				if not(thumbnail_dir.lower().endswith(ACCEPTED_THUMBNAIL_FORMATS)):
						shutil.rmtree(working_dir)
						raise serializers.ValidationError({'response': f'Thumbnail image format incorrect - try: {ACCEPTED_THUMBNAIL_FORMATS}'})
				if horizontal:
					if thumbnail_width < thumbnail_height:
						shutil.rmtree(working_dir)
						raise serializers.ValidationError({'response': 'Video is horizontal - thumbnail width have to be greater than height'})
				else:
					if thumbnail_width > thumbnail_height:
						shutil.rmtree(working_dir)
						raise serializers.ValidationError({'response': 'Video is vertical - thumbnail height have to be greater than width'})
				thumbnail_size = os.path.getsize(thumbnail_dir)
				if thumbnail_size > THUMBNAIL_SIZE_MAX_BYTES: # < HERE - REMOVE COMMENTS
						shutil.rmtree(working_dir)
						raise serializers.ValidationError({'response': 'Thumbnail is bigger than 2MB.'})

			###-^^^ THUMBNAIL ^^^-###

			clip = VideoFileClip(url)

			if (height%2==1 or width%2==1):
				clip = clip.resize(self.is_odd(height, width, smaller))
			###
			content_file_name = str(content_file).split('.', 1)[0]
			processed_video = os.path.join(processed_working_dir, "processed.mp4")
			processed_video_1080p = os.path.join(processed_working_dir, "processed_1080p.mp4")
			processed_video_720p = os.path.join(processed_working_dir, "processed_720p.mp4")
			processed_video_480p = os.path.join(processed_working_dir, "processed_480p.mp4")
			processed_video_360p = os.path.join(processed_working_dir, "processed_360p.mp4")
			processed_video_240p = os.path.join(processed_working_dir, "processed_240p.mp4")

			if(smaller >= 1080):
				clip.write_videofile(processed_video, fps=fps_count, codec='libx264', bitrate='6000k')
				processed_video_1080p = processed_video
				start_at = 1080
			elif(smaller >= 720):
				clip.write_videofile(processed_video, fps=fps_count, codec='libx264', bitrate='4500k')
				processed_video_720p = processed_video
				start_at = 720
			elif(smaller >= 480):
				clip.write_videofile(processed_video, fps=fps_count, codec='libx264', bitrate='3000k')
				processed_video_480p = processed_video
				start_at = 480
			elif(smaller >= 360):
				clip.write_videofile(processed_video, fps=fps_count, codec='libx264', bitrate='2000k')
				processed_video_360p = processed_video
				start_at = 360
			clip.close()
			if (content_file_size < os.path.getsize(processed_video)):
				resize_ref = VideoFileClip(url)
				only_resize = True
				if (thumbnail == None):
					resize_ref.save_frame(thumbnail_dir, t=int(duration/2))
			else:
				resize_ref = VideoFileClip(processed_video)
				only_resize = False
				if (thumbnail == None):
					resize_ref.save_frame(thumbnail_dir, t=int(duration/2))

			if(smaller >= 1080):
				if (start_at == 1080):
					if (only_resize): processed_video_1080p = url
					else: processed_video_1080p = processed_video
			if(smaller >= 720):
				if (start_at == 720):
					if (only_resize): processed_video_720p = url
					else: processed_video_720p = processed_video
				else:
					if(only_resize):
						clip_720p = resize_ref.resize(self.is_odd(height, width, 720)) #1.5
						clip_720p.write_videofile(processed_video_720p, fps=fps_count, codec='libx264')
					else:
						clip_720p = resize_ref.resize(self.is_odd(height, width, 720))
						clip_720p.write_videofile(processed_video_720p, fps=fps_count, codec='libx264', bitrate='3000k')
			if(smaller >= 480):
				if (start_at == 480):
					if (only_resize): processed_video_480p = url
					else: processed_video_480p = processed_video
				else:
					if(only_resize):
						clip_480p = resize_ref.resize(self.is_odd(height, width, 480))
						clip_480p.write_videofile(processed_video_480p, fps=fps_count, codec='libx264')
					else:
						clip_480p = resize_ref.resize(self.is_odd(height, width, 480))
						clip_480p.write_videofile(processed_video_480p, fps=fps_count, codec='libx264', bitrate='2000k')
			if(smaller >= 360):
				if (start_at == 360):
					if (only_resize): processed_video_360p = url
					else: processed_video_360p = processed_video
				else:
					if(only_resize):
						clip_360p = resize_ref.resize(self.is_odd(height, width, 360))
						clip_360p.write_videofile(processed_video_360p, fps=fps_count, codec='libx264')
					else:
						clip_360p = resize_ref.resize(self.is_odd(height, width, 360))
						clip_360p.write_videofile(processed_video_360p, fps=fps_count, codec='libx264', bitrate='4500k')
			if(only_resize):
				clip_240p = resize_ref.resize(self.is_odd(height, width, 240))
				clip_240p.write_videofile(processed_video_240p, fps=fps_count, codec='libx264')
			else:
				clip_240p = resize_ref.resize(self.is_odd(height, width, 240))
				clip_240p.write_videofile(processed_video_240p, fps=fps_count, codec='libx264', bitrate='1000k')

			resize_ref.close()
			###
			if (smaller >= 1080): video_django_obj_1080p = DjangoFile(open(processed_video_1080p, mode='rb'), name=f'{content_file_name}_1080p.mp4')
			else: video_django_obj_1080p = None
			if (smaller >= 720):video_django_obj_720p = DjangoFile(open(processed_video_720p, mode='rb'), name=f'{content_file_name}_720p.mp4')
			else: video_django_obj_720p = None
			if (smaller >= 480):video_django_obj_480p = DjangoFile(open(processed_video_480p, mode='rb'), name=f'{content_file_name}_480.mp4')
			else: video_django_obj_480p = None
			if (smaller >= 360):video_django_obj_360p = DjangoFile(open(processed_video_360p, mode='rb'), name=f'{content_file_name}_360.mp4')
			else: video_django_obj_360p = None
			video_django_obj_240p = DjangoFile(open(processed_video_240p, mode='rb'), name=f'{content_file_name}_240.mp4')
			thumbnail_django_obj = DjangoFile(open(thumbnail_dir, mode='rb'), name=f'{new_thumbnail_name}.jpg')

			post = Post(
						author = author,
						title = title,
						description = description,
						video_1080p = video_django_obj_1080p,
						video_720p = video_django_obj_720p,
						video_480p = video_django_obj_480p,
						video_360p = video_django_obj_360p,
						video_240p = video_django_obj_240p,
						thumbnail = thumbnail_django_obj,
						horizontal = horizontal,
						)

			post.save()

			if (video_django_obj_1080p): video_django_obj_1080p.close()
			if (video_django_obj_720p): video_django_obj_720p.close()
			if (video_django_obj_480p): video_django_obj_480p.close()
			if (video_django_obj_360p): video_django_obj_360p.close()
			if (video_django_obj_240p): video_django_obj_240p.close()
			thumbnail_django_obj.close()
			shutil.rmtree(working_dir) #REMOVE WORKING DIR
			return post

		except KeyError:
			raise serializers.ValidationError({'response': 'Smtn is missing'})


	def is_odd(self, height, width, max_width):
		smaller = min(height, width)
		div_by = float(smaller/max_width)
		wideo_height = int(height/div_by)
		wideo_width = int(width/div_by)
		if (wideo_height%2==1): wideo_height -= 1
		if (wideo_width%2==1): wideo_width -= 1
		return (wideo_width, wideo_height)


class PostUpdateSerializer(serializers.ModelSerializer):
	#author = serializers.SerializerMethodField('get_author_name')

	class Meta:
		model = Post
		fields = ('title', 'description', 'thumbnail')

	def validate(self, post):
		try:
			title = post.get('title')
			description = post.get('description')
			if(post.get('thumbnail')):
				thumbnail = post.get('thumbnail')
				thumbnail_validation = True
			else:
				thumbnail = self.instance.thumbnail
				thumbnail_validation = False

			print('thumbnail', thumbnail)
			if (title):
				if len(title) < 2:
					raise serializers.ValidationError({'response': 'Title have to be longer than 2 characters'})
			if (description):
				if len(description) > 10000:
					raise serializers.ValidationError({'response': 'Description can not be longer than 10 000 characters.'})
			
			if (thumbnail and thumbnail_validation):
				working_file_name = str(uuid.uuid4())
				working_dir = os.path.join(settings.TEMP, working_file_name)
				os.makedirs(working_dir, exist_ok=True)
				thumbnail_dir = os.path.join(working_dir, str(thumbnail))
				storage = FileSystemStorage(location=thumbnail_dir)
				with storage.open('', 'wb+') as destination:
					for chunk in thumbnail.chunks():
						destination.write(chunk)
					destination.close()

				thumbnail_img = cv2.imread(thumbnail_dir)
				dims = thumbnail_img.shape
				thumbnail_height, thumbnail_width = dims[0], dims[1]
				new_name = str(thumbnail)
				new_thumbnail_name = new_name.split('.', 1)[0]

				print ('thumbnail_height', thumbnail_height)
				print('thumbnail_width', thumbnail_width)

				if not(thumbnail_dir.lower().endswith(ACCEPTED_THUMBNAIL_FORMATS)):
						shutil.rmtree(working_dir)
						raise serializers.ValidationError({'response': f'Thumbnail image format incorrect - try: {ACCEPTED_THUMBNAIL_FORMATS}'})
				if self.instance.horizontal:
					if thumbnail_width < thumbnail_height:
						shutil.rmtree(working_dir)
						raise serializers.ValidationError({'response': 'Video is horizontal - thumbnail width have to be greater than height'})
				else:
					if thumbnail_width > thumbnail_height:
						shutil.rmtree(working_dir)
						raise serializers.ValidationError({'response': 'Video is vertical - thumbnail height have to be greater than width'})
				thumbnail_size = os.path.getsize(thumbnail_dir)
				if thumbnail_size > THUMBNAIL_SIZE_MAX_BYTES: # < HERE - REMOVE COMMENTS
						shutil.rmtree(working_dir)
						raise serializers.ValidationError({'response': 'Thumbnail is bigger than 2MB.'})
				shutil.rmtree(working_dir)
			return post
		except KeyError:
			pass
		return post

