from django.db import models
from django_extensions.db.fields import AutoSlugField
from django.contrib.auth.models import User
from django.dispatch import receiver


class Post(models.Model):
	author = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
	title = models.CharField(max_length=20, blank=True)
	slug = AutoSlugField(populate_from='title')
	description = models.TextField(null=True, blank=True)
	video_1080p = models.FileField(upload_to='videos', max_length=200, null=True, blank=True)
	video_720p = models.FileField(upload_to='videos', max_length=200, null=True, blank=True)
	video_480p = models.FileField(upload_to='videos', max_length=200, null=True, blank=True)
	video_360p = models.FileField(upload_to='videos', max_length=200, null=True, blank=True)
	video_240p = models.FileField(upload_to='videos', max_length=200, blank=True)
	thumbnail = models.FileField(upload_to='thumbnails', max_length=200, null=True, blank=True)
	likes = models.ManyToManyField(User, related_name='post_likes', blank=True)
	dislikes = models.ManyToManyField(User, related_name='post_dislikes', blank=True)
	horizontal = models.BooleanField(default=False)
	date_posted = models.DateTimeField(auto_now_add=True)


	def __str__(self):
		return f'{self.title} by {self.author.username}'

	def total_likes(self):
		return self.likes.count()

	def total_dislikes(self):
		return self.dislikes.count()

@receiver(models.signals.post_delete, sender=Post)
def remove_file_from_s3(sender, instance, using, **kwargs):
	try:
		instance.thumbnail.delete(save=False)
	except:
		pass
	try:
		instance.video_1080p.delete(save=False)
	except:
		pass
	try:
		instance.video_720p.delete(save=False)
	except:
		pass
	try:
		instance.video_480p.delete(save=False)
	except:
		pass
	try:
		instance.video_360p.delete(save=False)
	except:
		pass
	try:
		instance.video_240p.delete(save=False)
	except:
		pass

class Comment(models.Model):
	author = models.ForeignKey(User, on_delete=models.CASCADE)
	content = models.TextField()
	likes = models.ManyToManyField(User, related_name='comments_likes', blank=True)
	dislikes = models.ManyToManyField(User, related_name='comments_dislikes', blank=True)
	post = models.ForeignKey('Post', on_delete=models.CASCADE)
	date_posted = models.DateTimeField(auto_now_add=True, null=True, blank=True)
	edited = models.BooleanField(default=False)

	def __str__(self):
		return f'{self.post.title} comment by {self.author.username}'

	def total_likes(self):
		return self.likes.count()

	def total_dislikes(self):
		return self.dislikes.count()


class CommentResponse(models.Model):
	author = models.ForeignKey(User, on_delete=models.CASCADE)
	content = models.TextField()
	likes = models.ManyToManyField(User, related_name='comments_response_likes', blank=True)
	dislikes = models.ManyToManyField(User, related_name='comments_response_dislikes', blank=True)
	response_to = models.ForeignKey('comment', on_delete=models.CASCADE)
	date_posted = models.DateTimeField(auto_now_add=True)
	edited = models.BooleanField(default=False)

	def __str__(self):
		return f'Response comment from {self.author.username} to {self.response_to.author}'

	def total_likes(self):
		return self.likes.count()

	def total_dislikes(self):
		return self.dislikes.count()
